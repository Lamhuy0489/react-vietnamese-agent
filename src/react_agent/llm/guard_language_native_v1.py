"""Tokenizer-only admission and native CPU logits checks; never loads model weights."""

from __future__ import annotations

import hashlib
import inspect
import json
import tarfile
import time
import zipfile
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, GuardSnapshot
from react_agent.llm.guard_token_language_v1 import compile_language, documents

BUNDLE_SHA = "b14976413b72898b6c0c1b8c46c1ebb0f62f63633f647ab2064fbc048262240f"
FILES = frozenset(
    {
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt",
    }
)
CASES = (0, 1, 2, 3, 27, 111, 1022, 1023, 2045, 2046, 3066, 3068)


def digest(path: Path) -> str:
    no_links(path)
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def metadata(bundle: Path, output: Path) -> dict[str, Any]:
    no_links(bundle)
    no_links(output)
    if output.exists() or output.resolve().is_relative_to(bundle.resolve()):
        raise ValueError("fresh tokenizer directory outside Dataset required")
    manifest = bundle / "guard_bundle.json"
    if digest(manifest) != BUNDLE_SHA:
        raise ValueError("pinned Dataset manifest required")
    value = json.loads(manifest.read_text())
    pin = GuardSnapshot.model_validate(value["snapshot"])
    if pin.upstream_revision != CANDIDATE_REVISION:
        raise ValueError("pinned guard revision required")
    expected = {f.name: f for f in pin.files if f.name in FILES}
    contents: dict[str, bytes] = {}
    archive = bundle / "guard-model.tar"
    if archive.exists():
        no_links(archive)
        with tarfile.open(archive) as stream:
            members = stream.getmembers()
            if (
                len(members) != len(pin.files)
                or {m.name for m in members} != {f.name for f in pin.files}
                or any(not m.isfile() for m in members)
            ):
                raise ValueError("exact regular snapshot archive inventory required")
            for member in members:
                if member.name in FILES:
                    if member.size != expected[member.name].size:
                        raise ValueError("tokenizer size mismatch")
                    source = stream.extractfile(member)
                    if source is None:
                        raise ValueError("tokenizer member unreadable")
                    with source:
                        contents[member.name] = source.read()
    else:
        candidates = list(bundle.rglob("tokenizer.json"))
        if len(candidates) != 1:
            raise ValueError("unique expanded tokenizer mount required")
        for name in FILES:
            path = candidates[0].parent / name
            no_links(path)
            if path.stat().st_size != expected[name].size:
                raise ValueError("tokenizer size mismatch")
            contents[name] = path.read_bytes()
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}
    if hashes != {name: f.sha256 for name, f in expected.items()}:
        raise ValueError("tokenizer hash mismatch")
    config = json.loads(contents["config.json"])
    tokenizer_config = json.loads(contents["tokenizer_config.json"])
    generation = json.loads(contents["generation_config.json"])
    if config.get("model_type") != "qwen2" or any(
        "auto_map" in obj for obj in (config, tokenizer_config)
    ):
        raise ValueError("native Qwen tokenizer only")
    output.mkdir(parents=True)
    for name, data in contents.items():
        with (output / name).open("xb") as stream:
            stream.write(data)
    return dict(
        snapshot_sha256=pin.sha256,
        model_revision=pin.model_revision,
        tokenizer_sha256=hashes,
        vocabulary_size=config["vocab_size"],
        eos=sorted(generation["eos_token_id"]),
        dataset_manifest_sha256=BUNDLE_SHA,
        model_weights_read=False,
        full_weight_archive_authenticated=False,
    )


class NativeCodec:
    def __init__(self, tokenizer: Any) -> None:
        self.tokenizer = tokenizer

    def encode(self, text: str) -> list[int]:
        return list(self.tokenizer.encode(text, add_special_tokens=False))

    def decode(self, tokens: list[int]) -> str:
        return str(
            self.tokenizer.decode(
                tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False
            )
        )


