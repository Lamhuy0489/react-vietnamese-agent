# Public Llama distribution option — 2026-10-02

Question: can the existing Llama guard operate without Kaggle model-file approval?

Direct read-only verification on Hugging Face, without authentication:
- [Unsloth distribution](https://huggingface.co/unsloth/Llama-3.2-3B-Instruct):
  API metadata gated=false, private=false, license=llama3.2,
  base_model=meta-llama/Llama-3.2-3B-Instruct.
- Pinned revision:006f5dcd1393c3add266de40994ba96225e9689d.
- HEAD of model-00001-of-00002.safetensors at that revision returned200
  anonymously, Content-Length4965799096. No weight bytes downloaded.
- config.json: model_type=llama, torch_dtype=bfloat16, no quantization_config.
- [Meta repository](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct):
  API metadata gated=manual, revision0cb88a4f764b7a12671c53f0838cd831a0843b95.

Inference: Kaggle model attachment is not required if the notebook downloads
this public licensed distribution over Internet. This does not remove the
Llama3.2 license obligations or prove bit-identical weights/tokenizer against
the historical Kaggle input. Anonymous HEAD proves accessibility of one shard
at check time, not full download integrity, GPU load or model quality.

Recommendation: retain Qwen worker, replace only guard input acquisition with
an explicit pinned Hugging Face snapshot. Keep local files only for model load,
verify required weight/tokenizer/config hashes, preserve FP16 runtime and exact
model/generation identity, preflight source, freeze/push before GPU submission.
Use a new package/session/run identity; never mix results with the previous
Kaggle-mounted guard without declared source equivalence checks. Do not silently
substitute a quantized, fine-tuned or different-size model.

This note authorizes no acceptance claim. Notebook source is not yet changed;
no new GPU submission, no model download, no Dev/Test inference in this check.
The two failed Kaggle guard versions and their403 access receipts remain intact.
