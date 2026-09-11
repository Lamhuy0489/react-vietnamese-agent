"""Independent tensor artifact checks; no native imports or model acceptance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.llm.sdpa_probe_v1 import ATOL, CAP, RTOL, SDPA_SHA, cases
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record, sha
from react_agent.validation.guard_probe_audit_v2 import positive, require


def audit_cases(root: Path, commit: str, backend: str) -> dict[str, Any]:
    require(backend in ("native", "stub"), "known backend")
    before = inventory(root)
    names = {"manifest.json"} | {c["name"] + ".json" for c in cases()}
    require(set(before) in (names, names | {"summary.json"}), "exact tensor inventory")
    equal(
        read_record(root / "manifest.json"),
        dict(
            protocol="sdpa_tensor_plan_v1",
            source_commit=commit,
            backend=backend,
            cases=cases(),
            process_timeout_seconds=90,
            model_loads=0,
            model_generate_calls=0,
        ),
        "tensor manifest",
    )
    outcomes, pids, candidate, inputs = [], [], True, {}
    for case in cases():
        row = read_record(root / (case["name"] + ".json"))
        pid = row["pid"]
        require(type(pid) is int and pid > 0, "positive PID")
        pids.append(pid)
        common = dict(
            protocol="sdpa_tensor_case_v1",
            case=case,
            backend=backend,
            pid=pid,
            model_loads=0,
            model_generate_calls=0,
            tensor_values_retained=False,
        )
        equal({k: row[k] for k in common}, common, "case identity")
        if backend == "stub":
            equal(row, {**common, "native_verified": False, "status": "SIMULATED"}, "stub scope")
            continue
        equal(
            row["environment"],
            dict(
                torch="2.10.0+cu128",
                cuda="12.8",
                transformers="5.5.0",
                hf_sdpa_sha256=SDPA_SHA,
                device_name="Tesla T4",
                capability=[7, 5],
            ),
            "native environment",
        )
        require(row["native_verified"] is True and row["status"] == "OBSERVED", "native evidence")
        equal(row["allocator_cap_bytes"], CAP, "tensor-only cap")
        require(row["hf_use_gqa"] is True, "pinned HF unmasked GQA branch")
        require(
            set(row["native_eligibility"]) == {"flash", "efficient", "cudnn"}
            and all(type(v) is bool for v in row["native_eligibility"].values()),
            "native backend eligibility observations",
        )
        require(len(row["input_sha256"]) == 3, "QKV fingerprints")
        for value in row["input_sha256"]:
            sha(value)
        if case["name"].endswith(("long_native", "long_repeat")):
            inputs[case["name"]] = row["input_sha256"]
        modes = ["native", "repeat"] if case["mode"] == "parity" else [case["mode"]]
        equal([m["mode"] for m in row["modes"]], modes, "treatment order")
        for m in row["modes"]:
            require(positive(m["instrumented_seconds"]), "call timing")
            for label in ("before", "after"):
                mem = m[label]
                require(
                    all(type(v) is int and v >= 0 for v in mem.values()), "memory integer bytes"
                )
                require(
                    mem["allocated"] <= mem["reserved"] <= mem["peak_reserved"] <= CAP,
                    "allocator reserved cap",
                )
                require(
                    mem["allocated"] <= mem["peak_allocated"] <= mem["peak_reserved"],
                    "allocator peak",
                )
                require(mem["global_free"] <= mem["global_total"], "global memory")
            require(m["status"] in ("OK", "OOM", "ERROR"), "bounded observed status")
            if m["status"] != "OK":
                equal(
                    m["error_class"],
                    "OutOfMemoryError" if m["status"] == "OOM" else "RuntimeError",
                    "failure class",
                )
                require(m["output_shape"] is None and m["output_finite"] is None, "no OOM output")
                if m["mode"] == "repeat" or case["mode"] == "parity" or m["status"] == "ERROR":
                    candidate = False
            else:
                require(m["error_class"] is None and m["output_finite"] is True, "finite output")
                equal(
                    m["output_shape"], [1, case["query_tokens"], case["heads"], 128], "output shape"
                )
                if m["mode"] == "repeat":
                    require(
                        "aten::_scaled_dot_product_efficient_attention" in m["operators"],
                        "forced efficient operator observed",
                    )
                    require(
                        not any("math" in op or "flash" in op for op in m["operators"]),
                        "no silent fallback",
                    )
            outcomes.append(
                dict(
                    case=case["name"],
                    mode=m["mode"],
                    status=m["status"],
                    operators=m["operators"],
                    peak_allocated=m["after"]["peak_allocated"],
                    instrumented_seconds=m["instrumented_seconds"],
                )
            )
        parity = row["parity"]
        if case["mode"] == "parity" and all(m["status"] == "OK" for m in row["modes"]):
            equal(parity["atol"], ATOL, "predeclared absolute tolerance")
            equal(parity["rtol"], RTOL, "predeclared relative tolerance")
            require(parity["max_abs_error"] >= 0, "nonnegative difference")
            equal(parity["passed"], parity["max_tolerance_excess"] <= 0, "parity decision")
            candidate = candidate and parity["passed"]
        else:
            require(parity is None, "no unmeasured parity")
    if backend == "native":
        require(len(set(pids)) == 10, "fresh native process per case")
        for role in ("agent", "guard"):
            equal(
                inputs[f"{role}_long_native"], inputs[f"{role}_long_repeat"], "paired long inputs"
            )
    result = dict(
        protocol="sdpa_tensor_audit_v1",
        valid=True,
        source_commit=commit,
        backend=backend,
        native_verified=backend == "native",
        candidate_valid=candidate if backend == "native" else None,
        phase5_accepted=False,
        model_loads=0,
        model_generate_calls=0,
        case_count=10,
        outcomes=outcomes,
        scope="Synthetic tensor feasibility/parity only; no full model, KV cache, "
        "original OOM attribution or uninstrumented speed claim",
    )
    if "summary.json" in before:
        equal(read_record(root / "summary.json"), result, "worker/independent summary")
    equal(inventory(root), before, "immutable tensor evidence")
    return result
