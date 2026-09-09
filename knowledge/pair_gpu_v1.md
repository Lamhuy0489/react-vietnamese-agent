# Pair GPU v1 preparation — 2026-09-09

[Contract](../docs/architecture/phase5_pair_gpu_v1_contract.md). One private offline
two-T4 technical pair, agent readiness then guard, one small call each, cleanup
and six recovery samples. Not max-context stress, guard selection, policy runtime
integration or Phase5 closure. All large weights remain on Kaggle.

Preflight found a concrete native-library mismatch: exact pinned Transformers5.5
wheel registers original_inv_freq in addition to inv_freq. New agent_hf_v2
admits exactly the two64-element native buffers, same shapes/dtypes/devices and
unchanged339FP16parameters. Original v1 stays frozen. Wheel/internal source hashes
are recorded in the contract. No GPU failure or Test output prompted this fix.

New HF entry point pins expected agent runtime identity and guard revision,
uses v2 agent factory and unchanged guard factory in ModelPair. Requires native
torch2.10.0+cu128/CUDA12.8/Transformers5.5.0; no dynamic torch reinstall. Kaggle
image digest was empty in prior GPU metadata, so request original image pinning
and verify versions/actual tensor operations, without claiming a Docker SHA pin.

Standalone wrapper embeds the frozen PAX-aware bootstrap plus11allowed overlay
files and exact source/manifest hashes. Private guard Dataset v1 remains unchanged;
agent uses pinned read-only Qwen7B model mount. No whole-repo/credential/Test/GT/
knowledge upload. `prepare_phase5_model_pair.py` performs exact archive/expanded
simulations, fresh isolated venv,8tools/fault,21Dummy/completed+missing-only resume
and the same new worker entry point in stub mode. Actual HF mode is not run locally.

22new targeted tests pass; full QA01:1.352tests/361,66s. Final-source QA02:
1.352tests/328,89s pass; setup/Ruff/mypy229files/knowledge pass.
[Pre-submit QA](../experiments/manifests/phase5_pair_gpu_v1_pre_submit_qa01.json).
Source b76c040 exact preflight02 passes archive and expanded/PAX layouts,
8tools/fault,21Dummy, completed/missing-only resume preserving20checkpoints,
two synthetic pair calls and reap/recovery per layout. No actual model/GPU locally.
[Selected receipt](../experiments/manifests/phase5_pair_gpu_v1_preflight02.json).
Next inspect metadata/credential exclusion, push source/preflight, verify private
Dataset version, then submit once `huylmhuhu/react-vn-pair-gpu-v1`, timeout3600s.
Live quota29,33h; Dataset READY; kernel slug absent. No submission yet.
Preserve failed attempts; no semantic retries.

Exact preflight01 caught a local mount-simulation issue after8tools/21Dummy/resume
passed: macOS tempfile spelled the scratch path through /var, a symlink to
/private/var. Strict no_links correctly rejected the probe output. Fix only the
builder's own newly-created scratch root with resolve(); model-path checks stay
unchanged. Keep preflight01 wrapper/failure; run new clean-source preflight02.
