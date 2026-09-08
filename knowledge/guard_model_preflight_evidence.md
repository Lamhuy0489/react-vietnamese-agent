# Guard candidate: evidence before GPU preflight

Access date: 2026-09-08. Question: which small, non-Meta candidate can test the
new task-local guard adapter before model-quality selection? This is not a
decision to use that guard in final experiments. Research contract unchanged.

## Claim-to-evidence

1. Qwen Team (2024), **Qwen2.5-1.5B-Instruct model card**:
   [official source](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct).
   Direct publisher evidence: 1.54B parameters, Apache-2.0, native Qwen2 causal
   architecture; family claims improved structured JSON and multilingual support
   including Vietnamese. The specific model lists 32,768 context tokens.
   These are publisher claims, not measured Vietnamese injection-detection quality.
2. Qwen repository, **immutable candidate revision**:
   [commit 989aa7980e4cf806f80c7fef2b1adb7bc71aa306](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/commit/989aa7980e4cf806f80c7fef2b1adb7bc71aa306).
   Direct evidence of a resolvable upstream revision, not evidence that local
   weights have been downloaded or verified. No Kaggle variation/version or
   equivalence with a Kaggle snapshot has been established for this candidate.
3. Hugging Face, **Accelerate big-model inference**, live documentation:
   [device maps and memory guidance](https://huggingface.co/docs/accelerate/en/concept_guides/big_model_inference).
   Direct guidance: weight-placement budgets need CUDA/generation headroom;
   automatic mapping can offload. Inference for this project: the previous
   agent-only 13 GiB/device profile cannot be assumed to coexist with a guard.
   No combined-agent OOM or successful fit has been measured in this milestone.

## Engineering choice and limits

Prepare one bounded offline adapter for this candidate. Approximate FP16 weight
storage from parameter count is about 3.1 GB (arithmetic estimate only), excluding
activations, cache, allocator fragmentation and CUDA context. A 5 GiB guard
allocator cap plus 1 GiB free headroom is a technical test configuration, not a
guarantee of fit. Agent placement still needs a separately versioned profile.

[Adapter contract](../docs/architecture/phase5_guard_hf_contract.md) separates CPU
fake evidence, upstream identity, local content hashes and future GPU results.
No official weights acquired, no benchmark/Test accessed, no model quality score.
No new account or Meta authorization is required for local implementation.
Before upload, selected Kaggle account/quota/private Dataset and offline packages
must be verified under the Kaggle skills; do not cycle credentials for quota.
