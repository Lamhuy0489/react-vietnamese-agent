"""Real-spawn ordinary-request rehearsal: native tqdm, synthetic model/tensor objects."""

from __future__ import annotations

import argparse
import importlib
import json
import multiprocessing as mp
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import FunctionType
from types import SimpleNamespace as NS
from typing import Any, cast

from react_agent.foundation.normalization import text_hash
from react_agent.llm import efficient_requests_v1 as adapter
from react_agent.llm.agent_hf_v2 import AgentHFBackendV2
from react_agent.llm.agent_mount_v1 import MODEL, no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.guard_hf_v1 import GuardHFBackend, GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import MODEL_ID
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig, Role
from react_agent.llm.request_pair_v1 import request_pair
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory
from react_agent.validation.efficient_requests_audit_v1 import audit
from react_agent.validation.guard_probe_audit_v2 import require

CASES = ("success", "reversed", "agent_error", "guard_error")
REQUESTS = ((1, 1), (4096, 3), (1, 1))
ROLES: tuple[Role, Role] = ("agent", "guard")


def synthetic_libraries() -> tuple[Any, Any]:
    enabled = dict(flash=True, math=True, mem_efficient=True, cudnn=True)

    def sdpa(q: Any, k: Any, v: Any, **kw: Any) -> Any:
        return q

    @contextmanager
    def kernel(backend: Any) -> Any:
        require(backend == "efficient", "synthetic efficient selection")
        before = enabled.copy()
        enabled.update(flash=False, math=False, mem_efficient=True, cudnn=False)
        try:
            yield
        finally:
            enabled.update(before)

    hf = NS(__name__="synthetic_hf", use_gqa_in_sdpa=lambda mask, key: True)
    hf.use_gqa_in_sdpa.__module__ = hf.__name__
    hf.sdpa_attention_forward = FunctionType((lambda: None).__code__, vars(hf))
    torch = NS(
        float16="float16",
        bool="bool",
        _C=NS(_nn=NS(scaled_dot_product_attention=sdpa)),
        nn=NS(
            functional=NS(scaled_dot_product_attention=sdpa),
            attention=NS(sdpa_kernel=kernel, SDPBackend=NS(EFFICIENT_ATTENTION="efficient")),
        ),
        backends=NS(cuda=NS(**{n + "_sdp_enabled": (lambda n=n: enabled[n]) for n in enabled})),
    )
    return torch, hf