def native_probe(bundle: Path, tokenizer_root: Path, admission: dict[str, Any]) -> dict[str, Any]:
    import tokenizers  # type: ignore[import-not-found]
    import torch  # type: ignore[import-not-found]
    import transformers  # type: ignore[import-not-found]
    from transformers.generation.logits_process import (  # type: ignore[import-not-found]
        ForcedBOSTokenLogitsProcessor,
        PrefixConstrainedLogitsProcessor,
    )

    if (torch.__version__, transformers.__version__, tokenizers.__version__) != (
        "2.10.0+cu128",
        "5.5.0",
        "0.22.2",
    ):
        raise ValueError("pinned worker library versions required")
    manifest = json.loads((bundle / "guard_bundle.json").read_text())
    wheel = bundle / "transformers-5.5.0-py3-none-any.whl"
    if digest(wheel) != manifest["wheel_sha256"][wheel.name]:
        raise ValueError("native wheel hash mismatch")
    source = inspect.getsourcefile(PrefixConstrainedLogitsProcessor)
    with zipfile.ZipFile(wheel) as stream:
        pinned = hashlib.sha256(
            stream.read("transformers/generation/logits_process.py")
        ).hexdigest()
    if source is None or digest(Path(source)) != pinned:
        raise ValueError("installed logits processor differs from pinned wheel")
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(tokenizer_root),
        local_files_only=True,
        trust_remote_code=False,
        use_fast=True,
    )
    if not tokenizer.is_fast or tokenizer.eos_token_id not in admission["eos"]:
        raise ValueError("fast tokenizer/EOS mismatch")
    started = time.perf_counter()
    language = compile_language(
        NativeCodec(tokenizer),
        tokenizer_sha256=text_hash(canonical_json(admission["tokenizer_sha256"])),
        vocabulary_size=admission["vocabulary_size"],
        eos=tuple(admission["eos"]),
    )
    compilation_seconds = time.perf_counter() - started
    for tokens in language.sequences:
        if set(tokens).intersection(tokenizer.all_special_ids):
            raise ValueError("special token in constrained document")
        for eos in language.eos:
            language.verify_completion((*tokens, eos))
    prompt = tuple(tokenizer.encode("Synthetic CPU logits probe.", add_special_tokens=False))
    callback = language.request(prompt)
    processor = PrefixConstrainedLogitsProcessor(callback, num_beams=1)
    before_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    checked = 0
    started = time.perf_counter()
    try:
        for index in CASES:
            tokens = language.sequences[index]
            for length in range(len(tokens) + 1):
                ids = torch.tensor([(*prompt, *tokens[:length])], dtype=torch.long, device="cpu")
                scores = torch.zeros((1, language.vocabulary_size), device="cpu")
                scores[0, 0] = 1000  # Deliberately prefer a forbidden token.
                original = scores.clone()
                masked = processor(ids, scores)
                allowed = sorted(language.allowed(tokens[:length]))
                finite = torch.where(torch.isfinite(masked[0]))[0].tolist()
                if finite != allowed or not torch.equal(scores, original):
                    raise ValueError("incorrect or mutating native mask")
                if int(masked.argmax(-1)[0]) not in allowed:
                    raise ValueError("forbidden token selected")
                checked += 1
        # Later processors can override the constraint: preserve this negative evidence.
        short = language.request((42,))
        ids = torch.tensor([[42]], dtype=torch.long, device="cpu")
        first = PrefixConstrainedLogitsProcessor(short, 1)(ids, scores)
        conflict = ForcedBOSTokenLogitsProcessor(0)(ids, first)
        if int(conflict.argmax(-1)[0]) in short(0, ids[0]):
            raise ValueError("expected conflicting processor control not observed")
        caught = []
        for fault in ("wrong_prompt", "empty_allowed", "interrupt"):

            def fail(batch_id: int, row: Any, mode: str = fault) -> list[int]:
                if mode == "interrupt":
                    raise KeyboardInterrupt("synthetic interruption")
                return []

            try:
                selected = (
                    processor
                    if fault == "wrong_prompt"
                    else PrefixConstrainedLogitsProcessor(fail, 1)
                )
                selected(ids, scores)
            except (ValueError, KeyboardInterrupt) as error:
                caught.append(type(error).__name__)
        if caught != ["ValueError", "ValueError", "KeyboardInterrupt"]:
            raise ValueError("native fault propagation mismatch")
        # Fresh callback remains usable after the fault cases; no installed hooks.
        processor(torch.tensor([prompt], dtype=torch.long), scores)
    finally:
        torch.set_num_threads(before_threads)
    for name, expected in admission["tokenizer_sha256"].items():
        if digest(tokenizer_root / name) != expected:
            raise ValueError("tokenizer input changed during probe")
    return dict(
        protocol="guard_language_native_cpu_v1",
        valid=True,
        library_verified=True,
        torch=torch.__version__,
        transformers=transformers.__version__,
        tokenizers=tokenizers.__version__,
        processor_source_sha256=pinned,
        language_identity=language.identity_sha256,
        documents=len(documents()),
        native_mask_checks=checked,
        case_indices=list(CASES),
        max_response_tokens_with_eos=max(len(t) + 1 for t in language.sequences),
        compilation_seconds=compilation_seconds,
        mask_seconds=time.perf_counter() - started,
        conflicting_processor_can_override=True,
        failures_propagated=caught,
        torch_threads_restored=torch.get_num_threads() == before_threads,
        model_generate_calls=0,
        model_weights_loaded=0,
        gpu_used=False,
        native_generation_validated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
    )
