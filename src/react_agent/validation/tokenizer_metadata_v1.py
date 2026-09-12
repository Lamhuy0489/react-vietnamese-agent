"""Authenticate pinned public tokenizer configuration bytes, without native imports."""

import hashlib
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import MODEL, REVISION, no_links
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION
from react_agent.llm.model_pair_v1 import Role
from react_agent.validation.efficient_requests_audit_v1 import _record
from react_agent.validation.guard_probe_audit_v2 import require

# Both immutable publisher revisions share these bytes. Pins are independently
# present in the agent upstream inventory/mount scan and accepted guard snapshot.
SIZE = 7305
SHA256 = "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583"
BLOB = "07bfe0640cb5a0037f9322287fbfc682806cf672"
MODELS: dict[Role, tuple[str, str]] = {
    "agent": (MODEL, REVISION),
    "guard": ("Qwen/Qwen2.5-1.5B-Instruct", CANDIDATE_REVISION),
}


def authenticate(path: Path, role: Role) -> dict[str, Any]:
    """Derive expected pad/EOS IDs; not proof that a native tokenizer executed."""
    require(role in MODELS, "pinned tokenizer role")
    no_links(path)
    require(path.is_file(), "tokenizer configuration file")
    with path.open("rb") as stream:
        raw = stream.read(SIZE + 1)
    require(len(raw) == SIZE, "tokenizer configuration size")
    blob = hashlib.sha1(  # noqa: S324 - immutable upstream Git object identity
        f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False
    ).hexdigest()
    require(
        hashlib.sha256(raw).hexdigest() == SHA256 and blob == BLOB,
        "tokenizer configuration hash",
    )
    config = _record(raw.decode("utf-8"))
    require(config["tokenizer_class"] == "Qwen2Tokenizer", "pinned tokenizer class")
    ids: dict[str, int] = {}
    for name in ("pad", "eos"):
        token = config[name + "_token"]
        matches = [
            key
            for key, entry in config["added_tokens_decoder"].items()
            if entry["content"] == token and entry["special"] is True
        ]
        require(len(matches) == 1 and matches[0].isdecimal(), "unique special token ID")
        ids[name + "_token_id"] = int(matches[0])
    model, revision = MODELS[role]
    return dict(
        protocol="tokenizer_metadata_v1",
        identity=dict(
            model_id=model,
            revision=revision,
            name="tokenizer_config.json",
            size=SIZE,
            sha256=SHA256,
            git_blob_sha1=BLOB,
        ),
        **ids,
        tokenizer_class=config["tokenizer_class"],
        metadata_authenticated=True,
        native_tokenizer_executed=False,
    )
