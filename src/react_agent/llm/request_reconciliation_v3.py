"""Validate authenticated v3 status without erasing or retrying an uncertain attempt."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from react_agent.llm.session_journal_v1 import save_new
from react_agent.serving.structured_api_v1 import canonical, sha

IDENTITY = frozenset({"instance_id", "session_id", "source_commit", "worker_sha256",
                      "model_revision", "model_id", "role"})


def verify_terminal_status(*, identity: dict[str, str], request_id: str,
                           request_sha256: str, response: dict[str, Any]) -> dict[str, Any]:
    """Return only a terminal receipt after exact identity/hash and cleanup checks.

    Caller must authenticate the transport. This cannot verify worker honesty or
    authorize a rerun. A terminal receipt resolves execution status, not utility.
    An instance-retired result is deliberately kept blocked even if synchronized.
    """
    if (set(identity) != IDENTITY or not all(identity.values())
            or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", request_id)
            or not re.fullmatch(r"[0-9a-f]{64}", request_sha256)):
        raise ValueError("invalid expected request identity")
    if response.get("identity") != identity:
        raise ValueError("worker or boot identity mismatch")
    status = response.get("request")
    if not isinstance(status, dict) or (
            status.get("instance_id") != identity["instance_id"]
            or status.get("request_id") != request_id
            or status.get("request_sha256") != request_sha256):
        raise ValueError("request identity mismatch")
    if (status.get("state") not in {"SUCCEEDED", "FAILED", "CANCELLED"}
            or status.get("engine_returned") is not True
            or status.get("engine_active") is not False
            or status.get("gpu_quiescence_attested") is not True
            or status.get("quiescence_basis") != "device_synchronize"
            or status.get("durable") is not True
            or status.get("instance_retired") is not False):
        raise ValueError("request remains unresolved or instance retired")
    code = status.get("http_status")
    digest = status.get("response_sha256")
    if (type(code) is not int or not 200 <= code <= 599
            or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or (status["state"] == "SUCCEEDED" and code != 200)
            or (status["state"] == "FAILED" and code < 400)
            or (status["state"] != "CANCELLED" and status.get("cancel_requested") is not False)
            or (status["state"] == "CANCELLED" and
                (code != 409 or status.get("cancel_requested") is not True))):
        raise ValueError("invalid terminal outcome")
    return {"identity": dict(identity), "request_id": request_id,
            "request_sha256": request_sha256, "state": status["state"],
            "http_status": code, "response_sha256": digest,
            "remote_status_sha256": sha(canonical(response).encode()),
            "execution_resolved": True, "semantic_retry_authorized": False}


def save_resolution(path: Path, *, identity: dict[str, str], request_id: str,
                    request_sha256: str, response: dict[str, Any]) -> dict[str, Any]:
    """Append a new receipt only; never modifies the frozen v1 session journal."""
    receipt = verify_terminal_status(identity=identity, request_id=request_id,
                                     request_sha256=request_sha256, response=response)
    save_new(path, receipt)
    return receipt
