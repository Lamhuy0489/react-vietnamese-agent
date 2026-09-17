# Ghi chú Kaggle Phase 1

## Guard tokenizer / logits CPU compatibility — 2026-09-16

- [Native CPU report](../docs/evaluation/phase5_guard_language_native_v1_run.md):
  reuse pinned private Dataset but read only six tokenizer/config files, no
  weight payload/model.generate/GPU. Test actual libraries before inference.
- Source mount and tokenizer mount each need archive/expanded coverage. Execute
  the actual launcher CLI in an explicitly labelled metadata-only local rehearsal;
  it does not claim native imports passed. This CPU notebook completed at v1.
- Resume validation binds task checkpoints and identity; aggregate reports may
  legitimately change. Preserve failed preflight rather than weakening checkpoint
  checks or retrying model tasks.
- Do not extract a digest by splitting merged shell stdout/stderr: macOS locale
  warnings polluted a selected hash. Hash file bytes directly and require64hex;
  admission rejected this locally before any Kaggle submission. Keep the invalid
  selection and corrected selection distinct; do not rerun the package for it.
- Prefix masking alone is not full decoding-policy admission. Actual ForcedBOS
  after the mask can override it. Bind/check the complete processor chain and
  completion rules before opting a guard adapter into constrained generation.

## Seven-level runtime package / CLI reads — 2026-09-13

- Exact isolated mount found repository `validation/__init__.py` importing
  benchmark QA absent from the worker. Keep worker namespace packaging; do not
  add private/evaluator modules merely to satisfy an import. A second preflight
  caught an authoring-schema import; use a local public-only task schema instead.
  Both failed local identities remain intact; only preflight03 was submitted.
- Installed CLI 2.2.4 `kernels pull owner/slug/1` returned API 403 for this private
  kernel, while `pull owner/slug` succeeded. Authenticate returned code against
  the frozen wrapper hash and explicit remote private/offline/model/image/GPU
  metadata. Do not infer account failure or submit a replacement job from this.
- One-shot logs were empty while RUNNING; live `--follow` returned HTTP 500.
  Status subsequently became COMPLETE. Log-access failure is not evidence of
  inference failure. Preserve output, keep polling the same identity and never
  rerun semantic results to obtain a better score.
- [Run evidence and source pins](phase5_security_runtime_probe_v1.md).

## Combined cancellation GPU v1 — 2026-09-09

- Exact archive/expanded/PAX13file overlay preflight +17newtests trước submit;
  kernel COMPLETE lần đầu. Docker image digest yêu cầu khớp metadata tải ngược.
- Three pairs giữ model thật và small CUDA busy loop;6workers reaped,18samples
  VRAM về baseline. Không suy ra native autoregressive cancellation hoặc maxcontext.
- Log có warning3leaked semaphore objects lúc shutdown. Giữ warning như bằng
  chứng; resource-tracker warning không tự xác định nơi tạo hoặc persistent leak.
  GPU recovery pass không đồng nghĩa IPC cleanup verified, không tự unregister
  hoặc nới graces. [Report](../docs/evaluation/phase5_pair_cancel_gpu_v1_report.md).
- Cả3idle siblings vẫn TERMINATE, không graceful; phân biệt với ca guard-ignore
  chủ động KILL. Six HFloadrecords/zero generation,91rawfiles/21Dummy/84events;
  auditJSON/table lặp lại khớp bytes, không model rerun để lấy kết quả đẹp hơn.

## Pair GPU v1 completion — 2026-09-09

- First private pair kernel COMPLETE, exact wrapper two-layout preflight trước
  submit; không whole-repo/weights download local hoặc retry. [Report](../docs/evaluation/phase5_pair_gpu_v1_report.md).
- Kiểm native source trong wheel đã hash-pin phát hiện Transformers5.5 đăng ký
  thêm original_inv_freq. Sửa adapter v2 riêng và negative tests trước GPU;
  không sửa frozen v1 hoặc bỏ kiểm buffer/tensor inventory.
- macOS temp root /var là symlink: resolve chính scratch root mình vừa tạo
  trong builder, giữ strict no_links ở model/output. Giữ preflight01 failure,
  preflight02 hai layouts pass. Di chuyển generated __pycache__ ra ngoài thư
  mục upload để chỉ còn wrapper/metadata; không đổi bytes đã hash-pin.
