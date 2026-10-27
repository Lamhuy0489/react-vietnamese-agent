#!/usr/bin/env python3
"""Keep idle vLLM notebooks alive between runs.

The serving notebook shuts down after 30 minutes without a successful completion.
Every ``--every`` minutes this sends a 1-token completion to each endpoint, but
only while none of that endpoint's log files changed in the last 5 minutes, so a
ping never shares a batch with a scored request. ``--endpoint`` takes
``ENV_FILE`` or ``ENV_FILE=LOG1,LOG2``. Stop it with Ctrl-C or kill.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.openai_compat_v1 import OrderedHTTPSJSON


def read_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text().splitlines():
        key, _, value = line.removeprefix("export ").partition("=")
        if key and value:
            values[key.strip()] = value.strip().strip("'\"")
    return values


def busy(logs: list[Path], quiet_seconds: float = 300) -> bool:
    now = time.time()
    return any(log.exists() and now - log.stat().st_mtime < quiet_seconds for log in logs)


def ping(env: dict[str, str]) -> str:
    transport = OrderedHTTPSJSON(env["VLLM_BASE_URL"], env["VLLM_API_KEY"], timeout=60)
    model = transport("GET", "/models", None)["data"][0]["id"]
    transport("POST", "/chat/completions", {
        "model": model, "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1, "temperature": 0})
    return str(model)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", nargs="+", required=True,
                        help="endpoint.env, optionally =comma-separated busy logs")
    parser.add_argument("--every", type=float, default=10, help="minutes")
    args = parser.parse_args()
    endpoints = []
    for item in args.endpoint:
        env, _, logs = item.partition("=")
        endpoints.append((Path(env), [Path(log) for log in logs.split(",") if log]))
    while True:
        for path, logs in endpoints:
            if not busy(logs):
                try:
                    print(time.strftime("%H:%M"), "ping", ping(read_env(path)), flush=True)
                except (APIError, KeyError, IndexError, OSError) as exc:
                    print(time.strftime("%H:%M"), "ping failed", path.parent.name,
                          type(exc).__name__, flush=True)
        time.sleep(args.every * 60)


if __name__ == "__main__":
    main()
