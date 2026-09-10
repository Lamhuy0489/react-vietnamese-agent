"""Static-check fault tests use a clearly synthetic wheel, no native imports."""

import importlib
import zipfile
from pathlib import Path
from typing import Any

import pytest

from react_agent.validation.context_stress_audit_v1 import NATIVE_NONE_FIELDS
from react_agent.validation.guard_probe_audit_v2 import digest


@pytest.fixture
def source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Path, dict[str, str]]:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    tool = importlib.import_module("check_phase5_context_stress_compatibility")
    fields = NATIVE_NONE_FIELDS | {
        "min_new_tokens",
        "max_new_tokens",
        "do_sample",
        "num_beams",
        "use_cache",
        "cache_implementation",
        "return_dict_in_generate",
        "output_scores",
        "output_logits",
        "output_attentions",
        "output_hidden_states",
        "eos_token_id",
        "pad_token_id",
        "transformers_version",
        "_commit_hash",
    }
    constructor = "class GenerationConfig:\n    def __init__(self, **kwargs):\n"
    constructor += "".join(
        f"        self.{key} = kwargs.pop({key!r}, None)\n" for key in sorted(fields)
    )
    constructor += (
        "    def to_dict(self):\n        del output['_commit_hash']\n"
        "        output['transformers_version'] = __version__\n"
    )
    sources = {
        tool.MEMBERS[0]: constructor,
        tool.MEMBERS[1]: "class Qwen2ForCausalLM:\n"
        "    def forward(self, input_ids, attention_mask, past_key_values, "
        "use_cache, logits_to_keep, **kwargs):\n        pass\n",
        tool.MEMBERS[2]: "class DynamicLayer:\n    def get_seq_length(self):\n"
        "        return self.keys.shape[-2]\n    def update(self):\n"
        "        return self.keys, self.values\n",
    }
    return tool, tmp_path / "synthetic-test-only.whl", sources


def make_wheel(path: Path, sources: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in sources.items():
            archive.writestr(name, value)


@pytest.mark.parametrize(
    "fault", [None, "pin", "default", "extra", "serialization", "forward", "cache"]
)
def test_static_contract_and_faults(
    source: Any, monkeypatch: pytest.MonkeyPatch, fault: Any
) -> None:
    tool, path, sources = source
    if fault == "default":
        sources[tool.MEMBERS[0]] = sources[tool.MEMBERS[0]].replace(
            "'temperature', None", "'temperature', 1.0"
        )
    elif fault == "extra":
        sources[tool.MEMBERS[0]] = sources[tool.MEMBERS[0]].replace(
            "    def to_dict", "        self.extra = kwargs.pop('extra', None)\n    def to_dict"
        )
    elif fault == "serialization":
        sources[tool.MEMBERS[0]] = sources[tool.MEMBERS[0]].replace(
            "del output['_commit_hash']", "pass"
        )
    elif fault == "forward":
        sources[tool.MEMBERS[1]] = sources[tool.MEMBERS[1]].replace("logits_to_keep", "unsupported")
    elif fault == "cache":
        sources[tool.MEMBERS[2]] = sources[tool.MEMBERS[2]].replace("shape[-2]", "shape[-1]")
    make_wheel(path, sources)
    before = digest(path)
    # This bypass is test-only; production always checks the published frozen hash.
    if fault != "pin":
        monkeypatch.setattr(tool, "WHEEL_SHA256", before)
    if fault is None:
        result = tool.inspect_wheel(path)
        assert (
            result["valid"]
            and result["constructor_fields"] == 70
            and result["serialized_fields"] == 69
        )
        assert not result["native_imported"] and not result["native_inference_verified"]
        assert result == tool.inspect_wheel(path)
    else:
        with pytest.raises(ValueError):
            tool.inspect_wheel(path)
    assert digest(path) == before