- Remote metadata của run này trả Docker image digest; lưu đúng observed digest,
  không nói đã pin digest trước run. API framework label trả `Transformers`
  thay vì `transformers`; model owner/slug/variation/version1 không thay đổi.
- Cặp model fit ở context43/147tokens không chứng minh max-context. Cả hai worker
  cần TERMINATE/-15 mặc dù mọi recovery sample residual0bytes; không claim graceful.
- Inspector envelope/Dummy/recovery không thay thế technical self-review, không
  đánh giá quality. Output chỉ có response hashes và observable metrics, không CoT.

## Guard GPU v1 completion — 2026-09-08

- PAX-aware bootstrap v2 hoàn tất kernel v1 ngay lần submit đầu; không cần
  upload lại Dataset/model. Runtime/model/prompt bytes giữ nguyên.
- Pull private kernel với hậu tố `/1` trả403, latest pull thành công; kiểm
  downloaded wrapper hash với preflight thay vì claim version endpoint pass.
- `kernels output` tự tải kernel log ngoài file regex; audit inventory phải
  tính log thực có, không xóa nó để làm đẹp inventory.
- Four guard calls valid/repeatable không chứng minh quality: B vẫn SAFE.
  Hai workers dùng forced terminate/reap, không graceful; audit cũ phải giữ
  rejection, v2 reporting ghi riêng graceful flag. Không semantic retry.
- Một lượt tải gồm 56rawfiles, 21Dummy/84events và realCUDA trênT4; offline
  torch2.10.0+cu128/transformers5.5.0 chạy được với wheelhouse đã pin.
  [Audit và giới hạn](../docs/evaluation/phase5_guard_gpu_audit_deviation.md).

## Guard probe remote mount — 2026-09-08

- Dataset v1 create thành công nhưng status/metadata ban đầu HTTP 403 và
  mine-search chưa thấy; sau xử lý mới READY/v1/private. Không kết luận thiếu
  quyền từ lần đọc sớm hoặc create lại. Quota đọc được không chứng minh Dataset ready.
- `git archive` có global PAX comment; Python `tarfile` xử lý như metadata,
  Kaggle lại materialize `source/pax_global_header` thành regular file 52 bytes.
  Vì vậy local expanded simulation dùng tarfile có thể pass nhưng chưa mô
  phỏng đủ mount Kaggle. Remote file listing phát hiện trước GPU; tải header
  và manifest, kiểm hash/commit rồi tái hiện exact inventory rejection cục bộ.
- Không nới lỏng mọi extra files: sửa versioned archive/bootstrap với exact
  sidecar binding hoặc archive không PAX, rồi chạy lại actual-layout preflight.
  Giữ Dataset v1/bundle03; đây là phát hiện pre-submission, **0 GPU submissions**,
  không phải một model failure. [Biên bản](../experiments/manifests/phase5_guard_remote_mount_v1_diagnostic01.json).
- CLI tải riêng `source/pax_global_header` vào basename `pax_global_header`
  trong lần này; kiểm đường dẫn thực trước audit, không tải lại chỉ vì đoán sai path.
- Local pytest chạy đồng thời dưới shared temp parent gây cleanup symlink warnings;
  lượt tuần tự với fresh explicit basetemp pass sạch 1.011 tests. Không sửa frozen
  test behavior hoặc xóa thư mục rộng để che cảnh báo.

## Cập nhật v1.1 — 2026-09-06

Khi tạo kernel mới, `id` và slug sinh từ `title` cần nhất quán. Lần v1.1 đầu
server cảnh báo rồi tạo handle theo title. Đó không phải inference failure:
dùng handle từ output push cho status/logs/output, không push lại để đổi tên.

Phase 2 còn gặp lỗi fault adapter không delegate `validate_arguments`, khiến
parser dùng generic BaseModel dù unit test execute trực tiếp vẫn pass. Vì vậy
preflight mới gọi tool qua AgentRuntime/parser/Broker và có recovery case.

