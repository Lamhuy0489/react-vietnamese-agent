# Worker startup mount repair — 2026-10-02

The owner explicitly authorized operating the two selected collaborator workers:
lamhuy8904/Qwen3-8B and meanalways/Llama3.2-3B-Instruct. Both private kernels were
submitted once as version 1, using source e4078d7d5d2fe66a881e53ec5f194e3f9aa66b47.
Read-only quota admission reported 20.67h and 19.88h GPU remaining respectively.
Remote source bytes matched the exact preflighted package, and remote metadata
confirmed private kernels, NvidiaTeslaT4 and the intended model input version 1.

Guard version 1 failed before model load with EXACT_MODEL_MOUNT_MISSING. It had
already passed the two-T4 tensor checks. Its raw logs and remote source remain
under build/operations/phase5_pair_20261002 and the original frozen package.
This is an infrastructure startup failure, not a semantic benchmark result.
No host Dev inference has been sent to this pair.

The loader previously assumed only /kaggle/input/models/OWNER/MODEL/FRAMEWORK/
VARIATION/VERSION. The repair also admits the exact legacy layout at
/kaggle/input/MODEL/FRAMEWORK/VARIATION/VERSION. It rejects ambiguous layouts,
symlinks, invalid handles and other versions; no recursive model search or
automatic model download is introduced. The existing full model-file
fingerprint and authenticated worker identity remain mandatory.

The first failure does not prove the legacy path exists on this worker. The
replacement includes bounded public-path diagnostics if neither exact path is
available. Native verification remains necessary; CPU QA is not a mount proof.
Kaggle's cache resolver derives mounted paths from the backend mountSlug, so a
hardcoded owner-prefixed path is not a universal platform guarantee:
[official implementation](https://github.com/Kaggle/kagglehub/blob/main/src/kagglehub/kaggle_cache_resolver.py).

Source/config change requires a new package/session and new source commit before
submission. Preserve version 1 and the historical v1 uncertain experiments.
Model names, input versions, FP16, prompt/generation settings and Dev fixtures
are unchanged; no Test or private ground truth is accessed. Do not resubmit a
still-running version merely because logs are not yet available.

Validation before source freeze: 54 targeted tests passed (mount regression,
structured API, exact worker package, entrypoint and native closure runner).
Setup, repository Ruff and mypy (630 source files) passed. Full repository
pytest was not rerun; exact replacement-package preflight and native checks are
recorded separately after packaging. Phase 5 is not accepted.
