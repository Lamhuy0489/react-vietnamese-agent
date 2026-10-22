#!/usr/bin/env python3
"""Check identity and one constrained agent turn on a vLLM endpoint (VLLM_BASE_URL/KEY)."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml

from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import HTTPSJSON
from react_agent.llm.openai_compat_v1 import OpenAICompatBackend

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--revision")
    args = parser.parse_args()
    spec = yaml.safe_load((ROOT / "configs/models/backbones_v2.yaml").read_text())[args.model_key]
    revision = args.revision or spec["revision"]
    base_url, api_key = os.environ.get("VLLM_BASE_URL"), os.environ.get("VLLM_API_KEY")
    if not revision or not base_url or not api_key:
        raise SystemExit("Need a pinned revision, VLLM_BASE_URL and VLLM_API_KEY")
    backend = OpenAICompatBackend(HTTPSJSON(base_url, api_key, timeout=150), repo=spec["repo"],
                                  revision=revision,
                                  chat_template_kwargs=spec.get("chat_template_kwargs"))
    backend.probe()
    response = backend.generate([
        {"role": "system", "content": "Chỉ trả về một JSON object theo schema."},
        {"role": "user", "content": "Tìm tài liệu về lịch thi học kỳ bằng công cụ doc_search."},
    ], GenerationConfig())
    print(json.dumps({"identity": "OK", "output": json.loads(response.text),
                      "call": backend.calls[-1]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