Runner cũ chỉ ghi results cuối suite nên mất danh sách task hoàn thành khi lỗi
giữa chừng. Runner v1.1 lưu checkpoint mỗi task, từ chối identity/hash mismatch,
và không retry semantic failure. Bundle preflight kiểm tra cả archive/expanded
mount, 8 tool, Dummy đủ 21 task và resume trước upload. GPU kiểm tra bằng phép
tính tensor thực, không chỉ `cuda.is_available()`.

Skill `.agents/skills/experiment-repro/references/kaggle-preflight.md` đã lưu
quy trình; không sửa skill global để tránh áp điều kiện repo lên dự án khác.

Ba attempt đầu là lỗi hạ tầng và đều dừng trước inference:

1. Kaggle tự bung file `tar.gz` của Dataset thay vì mount nguyên archive.
2. Nội dung bung nằm trong một thư mục tên sinh tự động, không ở mount root.
3. Python subprocess không tự có `<repo>/src` trong `PYTHONPATH`.

Wrapper hiện tại xử lý cả archive và expanded mount, tìm đúng một package root,
kiểm tra SHA-256 từng file tracked, chấp nhận `Transformers` khác hoa/thường,
xác minh các file model bắt buộc, rồi truyền `PYTHONPATH` và frozen commit cho
mọi subprocess.

Quy tắc giữ nguyên:

- Chỉ một account cho authoritative run; không gộp quota nhiều account.
- Retry chỉ khi lỗi hạ tầng; không retry semantic failure để lấy điểm đẹp.
- Dataset/kernel đều private, model revision cố định, internet tắt.
- Chạy `make kaggle-bundle-validate` trước mọi lần upload.
## Measured pilot metadata — 2026-09-06

SaveKernel returned HTTP 409 when the kernel title matched the Dataset name.
The standard CLI hid the detailed server message; the API HTTP response body
identified the collision. Use distinct Dataset/kernel slugs and titles. CPU
machine_shape should be omitted/null, not the literal string `None`.
Failed SaveKernel requests are not completed or failed inference attempts.

## Measured pilot completion lessons — 2026-09-06

- Real Gemma 4/Qwen 7B tokenizers/configs and tiny random generation passed on
  a Kaggle CPU kernel before GPU submission. Local Intel macOS PyTorch 2.2.2
  is not a substitute for validating this newer Transformers runtime.
- Offline wheelhouse pins Transformers 5.5.0 and compatible dependencies with
  hashes; provide CPython 3.11/3.12 regex wheels for the images in scope.
  Do not replace Kaggle's Torch/CUDA stack blindly. Both measured runs actually
  reported Torch 2.10.0+cu128, Transformers 5.5.0, tokenizers 0.22.2,
  accelerate 1.10.1 and two Tesla T4 GPUs.
- Both GPU kernels completed on v1 after CPU/bundle preflight. Record this
  separately from the earlier metadata 409 calls, which never ran inference.
- `kernels output --page-size 1000` returned HTTP 400 in this session;
  `--page-size 100` worked. This is observed behavior, not a universal API limit.
- Select only bundle info and run artifacts when downloading. Installing the
  offline dependencies under `/kaggle/working` causes thousands of dependency
  files to appear in exported outputs; CLI pagination can remain slow even
  with filename filtering. Check required checkpoint coverage, not CLI silence.
- Never download over audited files. Retain manifest hashes; regenerate tables
  from saved measurements without spending another GPU attempt for low scores.
# Phase 5 guard preparation — 2026-09-08

- Bundle02 local preflight bắt `validation.__init__` eager-import pool validator
  khi chỉ mang environment validator. Bundle03 bỏ initializer khỏi archive,
  dùng namespace directory; both isolated layouts pass. Không sửa source cũ,
  không mang authoring/pool modules vào GPU để che missing import.
- Kaggle CLI nằm ở `python3 -m kaggle` (2.2.4), không phải `.venv/bin/kaggle`.
  Help/version hoạt động; không cần cài lại chỉ vì thiếu entrypoint trong venv.
- Python.org Python 3.11 cục bộ gặp `CERTIFICATE_VERIFY_FAILED` khi dùng CA mặc
  định với HF. Curl TLS-verified đọc được metadata. Acquisition dùng explicit CA
  bundle hợp lệ từ certifi; **không dùng ssl unverified/curl insecure**.
