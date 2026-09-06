#!/usr/bin/env python3
"""CPU-only loader/template tests without inference on benchmark tasks."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from pathlib import Path

from react_agent.llm.pilot_profiles import PROFILES, adapt_messages, find_pilot_model


def main() -> int:
    import torch  # type: ignore[import-not-found]
    import transformers as tr  # type: ignore[import-not-found]

    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(42)
    for key in ("gemma4", "qwen7b"):
        profile = PROFILES[key]
        model_path = find_pilot_model(args.input_root, profile)
        config = tr.AutoConfig.from_pretrained(model_path, local_files_only=True)
        tokenizer = tr.AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        messages = [
            {"role": "system", "content": "A0 schema probe"},
            {"role": "user", "content": "Synthetic task"},
            {"role": "assistant", "content": "Action"},
            {"role": "user", "content": "Observation"},
            {"role": "user", "content": "Correction"},
        ]
        prompt = tokenizer.apply_chat_template(
            adapt_messages(messages, profile.chat_adapter),
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        assert "<|think|>" not in prompt  # noqa: S101 - explicit preflight acceptance
        assert all(m["content"] in prompt for m in messages)  # noqa: S101
        tokens = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        assert tokens["input_ids"].shape[-1] > 0  # noqa: S101
        print(f"PASS tokenizer/config: {key} {config.model_type}", flush=True)
    gemma = tr.Gemma4ForCausalLM(
        tr.Gemma4TextConfig(
            vocab_size=64,
            hidden_size=32,
            intermediate_size=64,
            num_hidden_layers=2,
            num_attention_heads=2,
            num_key_value_heads=1,
            head_dim=16,
            global_head_dim=16,
            vocab_size_per_layer_input=64,
            hidden_size_per_layer_input=8,
            max_position_embeddings=64,
            sliding_window=16,
            layer_types=["sliding_attention", "full_attention"],
        )
    )
    qwen = tr.Qwen2ForCausalLM(
        tr.Qwen2Config(
            vocab_size=64,
            hidden_size=32,
            intermediate_size=64,
            num_hidden_layers=2,
            num_attention_heads=2,
            num_key_value_heads=1,
            max_position_embeddings=64,
        )
    )
    for model in (gemma, qwen):
        model.eval()
        with torch.inference_mode():
            output = model.generate(
                input_ids=torch.tensor([[2, 4, 5]]),
                max_new_tokens=2,
                do_sample=False,
                pad_token_id=0,
                eos_token_id=None,
            )
        assert output.shape == (1, 5)  # noqa: S101
    assert hasattr(tr, "Gemma4ForConditionalGeneration")  # noqa: S101
    report = {
        "valid": True,
        "gpu_used": False,
        "benchmark_model_runs": 0,
        "template_profiles": ["gemma4", "qwen7b"],
        "tiny_random_generation_models": 2,
        "versions": {p: version(p) for p in ("torch", "transformers", "tokenizers", "accelerate")},
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
