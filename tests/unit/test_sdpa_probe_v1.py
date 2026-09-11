"""Tensor controls and immutable artifacts; all fixtures synthetic, no GPU."""

import importlib
import json
import shutil
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from react_agent.llm.sdpa_probe_v1 import ATOL, CAP, RTOL, SDPA_SHA, attention, cases, run_case
from react_agent.validation.guard_probe_audit_v2 import digest
from react_agent.validation.sdpa_probe_audit_v1 import audit_cases

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "a" * 40


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value))


@pytest.fixture
def entry(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("run_phase5_sdpa_probe")


def test_stub_roundtrip_and_no_native_import(
    entry: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden() -> Any:
        raise AssertionError("native import")

    monkeypatch.setattr("react_agent.llm.sdpa_probe_v1.libraries", forbidden)
    result = entry.run(tmp_path / "run", "stub", COMMIT)
    assert result == audit_cases(tmp_path / "run", COMMIT, "stub")
    assert result["candidate_valid"] is None and not result["native_verified"]
    assert len(list((tmp_path / "run").iterdir())) == 12
    with pytest.raises(ValueError):
        entry.run(tmp_path / "run", "stub", COMMIT)


@pytest.mark.parametrize("commit", ["", "a" * 39, "A" * 40, "a" * 41])
def test_bad_commit_before_writes(entry: Any, tmp_path: Path, commit: str) -> None:
    with pytest.raises(ValueError):
        entry.run(tmp_path / "absent", "native", commit)
    assert not (tmp_path / "absent").exists()


def test_fixed_geometry_and_invalid_case() -> None:
    assert len(cases()) == 10
    assert [c["key_tokens"] for c in cases() if c["name"].endswith("boundary_decode")] == [
        4608,
        4224,
    ]
    with pytest.raises(ValueError):
        run_case({**cases()[0], "heads": 1}, "native")
    with pytest.raises(ValueError):
        run_case(cases()[0], "unknown")


@pytest.mark.parametrize("heads,kv,qlen", [(28, 4, 128), (12, 2, 1)])
def test_attention_composition_preserves_logical_heads(heads: int, kv: int, qlen: int) -> None:
    events = []

    class Tensor:
        def __init__(self, h: int) -> None:
            self.shape = (1, h, qlen, 128)

        def transpose(self, a: int, b: int) -> Any:
            events.append(("transpose", a, b))
            return self

        def contiguous(self) -> Any:
            return self

    q, k, v = Tensor(heads), Tensor(kv), Tensor(kv)

    def sdpa(*args: Any, **kwargs: Any) -> Any:
        events.append(kwargs)
        return q

    def repeat(t: Any, n: int) -> Any:
        assert n == heads // kv
        events.append(("repeat", n))
        return Tensor(heads)

    hf = SimpleNamespace(repeat_kv=repeat, sdpa_attention_forward=lambda *a, **k: (q, None))

    def context(value: Any) -> Any:
        assert value == "efficient"
        events.append("efficient-only")
        return nullcontext()

    torch = SimpleNamespace(
        nn=SimpleNamespace(
            attention=SimpleNamespace(
                sdpa_kernel=context, SDPBackend=SimpleNamespace(EFFICIENT_ATTENTION="efficient")
            ),
            functional=SimpleNamespace(scaled_dot_product_attention=sdpa),
        )
    )
    assert attention(torch, hf, q, k, v, "native") is q
    assert not events
    assert attention(torch, hf, q, k, v, "repeat") is q
    assert events[:3] == [("repeat", heads // kv), ("repeat", heads // kv), "efficient-only"]
    assert events[3] == dict(attn_mask=None, dropout_p=0.0, is_causal=qlen > 1, enable_gqa=False)
    with pytest.raises(ValueError):
        attention(torch, hf, q, k, v, "unknown")


@pytest.fixture
def native(tmp_path: Path) -> Path:
    root = tmp_path / "tensor"
    root.mkdir()
    write(
        root / "manifest.json",
        dict(
            protocol="sdpa_tensor_plan_v1",
            source_commit=COMMIT,
            backend="native",
            cases=cases(),
            process_timeout_seconds=90,
            model_loads=0,
            model_generate_calls=0,
        ),
    )
    for index, case in enumerate(cases()):
        row = run_case(case, "stub")
        row.update(
            backend="native",
            pid=100 + index,
            native_verified=True,
            status="OBSERVED",
            allocator_cap_bytes=CAP,
            hf_use_gqa=True,
            native_eligibility=dict(flash=False, efficient=False, cudnn=False),
            input_sha256=["b" * 64] * 3,
            environment=dict(
                torch="2.10.0+cu128",
                cuda="12.8",
                transformers="5.5.0",
                hf_sdpa_sha256=SDPA_SHA,
                device_name="Tesla T4",
                capability=[7, 5],
            ),
            modes=[],
            parity=None,
        )
        for mode in ["native", "repeat"] if case["mode"] == "parity" else [case["mode"]]:
            mem = dict(
                allocated=128,
                reserved=256,
                peak_allocated=128,
                peak_reserved=256,
                global_free=2**30,
                global_total=15 * 2**30,
            )
            row["modes"].append(
                dict(
                    mode=mode,
                    status="OK",
                    error_class=None,
                    instrumented_seconds=0.01,
                    before=mem,
                    after=mem,
                    operators=[
                        "aten::_scaled_dot_product_attention_math"
                        if mode == "native"
                        else "aten::_scaled_dot_product_efficient_attention"
                    ],
                    output_shape=[1, case["query_tokens"], case["heads"], 128],
                    output_finite=True,
                )
            )
        if case["mode"] == "parity":
            row["parity"] = dict(
                atol=ATOL, rtol=RTOL, max_abs_error=0.0, max_tolerance_excess=-ATOL, passed=True
            )
        write(root / (case["name"] + ".json"), row)
    return root


def test_native_shaped_artifact_audit(native: Path) -> None:
    a = audit_cases(native, COMMIT, "native")
    write(native / "summary.json", a)
    assert audit_cases(native, COMMIT, "native") == a
    assert a["candidate_valid"] and not a["phase5_accepted"]
    assert len(a["outcomes"]) == 14


@pytest.mark.parametrize(
    "mutation",
    [
        "pid",
        "shape",
        "input",
        "cap",
        "library",
        "fallback",
        "tolerance",
        "summary",
        "extra",
        "native_flag",
    ],
)
def test_mutations_rejected(native: Path, mutation: str) -> None:
    p = native / ("agent_long_repeat.json" if mutation == "input" else "agent_short_prefill.json")
    v = json.loads(p.read_text())
    if mutation == "pid":
        v["pid"] = 101
    elif mutation == "shape":
        v["modes"][0]["output_shape"][1] = 127
    elif mutation == "input":
        v["input_sha256"][0] = "c" * 64
    elif mutation == "cap":
        v["modes"][0]["after"]["peak_reserved"] = CAP + 1
    elif mutation == "library":
        v["environment"]["torch"] = "2.2.2"
    elif mutation == "fallback":
        v["modes"][1]["operators"] = ["aten::_scaled_dot_product_attention_math"]
    elif mutation == "tolerance":
        v["parity"]["atol"] = 1.0
    elif mutation == "native_flag":
        v["native_verified"] = False
    elif mutation == "summary":
        write(native / "summary.json", {})
    elif mutation == "extra":
        write(native / "extra.json", {})
    write(p, v)
    with pytest.raises(ValueError):
        audit_cases(native, COMMIT, "native")


@pytest.mark.parametrize(
    "name,expected",
    [("agent_long_native", True), ("agent_long_repeat", False), ("agent_short_prefill", False)],
)
def test_oom_is_preserved_not_retried(native: Path, name: str, expected: bool) -> None:
    p = native / (name + ".json")
    v = json.loads(p.read_text())
    v["modes"][0].update(
        status="OOM", error_class="OutOfMemoryError", output_shape=None, output_finite=None
    )
    v["parity"] = None
    write(p, v)
    assert audit_cases(native, COMMIT, "native")["candidate_valid"] is expected


def test_failed_parity_is_not_a_success(native: Path) -> None:
    p = native / "guard_short_decode.json"
    v = json.loads(p.read_text())
    v["parity"].update(max_abs_error=0.02, max_tolerance_excess=0.01, passed=False)
    write(p, v)
    assert audit_cases(native, COMMIT, "native")["candidate_valid"] is False


@pytest.fixture
def release(entry: Any, native: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    auditor = importlib.import_module("audit_phase5_sdpa_tensor_gpu")
    raw, remote = tmp_path / "raw", tmp_path / "remote"
    raw.mkdir()
    remote.mkdir()
    write(native / "summary.json", audit_cases(native, COMMIT, "native"))
    shutil.copytree(native, raw / "sdpa_tensor")
    (raw / "dummy").mkdir()
    for name, v in [("identity", {"task_ids": []}), ("results", []), ("summary", {})]:
        write(raw / f"dummy/{name}.json", v)
    bundle = tmp_path / "bundle.json"
    value = dict(dataset="synthetic/private", snapshot={}, wheel_sha256={})
    write(bundle, value)
    (remote / "worker.py").write_text("# synthetic test source")
    metadata = dict(
        id="huylmhuhu/react-vn-sdpa-tensor-v1",
        code_file="worker.py",
        is_private=True,
        enable_gpu=True,
        enable_tpu=False,
        enable_internet=False,
        machine_shape="NvidiaTeslaT4",
        docker_image=auditor.IMAGE,
        dataset_sources=[value["dataset"]],
        model_sources=[],
        kernel_sources=[],
        competition_sources=[],
    )
    write(remote / "kernel-metadata.json", metadata)
    preflight = tmp_path / "preflight.json"
    pre = dict(
        protocol="sdpa_tensor_gpu_exact_preflight_v1",
        valid=True,
        phase5_accepted=False,
        source_commit=COMMIT,
        base_source_sha256="c" * 64,
        bundle_manifest_sha256=digest(bundle),
        overlay_sha256={},
        prerequisites={},
        wrapper_sha256=digest(remote / "worker.py"),
        checks=[
            dict(
                layout=layout,
                tensor_stub=dict(valid=True, native_verified=False, candidate_valid=None),
            )
            for layout in ("archive", "expanded")
        ],
    )
    write(preflight, pre)
    write(
        raw / "sdpa_tensor_bootstrap_identity.json",
        dict(
            protocol="sdpa_tensor_bootstrap_v1",
            **{
                k: pre[k]
                for k in (
                    "source_commit",
                    "base_source_sha256",
                    "bundle_manifest_sha256",
                    "overlay_sha256",
                )
            },
            snapshot={},
            wheel_sha256={},
        ),
    )
    (raw / "react-vn-sdpa-tensor-v1.log").write_text("synthetic SDPA_TENSOR_GPU_COMPLETE")
    monkeypatch.setattr(auditor, "BUNDLE", bundle)
    monkeypatch.setattr(auditor, "BUNDLE_SHA", digest(bundle))
    monkeypatch.setattr(auditor, "prerequisites", lambda _: {})
    monkeypatch.setattr(auditor, "audit_dummy", lambda *a: {"synthetic_test_transport": True})
    return auditor, raw, remote, preflight


def test_outer_release_repeatable(release: Any) -> None:
    auditor, raw, remote, preflight = release
    a = auditor.audit(raw, remote, preflight)
    assert a == auditor.audit(raw, remote, preflight)
    assert a["candidate_valid"] and not a["phase5_accepted"]


@pytest.mark.parametrize("fault", ["model", "gpu", "wrapper", "summary", "extra", "preflight"])
def test_outer_rejects_corruption(release: Any, fault: str) -> None:
    auditor, raw, remote, preflight = release
    if fault == "wrapper":
        (remote / "worker.py").write_text("modified")
    elif fault == "summary":
        (raw / "sdpa_tensor/summary.json").unlink()
    elif fault == "extra":
        write(raw / "extra.json", {})
    else:
        p = preflight if fault == "preflight" else remote / "kernel-metadata.json"
        v = json.loads(p.read_text())
        if fault == "model":
            v["model_sources"] = ["unexpected/weights"]
        elif fault == "gpu":
            v["enable_gpu"] = False
        else:
            v["checks"][0]["tensor_stub"]["candidate_valid"] = True
        write(p, v)
    with pytest.raises(ValueError):
        auditor.audit(raw, remote, preflight)


@pytest.mark.parametrize("fault", ["hash", "missing", "extra", "overwrite"])
def test_additive_wrapper(entry: Any, tmp_path: Path, fault: str) -> None:
    builder = importlib.import_module("prepare_phase5_sdpa_tensor")
    wrapper = builder.load(ROOT / "notebooks/kaggle/sdpa_tensor_kernel_v1.py")
    prior = json.loads(
        (ROOT / "experiments/manifests/phase5_policy_native_cpu_v1_preflight01.json").read_text()
    )
    assert len(wrapper.OVERLAY_PATHS) == 28
    assert set(prior["overlay_sha256"]) < wrapper.OVERLAY_PATHS
    source = (ROOT / "notebooks/kaggle/sdpa_tensor_kernel_v1.py").read_text()
    assert '"guard-model.tar"' not in source and '"model.safetensors"' not in source
    importlib.import_module("test_policy_native_compat_v1").test_overlay_rejects_mutations(
        wrapper, tmp_path, fault
    )