- Guard snapshot pin cần metadata upstream độc lập: Git blob SHA-1 gồm header
  `blob <size>\0`; LFS weights dùng publisher SHA-256. HF commit label tự khai
  cộng hash tự tính không đủ chứng minh publisher. Không tải model từ branch main.
- Quota đã đọc cho tài khoản pilot `huylmhuhu`: GPU còn 29,49h ngày 2026-09-08.
  Đây là snapshot quota, không reservation và không lý do đổi accounts để bypass.
- Bundle guard mới đang kiểm chứng môi trường venv sạch/offline, both layouts,
  no inherited development imports. Không coi unit tests là GPU readiness.
# CPU mount diagnostic additions — 2026-09-09

- At first kernel creation, keep requested id slug and title-derived slug aligned.
  Agent mount v1 requested agent7b but title omitted7b; Kaggle created
  `react-vn-agent-mount-auth-v1`. Follow the returned handle, preserve requested
  metadata, verify pulled wrapper hash; do not submit again only to rename.
- Pulled model_sources may serialize framework as `Transformers` while requested
  metadata uses `transformers`. Accept only the documented exact enum variant,
  preserving owner/model/variation/version; do not broadly normalize identity.
- Read-only CPU hashing of mounted model avoids local weights/download/copy and
  does not consume GPU quota. A hash diagnostic intentionally exiting1 can yield
  ERROR with a complete receipt; inspect artifacts before calling it infrastructure
  failure. Qwen7Bv1 runtime11files matched HF, README differed; preserve both facts.
  [Diagnostic evidence](agent_mount_v1.md). This does not replace GPU runtime preflight.

## Context stress preflight — 2026-09-10

- Pinned Transformers5.5.0 `GenerationConfig` constructor has70 fields, all
  kwargs defaultsNone; `to_dict()` removes `_commit_hash` and supplies version,
  leaving69 fields. The fresh stress config has55None/13explicit/version.
  This is the submitted config only: `_prepare_generation_config` fills None
  fields from the publisher config, then global defaults. Record the resolved
  policy separately; a fresh object does not remove publisher repetition settings.
  [Hash-bound static check and mutation tests](context_stress_audit_v1.md).
- Generation returns its last token before forwarding that token into KV cache.
  Counts4608/4224 do not establish full cache coverage: inspect4607/4223 first,
  then the separately timed final-token forward at4608/4224. This remains a
  diagnostic, not a change to benchmark decoding.
- Static wheel checks and synthetic artifact audits do **not** replace exact
  packaged CPU rehearsal or native GPU validation. Context CLI stub also does
  not configure native tqdm: carry the separate thread-progress policy rehearsal
  into the new wrapper preflight. No new context GPU submission at this milestone.

## Native policy observation preparation — 2026-09-10

- [Policy observation v1](generation_policy_v1.md) keeps the frozen stress
  backend and records actual resolver/length calls through temporary instance
  hooks, then restores originals in finally. Do not call the resolver twice and
  mistake a separate reconstruction for an observation of generation.
- Transformers adds private special-token tensors before length preparation.
  Copy only the69 known serialized config fields; never deepcopy the whole
  config after private CUDA tensors appear. Unknown fields fail closed.
- The new HF entry keeps policy output outside the23-file old probe. Future
  packaging must include both roots and independently bind loaded publisher
  settings to authenticated metadata. Five self-reported policy files alone are
  not source authentication or actual native compatibility proof.

## Native-library CPU rehearsal — 2026-09-10

- One private/offline CPU kernel using the pinned GPU-capable image can test
  installed Transformers5.5.0/Torch2.10.0+cu128 config functions without CUDA,
  weights or model.generate. [Audited run](../docs/evaluation/phase5_policy_native_cpu_v1_report.md)
  passes4cases; do not generalize this to native GPU/model compatibility.
- CPU metadata pulled by CLI2.2.4 returns machine_shape string `"None"`, not
  JSONnull. Preserve the received metadata and narrowly accept this absent-shape
  representation only alongside explicit GPU/TPU=false. Do not normalize arbitrary
  strings or resubmit a valid kernel to fix an auditor serialization mismatch.