@dataclass(frozen=True)
class SyntheticNativeFactory:
    role: Role
    root: Path
    fail: bool = False

    def __call__(self) -> LLMBackend:
        require(mp.current_process().daemon and mp.get_start_method() == "spawn", "daemon spawn")
        require(not {"torch", "transformers"} & sys.modules.keys(), "no native model imports")
        std = importlib.import_module("tqdm.std")
        require(hasattr(std.tqdm, "_lock"), "progress configured before synthetic load")
        require(not hasattr(std.TqdmDefaultWriteLock, "mp_lock"), "no process progress lock")
        # Actual native constructors are NEVER called; objects only satisfy exact
        # factory type/identity admission. Per-instance generate is synthetic.
        native: Any = object.__new__(AgentHFBackendV2 if self.role == "agent" else GuardHFBackend)
        native.model_id = MODEL if self.role == "agent" else MODEL_ID
        native.model_revision = AGENT_REVISION if self.role == "agent" else adapter.GUARD_REVISION
        if self.role == "guard":
            native.config = GuardHFConfig()
        torch, hf = synthetic_libraries()
        adapter.libraries = lambda: (torch, hf)  # type: ignore[attr-defined]
        write_receipt(
            self.root / f"{self.role}_shape.json",
            dict(
                pid=os.getpid(),
                parent_pid=os.getppid(),
                role=self.role,
                synthetic=True,
                model_loads=0,
                progress_before_load=True,
                daemon=True,
                start_method="spawn",
            ),
        )
        metrics = self.root / f"{self.role}_metrics.jsonl"
        rows: list[dict[str, Any]] = []

        def save(row: dict[str, Any]) -> None:
            with metrics.open("x" if not rows else "a") as stream:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            rows.append(row)

        save(
            dict(
                event="load",
                synthetic=True,
                model_id=native.model_id,
                model_revision=native.model_revision,
                dtype="float16",
                attention="sdpa",
                quantization=None,
                torch_version="2.10.0+cu128",
                transformers_version="5.5.0",
                cuda_version="12.8",
                load_seconds_including_hashes=1.0,
                protocol="agent_hf_dual_gpu_v1"
                if self.role == "agent"
                else "guard_hf_single_gpu_v1",
                adapter_protocol="agent_hf_dual_gpu_v2_tf550" if self.role == "agent" else None,
            )
        )

        def generate(messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
            index = len(rows)
            inputs, outputs = REQUESTS[index - 1]
            require(
                messages == [dict(role="user", content=f"synthetic-{inputs}-{outputs}")],
                "unchanged synthetic request",
            )
            row = dict(
                event="generate",
                call_index=index,
                synthetic=True,
                input_tokens=inputs,
                output_tokens=outputs,
                generate_seconds=0.1,
                call_seconds=0.2,
                generation_sha256=text_hash(config.model_dump_json()),
            )
            if self.fail:
                save(dict(row, status="ERROR"))
                raise RuntimeError("injected synthetic generation failure")
            for i in range(28 * outputs):
                forward, layer = divmod(i, 28)
                heads = 28 if self.role == "agent" else 12
                device = f"cuda:{0 if self.role == 'agent' and layer < 20 else 1}"
                query, key = inputs if forward == 0 else 1, inputs + forward

                def tensor(length: int, heads: int = heads, device: str = device) -> Any:
                    return NS(shape=(1, heads, length, 128), dtype="float16", device=device)

                q, k, v = tensor(query), tensor(key), tensor(key)
                require(hf.use_gqa_in_sdpa(None, k) is False, "synthetic helper interception")
                torch.nn.functional.scaled_dot_product_attention(
                    q, k, v, attn_mask=None, dropout_p=0.0, scale=128**-0.5, is_causal=query > 1
                )
            save(dict(row, status="OK"))
            return ModelResponse(
                text="synthetic-ack", model_id=native.model_id, model_revision=native.model_revision
            )

        native.generate = generate
        return cast(LLMBackend, native)


def run(root: Path) -> dict[str, Any]:
    no_links(root)
    root.mkdir(parents=True, exist_ok=False)
    summaries = []
    all_pids: list[int] = []
    for case in CASES:
        trial = root / case
        trial.mkdir()
        attention = trial / "attention"
        config = PairConfig(
            ModelIdentity(MODEL, AGENT_REVISION),
            ModelIdentity(MODEL_ID, adapter.GUARD_REVISION),
            agent_start_seconds=15,
            guard_start_seconds=15,
            agent_call_seconds=10,
            guard_call_seconds=10,
        )
        agent = SyntheticNativeFactory("agent", trial, case == "agent_error")
        guard = SyntheticNativeFactory("guard", trial, case == "guard_error")
        if case == "reversed":
            # Deliberately wrong ordering: attention receives ReadyBackend instead
            # of the exact native object. Failure must occur before generation.
            pair = ModelPair(agent, guard, config)
            for role in ROLES:
                worker = pair._workers[role]
                worker.factory = ThreadProgressFactory(
                    adapter.EfficientRequestFactory(worker.factory, role, attention / role)
                )
        else:
            pair = request_pair(agent, guard, config, attention)
        error = None
        try:
            pair.start()
            require(not attention.exists(), "readiness must not consume a request")
            write_receipt(trial / "ready.json", pair.snapshot())
            roles: tuple[Role, ...] = (
                ("agent", "guard")
                if case == "success"
                else ("agent" if case == "agent_error" else "guard",)
            )
            for role in roles:
                for inputs, outputs in REQUESTS:
                    response = pair.generate(
                        role,
                        [dict(role="user", content=f"synthetic-{inputs}-{outputs}")],
                        GenerationConfig(max_new_tokens=512 if role == "agent" else 128),
                    )
                    require(response.text == "synthetic-ack", "synthetic transport response")
        except RuntimeError:
            error = "RuntimeError"
        finally:
            pair.close()
        closed = pair.snapshot()
        write_receipt(trial / "closed.json", closed)
        require(
            all(not w["handle_pending"] for w in closed["workers"].values()), "all workers reaped"
        )
        require((error is None) == (case == "success"), "declared control outcome")
        attempts_before = {r: len(w["attempts"]) for r, w in closed["workers"].items()}
        try:
            pair.generate(
                "agent", [dict(role="user", content="synthetic-retry")], GenerationConfig()
            )
        except RuntimeError:
            pass
        else:
            raise ValueError("closed/failed pair accepted a retry")
        require(
            attempts_before
            == {r: len(w["attempts"]) for r, w in pair.snapshot()["workers"].items()},
            "no retry attempt",
        )
        audits = {}
        statuses = {}
        for role in ROLES:
            attempts = closed["workers"][role]["attempts"]
            statuses[role] = [a["status"] for a in attempts]
            expected = (
                ["OK"] * 4
                if case == "success"
                else (
                    (["BACKEND_FAILURE"] if role == "agent" else [])
                    if case == "reversed"
                    else ["OK", "BACKEND_FAILURE"]
                    if case == role + "_error"
                    else ["OK"]
                )
            )
            require(statuses[role] == expected, "readiness/warm attempt order")
            if not attempts:
                require(not (trial / f"{role}_shape.json").exists(), "unstarted sibling")
                continue
            shape = json.loads((trial / f"{role}_shape.json").read_text())
            pid = attempts[0]["pid"]
            require(shape["pid"] == pid and shape["parent_pid"] == os.getpid(), "sibling PID")
            require(
                all(
                    a["pid"] == pid and a["cold_start"] is (i == 0) for i, a in enumerate(attempts)
                ),
                "one resident worker per role",
            )
            all_pids.append(pid)
            if case == "success":
                audits[role] = audit(
                    attention / role,
                    trial / f"{role}_metrics.jsonl",
                    role=role,
                    worker_pid=pid,
                    expected_requests=3,
                )
            elif case == role + "_error":
                request = attention / role / "request_000001"
                require(
                    sorted(p.name for p in request.iterdir())
                    == ["entered.json", "error.json", "restored.json"],
                    "partial error records preserved",
                )
                require(
                    json.loads((request / "restored.json").read_text())["state_restored"] is True,
                    "failed request restored",
                )
        summaries.append(
            dict(
                case=case,
                statuses=statuses,
                error=error,
                all_handles_reaped=True,
                no_retry_attempt=True,
                audits=audits,
            )
        )
    require(
        len(all_pids) == 7 and len(set(all_pids)) == 7 and os.getpid() not in all_pids,
        "seven fresh child identities",
    )
    result = dict(
        protocol="request_pair_cpu_rehearsal_v1",
        valid=True,
        phase5_accepted=False,
        synthetic=True,
        model_loads=0,
        native_model_calls=0,
        gpu_runs=0,
        worker_pids=all_pids,
        rows=summaries,
        scope="Real spawn/native tqdm; synthetic models/tensors/metrics, "
        "not native parity or performance",
    )
    write_receipt(root / "summary.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
    print("REQUEST_PAIR_CPU_COMPLETE synthetic=True native_model_calls=0")
