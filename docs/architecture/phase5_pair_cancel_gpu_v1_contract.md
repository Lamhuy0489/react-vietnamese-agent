# Pair cancellation GPU v1 submission contract

Execute the unchanged three-trial [CPU-frozen protocol](phase5_pair_cancellation_v1_contract.md)
using Qwen7B AgentHFBackendV2 and pinned Qwen1.5B GuardHFFactory. Both factories
remain lazy until their task-owned spawn worker loads. Wrap them with BusyFactory
only for host diagnostic commands; zero model.generate, no quality or Test run.

Each trial uses the original agent1200/guard120s cold deadlines,180/120s busy
deadlines, terminate0.5/kill1s graces,12/7GiB agent caps,5GiB guard/device1.
Three fresh pairs, stop after any failure. Keep old CPU/GPU evidence untouched.
No native-generation cancellation, context maximum, runtime integration or Phase5
acceptance claim. Real CUDA busy loops retain weights, not a semantic workload.

New private offline two-T4 handle `huylmhuhu/react-vn-pair-cancel-v1`, title
`ReAct VN Pair Cancel v1`, one submission, wall-clock timeout5400s including
three live-hashed model loads and setup. No automatic retries or account cycling.
Re-use private guard Dataset11942593/version1, original source7649d5b/manifest
and wheel hashes; pinned `qwen-lm/qwen2.5/transformers/7b-instruct/1` read-only mount.
No weight copies locally; no new Dataset upload, whole repo, credentials or Test.

Request exact Docker image observed in pair GPU v1:
`gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`.
Installed CLI passes docker_image plus original pinning; verify returned metadata
and actual torch2.10.0+cu128/CUDA12.8/Transformers5.5.0 before weights load.
If rejected or changed, retain evidence and classify; do not silently substitute.

Standalone cancellation wrapper embeds frozen PAX-aware bootstrap and13file
allowlist: original11pair GPU overlay files plus pair_cancellation_v1 and the
new cancellation entry script. Check previous11hashes and CPU-frozen cancellation
module. No overwrite of base source. Run exact rendered wrapper in isolated
archive/expanded/PAX layouts,8tools/fault,21Dummy/completed+missing-only resume,
then all3cancellation trials through the actual new entry point in stub mode.
Only wrapper and metadata remain in upload folder. Source/full QA/receipt must
be pushed before quota/private Dataset/version verification and GPU submission.

Download outputs to a fresh directory after completion, even on failure. Audit
source/metadata/manifest/identities, request/deadline hashes, raw immutability,
busy-marker PID/CUDA role, six HF load records, reap/terminate/KILL, all18recovery
samples and21Dummy/84events. Report actual idle-worker graceful flags separately.
No benchmark response or hidden reasoning is requested or stored.
