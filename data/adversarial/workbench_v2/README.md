# Executable authoring workbench v0.1

Four synthetic canonical pairs, unsplit and review-pending. Not part of the
70-family benchmark and not a repaired/resealed v1. No variants or Test split.

`public/` contains legitimate model-facing instructions only. `overlays/`
contains synthetic environment inputs; only tool observations expose content.
`private/` is offline fixture ground truth and must never be sent to workers,
prompts, policies or models. No worker-packaging command is provided here.

Local Replay scripts validate reachability, safe utility and negative oracles;
they do not measure LLM performance, ASR, FPR or language quality. Review is
pending, not attributed to either project owner or collaborator.
