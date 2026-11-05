#!/usr/bin/env python3
"""Keep a Kaggle vLLM serve notebook from idling out (Study 2).

The serve notebook stops after ``IDLE_MINUTES`` without a *successful* completion
(``vllm:request_success_total``), so a GET is not enough: every ``--every`` minutes this
sends one chat completion with ``max_tokens=1`` to the served model. It stops after
``--hours`` (the notebook itself stops at ``MAX_HOURS``) or after 3 consecutive failures
(endpoint gone). Reads ``VLLM_BASE_URL``/``VLLM_API_KEY`` from the folder's ``endpoint.env``;
never prints them.

    .venv/bin/python scripts/keepalive_vllm_v1.py --folder build/kaggle/<serve folder> --hours 6
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path


def read_env(folder: Path) -> dict[str, str]:
    values = {}
    for line in (folder / "endpoint.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip().removeprefix("export ").strip()] = value.strip().strip("'\"")
    return values


def call(base: str, key: str, path: str, payload: dict[str, object] | None) -> dict[str, object]:
    request = urllib.request.Request(  # noqa: S310 - https tunnel URL from endpoint.env
        base.rstrip("/") + path, method="POST" if payload else "GET",
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        value: dict[str, object] = json.loads(response.read())
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--hours", type=float, default=6)
    parser.add_argument("--every", type=float, default=20, help="minutes between pings")
    args = parser.parse_args()
    env = read_env(args.folder)
    base, key = env["VLLM_BASE_URL"], env["VLLM_API_KEY"]
    deadline, failures = time.time() + args.hours * 3600, 0
    while time.time() < deadline:
        try:
            models = call(base, key, "/models", None)
            data = models["data"]
            served = [m["id"] for m in data] if isinstance(data, list) else []
            call(base, key, "/chat/completions", {
                "model": served[-1], "max_tokens": 1, "temperature": 0,
                "messages": [{"role": "user", "content": "ping"}]})
            failures = 0
            print(time.strftime("%H:%M"), "ping ok", flush=True)
        except Exception as exc:  # noqa: BLE001 - any failure counts; stop after 3
            failures += 1
            print(time.strftime("%H:%M"), "ping failed", type(exc).__name__, flush=True)
            if failures >= 3:
                print("endpoint gone; stopping", flush=True)
                return 1
        time.sleep(args.every * 60)
    print("deadline reached", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