- Kernel COMPLETE alone is not acceptance: verify remote code, native installed
  source hashes, exact raw inventory, failure controls and repeated independent
  audits. Reused synthetic counters must not be reported as model inference.

## HF factory composition failure — 2026-09-11

- Context/policy v1 failed after the agent load, before READY or guard startup.
  Preserve its 59 raw files; BACKEND_FAILURE is not proof of a model-load error.
  The exact native-type validator was given a host ReadyBackend by the entry's
  decorator order. [Failure and correction](context_policy_gpu_v1.md).
- A dispatcher stub and native-library hook harness do not exercise the real HF
  factory composition. Test the composed factory in actual daemon-spawn workers,
  retaining the original failing topology as a control. Native-shaped objects
  bypassing constructors prove readiness/transport only, not model execution.
- Place host ReadyFactory outside single-use stress instrumentation. Assert
  readiness leaves the stress call unused, verify both roles before mutating
  factories, and retain the native exact-type check. Run this gate in both exact
  archive/expanded preflights. New code means a new kernel identity, not a rerun
  overwriting the failed v1 evidence. [v2 contract](../docs/architecture/phase5_context_policy_gpu_v2_contract.md).

## Context OOM after successful readiness — 2026-09-11

- V2's two native READY acknowledgements verify the factory correction; they do
  not verify maximum-context feasibility. Agent raised OutOfMemoryError after
  preparation/policy resolution. Preserve all 69 raw files and the null actual
  generation count. The guard performed readiness only, not stress inference.
- Full 4096-token prefill has different temporary-memory costs from small chat
  calls. Attention labelled `sdpa` does not identify its selected CUDA kernel.
  Global endpoint free VRAM also does not imply allocator-cap headroom.
- [Source evidence and hypothesis](../docs/evaluation/phase5_context_policy_v2_oom_review.md)
  suggest native GQA/math fallback on T4, but this run did not record kernel or
  failure-time allocation. Diagnose it explicitly; do not call the inference
  conclusive, increase caps silently or repeatedly push the same failing run.
- A different attention path may change rounding. The proposed opt-in correction
  needs approval, numerical checks and a new identity; no automatic benchmark
  adoption or shorter-context substitute for the declared boundary test.

## Grouped package false-positive imports — 2026-09-14

- Never choose the first directory of an extracted archive as its project root.
  The v2 builder chose `configs` and created an incomplete nested source tree.
  Compileall cannot detect missing transitive imports or wrong package roots.
- `python -I` disables user paths, not an editable install already installed in
  that interpreter's venv. The v2 import audit actually loaded the development
  repo. Its original receipts are retained but the isolation claim is withdrawn
  in the [correction](../docs/evaluation/phase5_grouped_native_v2_report.md).
- Use a new offline venv and a complete, commit-bound source package; verify
  actual module `__file__` and namespace `__path__`, not just import success.
  Run the selected workload/resume in both archive and generated-expanded layouts.
  [Package v3 contract](../docs/architecture/phase5_grouped_package_v3_contract.md).
- `KAGGLE_CONFIG_DIR` selects a directory, not `kaggle1.json`. Explicitly select
  the intended owner without logging keys; an unrelated default account caused
  both misleading quota evidence and a 403 for the project's private notebook.
  Correct owner `huylmhuhu` can read that notebook. Never cycle accounts for quota.
- CLI model metadata download requires its destination directory to exist.
  A local missing-directory error is not a model-access denial; preserve the
  failed command, create the destination and repeat only this read-only check.
- In the installed CLI, `kernels status` and `logs` parse but do not forward a
  supplied version to the session API. `pull handle/1` returned 403 while an
  unversioned pull succeeded and matched submitted v1 code. Keep submission
  version evidence separate from latest-session observations; do not label a
  latest-session read as independently version-authenticated.
- Installed Dataset metadata CLI writes a response envelope: private visibility
  is `info.isPrivate`, not a root field. Preparation01 for constrained GPU stopped
  before push on that shape; preserve its logs and check the actual saved metadata
  before changing adapters. Corrected preparation02 sent exactly one GPU job.
  See [report](../docs/evaluation/phase5_constrained_gpu_v1_report.md).
