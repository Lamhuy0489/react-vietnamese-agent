# Sổ tra cứu Kaggle của đồ án

Cập nhật mục lục 2026-10-02; mỗi mục ghi ngày quan sát remote riêng. Biên bản sau source
freeze được gộp với host release audit/report trong một commit hoàn chỉnh.
Đây là **memory phát
triển cho nhóm**, không đưa vào prompt benchmark. Trạng thái dưới đây là mốc
bằng chứng lịch sử, không phải kiểm tra trực tuyến lại mọi URL hôm nay.

Các URL code/Dataset/model có receipts đối chiếu trong `experiments/manifests/`.
Chưa khẳng định mọi URL vẫn mở được với tài khoản khác.

## Bạn mới tham gia bắt đầu ở đâu?

1. Đọc [trạng thái hiện tại](current_status.md) và [bàn giao](handoff.md).
2. Source chính thức: [GitHub main](https://github.com/Lamhuy0489/react-vietnamese-agent).
3. Kaggle là máy chạy inference. Tài khoản sở hữu ghi theo từng tài nguyên bên dưới; cặp hiện tại là
   `lamhuy8904` và `meanalways` theo deployment 02/10; cặp `buiquocviet`/`huylmhuhu` là lịch sử.
4. Notebook/Dataset được giữ private. Quyền GitHub không tự cấp quyền Kaggle:
   nếu bạn Minh dùng tài khoản Kaggle riêng thì chủ tài nguyên cần cấp quyền
   cộng tác phù hợp. Không chép API key/token/mật khẩu vào Git hoặc trang này,
   không chuyển public chỉ để mở được link. 403/404 có thể là thiếu quyền.

## Mốc hiện hành — đọc mục này trước

**2026-10-25 — vLLM serve v1, Qwen3-8B, đã chạy thật:**
[lamhuy8904/react-vn-vllm-serve-v1](https://www.kaggle.com/code/lamhuy8904/react-vn-vllm-serve-v1)
(private, T4×2, Internet, push qua API bằng `scripts/launch_vllm_serve_v1.py`).
- v1 ERROR: vLLM 0.32.0 kéo torch 2.13+cu130, lệch torchaudio cu128 của Kaggle. Sửa ở v2
  bằng cách gỡ torchaudio.
- v2: READY lúc 23:37 (+07), boot `1fafef98e152`, served
  `Qwen/Qwen3-8B@b968826d9c46dd6066d109eabc6255188de91218`. URL tunnel là tạm, không ghi.
  Tự tắt sau 30 phút idle.
- Dataset: không có. Source: working tree trên nhánh hiện tại (commit cùng mục này).
- Quota 2026-10-25 (refresh 31/10): lamhuy8904 20,5 h, huylmhuhu 24,9 h, meanalways 23,3 h,
  buiquocviet 23,2 h. Cả 4 tài khoản cũng chạy notebook `astar-*` của dự án khác.
  Mỗi notebook chỉ serve một model; chạy song song thì dùng 2 tài khoản, ví dụ
  meanalways cho model thứ hai hoặc guard. Model gated cần secret `HF_TOKEN` gắn qua UI.


### 2026-10-02 — Guard Dev terminal audit và Phase5 closure

Đã dùng lại agent [lamhuy8904 v1](https://www.kaggle.com/code/lamhuy8904/react-vn-qwen3-agent-api-v3-candidate)
chỉ đểGEThealth và guard [meanalways v3](https://www.kaggle.com/code/meanalways/react-vn-llama3-guard-api-v3-candidate)
để chạy80Devinputs;không submission/Dataset mới. Worker sources e4078d7/77bc456;
Dataset URL/version:none. Existing private access remains owner-scoped.
Same-boot READY xác minh live tại admission;80unique guard requests terminal200,
TP21/FN19/FP5/TN35. HaiGET-only interruptions được ghi riêng;không retry kết quả.
Host baseline419938b;diagnostic working-tree source636files đã snapshot/hashpin.
[Report](../docs/evaluation/phase5_guard_quality_v1_report.md),
[terminal receipt](../experiments/manifests/phase5_guard_quality_20261002.json),
[Phase5completion](../experiments/manifests/phase5_completion_20261002.json).
Không cam kết endpoint còn READY sau lượt chạy;không credentials trong mục này.

[Cách kiểm trạng thái phiên và tiếp tục thực nghiệm](api_experiment_runbook.md).
Mốc mới nhất: local terminal audit ngày2026-10-02, không live-check Kaggle.

### 2026-10-02 — Audit lại closure cuối từ artifact đã lưu

| Actual notebook của saved epoch | Version | Source worker |
|---|---:|---|
| [lamhuy8904/react-vn-qwen3-agent-api-v3-candidate](https://www.kaggle.com/code/lamhuy8904/react-vn-qwen3-agent-api-v3-candidate) | 1 | e4078d7 |
| [meanalways/react-vn-llama3-guard-api-v3-candidate](https://www.kaggle.com/code/meanalways/react-vn-llama3-guard-api-v3-candidate) | 3 | 77bc456 |

Dataset URL/version: không có cho pair này; guard dùng public pinned HF snapshot,
agent dùng model mount. Đây là notebooks private và access vẫn theo owner;
không suy URL hoặc endpoint hiện truy cập được từ local audit.
Host release419938b4c2bc9842a92b2d797126d69ae727c953;84terminal,
72completed/12model_error;CPUcontrols pass;audit20DoD PASS trong phạm vi smoke.
Không phase promotion, submission, model call hoặc remote-status check mới.
[Review/report](../docs/research/phase5_independent_review_20261002.md),
[receipt](../experiments/manifests/phase5_independent_review_20261002.json),
[release](../experiments/manifests/phase5_release_20261002.json).
Giữ guardv1/v2 ERROR và mọi notebook/epoch bên dưới làm lịch sử.

### 2026-09-29 — Release04a closure deployment and recovery audit

| Actual notebook | Version | Trạng thái kiểm read-only trước recovery |
|---|---:|---|
| [buiquocviet/react-vn-qwen3-agent-api-v1](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1) | 8 | RUNNING; authenticated READY `qwen3-8b` |
| [huylmhuhu/react-vn-llama3-guard-api-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1) | 6 | RUNNING; authenticated READY `llama-3.2-3b-instruct` |

Status/discovery được chạy ngay trước native closure recovery; không chứa
prompt/response benchmark. Package local là
`build/kaggle/structured_pair_release04a_20260929`, preflight 4/4, source
commit `728821ea761b3994eb40ebba91ab8238e4667f82`, Dataset URL/version: không
có. Closure epoch đầu và recovery epoch đều dừng fail-closed tại C4/A0 do
request delivery-uncertain; raw journals và combined report giữ riêng tại
`build/evaluation/`. Xem [deployment report](../docs/evaluation/phase5_native_closure_recovery_report_20260929.md).

### 2026-09-29 — Restart theo owner, source pull và health đã xác thực

| Actual notebook | Version | Trạng thái quan sát lúc 06:40 UTC |
|---|---|---|
| [buiquocviet/react-vn-qwen3-agent-api-v1](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1) | 7 | RUNNING; authenticated READY; source pull khớp |
| [huylmhuhu/react-vn-llama3-guard-api-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1) | 5 | RUNNING; authenticated READY; source pull khớp |

Source `728821ea761b3994eb40ebba91ab8238e4667f82`, private/T4, model mounts
không đổi; Dataset URL/version: không có. Phiên mới có session/discovery mới;
không dùng để bỏ qua request uncertain hoặc resume experiment identity cũ.
Version lấy từ push receipts, không suy v3 sau v2; chưa audit các version xen
giữa. Package `build/kaggle/structured_pair_release03a_20260929`, preflight 4/4,
`restart_verified.json` lưu evidence không secret. Không task inference mới.
[Report](../docs/evaluation/phase5_restart_recovery_20260929.md),
[receipt](../experiments/manifests/phase5_restart_recovery_20260929.json).

### 2026-09-29 — Health probe sau khi notebook v2 vẫn chạy

Không submit hoặc đổi version notebook. Read-only probe lúc 19:14:24 UTC ngày
2026-09-28 (02:14:24 ngày 2026-09-29 theo giờ Việt Nam) dùng
đúng snapshot endpoint private hiện hành và lưu
`build/kaggle/structured_pair_endpoint_check_20260928T115147/health_191424_20260929.json`:
Qwen3-8B agent và Llama3.2-3B guard đều `READY`, identity/model/source/worker
khớp metadata đã pin. Đây chỉ là trạng thái tại thời điểm kiểm; không chứng minh
uptime, boot mới, request cancellation hoặc chất lượng model. Hai API không nhận
benchmark payload trong probe này. Candidate grammar v4 và freeze audit encoded
đều chạy local CPU/read-only, không cần submit Kaggle mới.

Probe follow-up lúc 19:57:46 UTC ngày 2026-09-28 chỉ gọi `GET /v1/models` và
không gửi benchmark payload: agent trả `HTTP_ERROR`/530, guard trả
`NETWORK_ERROR`. Receipt
`build/kaggle/structured_pair_endpoint_check_20260928T115147/health_195746_20260929_status.json`
giữ identity, mã lỗi và số inference bằng 0. Không suy notebook đã dừng, không
retry inference và không đổi version; health này phải trở lại READY cho cả hai
role trước khi mở Dev run mới.

### 2026-09-28 — Endpoint refresh và hai diagnostic bổ sung

Cùng hai notebookv2/owner/URLs ở bảng bên dưới, không submit version mới.
Source worker `728821ea761b3994eb40ebba91ab8238e4667f82`; không Dataset.
Status đúng tài khoản RUNNING; GET12:11:14UTC xác nhận agent/guard READY sau khi
refresh encrypted discovery vào `build/kaggle/structured_pair_endpoint_check_20260928T115147`.
Receipt local: `endpoint_refresh_audit.json`, `health_121114.json` trong snapshot.
Endpoint/key cũ release02a lỗi; giữ nguyên lịch sử. Session/source/model giống
nhau qua endpoint refresh, không có boot attestation; không reset journal.
Private access vẫn cần đúng owner; không credentials trong memory.

[Paired report](../docs/evaluation/remote_api_paired_dev_v1_report.md) và
[receipt](../experiments/manifests/remote_api_paired_dev_v1.json):28/28terminal.
[Provenance report](../docs/evaluation/remote_api_provenance_v1_report.md) và
[receipt](../experiments/manifests/remote_api_provenance_v1.json):12/12terminal.
Tổng155HTTPrequests cho hai diagnostic,0uncertain; không Phase5 acceptance.
Lifecyclev2 mới là CPU candidate, chưa cài vào hai notebook.

### 2026-09-28 — Cùng hai notebookv2, native public runtime A0–A6

Đã probe cùng agent/guard v2 của release02a trước inference; không submit mới.
Actual URLs/owner/version ngay bên dưới, Dataset vẫn không có, source worker
`728821ea761b3994eb40ebba91ab8238e4667f82`. Host source là working-tree325hashes.
7conditions hoàn tất:14agent+10guard,7calculator/final79,5HTTP child processes
GRACEFUL. Không remote GPU shutdown/cancel hoặc chất lượng benchmark.
[Report](../docs/evaluation/remote_api_levels_v1_report.md),
[receipt](../experiments/manifests/remote_api_levels_v1.json).
Raw `build/evaluation/remote_api_levels_v1/diagnostic01`; notebook vẫn giữ chạy,
READY chỉ là quan sát tại probe. Access private/credentials không đổi.

### 2026-09-28 — Restart hai notebook lên v2 theo yêu cầu owner

| Actual notebook | Version | Trạng thái đã quan sát |
|---|---|---|
| [buiquocviet/react-vn-qwen3-agent-api-v1](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1) | 2 | RUNNING, API READY, source pull khớp |
| [huylmhuhu/react-vn-llama3-guard-api-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1) | 2 | RUNNING, API READY, source pull khớp |

V1 đã COMPLETE trước restart. Source vẫn
`728821ea761b3994eb40ebba91ab8238e4667f82`; mounts Qwen8B/1 và Llama3B/1 như v1;
Dataset URL/version: không có. Hai notebook private, cùng tài khoản cũ, T4×2.
Preflight4/4; mỗi notebook push một lần. Raw/package mới:
`build/kaggle/structured_pair_release02a`. [Report](../docs/evaluation/structured_plan_api_v1_report.md),
[receipt](../experiments/manifests/structured_plan_api_v1.json).
Diagnostic1agent+1guard: Plan hợp lệ, guardSAFE/LOW, host chặnS2, outputnull;
không public-field utility hoặc nghiệm thuA6. Keys chỉ local; cần đúng owner
hoặc quyền private. READY không bảo đảm phiên còn online khi đọc lại.

### 2026-09-27 — Hai notebook structured API đã READY, paired smoke đạt

| Actual notebook (requested handle khớp) | Vai trò | Version / ID | Model source/version |
|---|---|---|---|
| [buiquocviet/react-vn-qwen3-agent-api-v1](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1) | Qwen3-8B agent | 1 / 136136611 | qwen-lm/qwen-3/Transformers/8b/1 |
| [huylmhuhu/react-vn-llama3-guard-api-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1) | Llama3.2-3B guard | 1 / 136136616 | metaresearch/llama-3.2/Transformers/3b-instruct/1 |

Source `728821ea761b3994eb40ebba91ab8238e4667f82`, đã push GitHub trước GPU.
Dataset URL/version: không có Dataset trong hai notebook này. Private/T4×2,
FP16; remote metadata/source bytewise khớp. Receipt push xác nhận version1;
pull latest khớp nhưng pull suffix `/1` không trả source, giữ lỗi riêng.
[Report](../docs/evaluation/structured_pair_api_v1_report.md),
[submission/preflight/live metadata/smoke receipt](../experiments/manifests/structured_pair_api_v1.json).
Ngày kiểm2026-09-27: hai API READY, paired synthetic2agent+2guard calls đạt,
final166/calculator qua Broker; guardSAFE/LOW. Không terminal lifecycle audit,
không benchmark quality. Hai server giữ chạy; owner xác nhận đã tắt bốn phiên
cũ. READY không đảm bảo uptime về sau. Private access cần đúng tài khoản/quyền
Kaggle, không suy từ link local. Keys/endpoints/topics không lưu trong memory.
Loaded-file hashes có trong receipt, không publisher attestation. Raw local
`build/kaggle/structured_pair_release01` và `build/evaluation/structured_pair_smoke01`.

### 2026-09-28 — READY audit and structured Dev pilot complete

Read-only `status`/`discover` authenticated the same two private v1 notebooks:

| Actual notebook | Role | Version / ID | Dated status |
|---|---|---|---|
| [buiquocviet/react-vn-qwen3-agent-api-v1](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1) | Qwen3-8B agent | 1 / 136136611 | `RUNNING`, `READY` at audit |
| [huylmhuhu/react-vn-llama3-guard-api-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1) | Llama3.2-3B guard | 1 / 136136616 | `RUNNING`, `READY` at audit |

Remote serving source remains `728821ea761b3994eb40ebba91ab8238e4667f82`; no
Dataset is mounted. The host-only Dev pilot then completed 37/37 checkpoints
(21 clean tasks and 16 paired guard controls) through these workers. [Pilot
report](../docs/evaluation/structured_api_dev_v1_report.md), [manifest and raw
receipt directory](../build/evaluation/structured_api_dev_v1/). This is Dev
diagnostic evidence, not Test or Phase 5 acceptance. Session/API credentials
remain local and are not recorded here.
Post-pilot read-only status check: both kernels remained `RUNNING`; no session
was stopped by the runner.

### 2026-09-27 — Bốn API do owner dựng, live diagnostic riêng

Owner xác nhận Llama3B là guard candidate, ba model còn lại là task agents.
[Report và nguồn bằng chứng](../docs/evaluation/kaggle_http_diagnostic_20260927.md),
[receipt](../experiments/manifests/kaggle_http_diagnostic_v1.json).
Notebook handles dưới đây từ owner/local launcher; GET API xác nhận alias/mount,
không xác thực độc lập notebook version/source hoặc quyền truy cập notebook.

| Notebook khai báo | Vai trò | Model mount/version server báo |
|---|---|---|
| [buiquocviet/qwen3-8b-gpu-api](https://www.kaggle.com/code/buiquocviet/qwen3-8b-gpu-api) | Agent candidate | qwen-lm/qwen-3/transformers/8b/1 |
| [lamhuy8904/gemma4-e4b-gpu-api](https://www.kaggle.com/code/lamhuy8904/gemma4-e4b-gpu-api) | Agent candidate | google/gemma-4/transformers/gemma-4-e4b-it/1 |
| [huylmhuhu/gemma3-gpu-api](https://www.kaggle.com/code/huylmhuhu/gemma3-gpu-api) | Guard candidate Llama3B; slug gemma3 là tên cũ | metaresearch/llama-3.2/transformers/3b-instruct/1 |
| [meanalways/deepseek-r1-llama8b-gpu-api](https://www.kaggle.com/code/meanalways/deepseek-r1-llama8b-gpu-api) | Agent candidate | deepseek-ai/deepseek-r1/transformers/deepseek-r1-distill-llama-8b/2 |

Ngày kiểm2026-09-27: ban đầu4GET200; runner sau đó Gemma GETtimeout nên uptime
chưa ổn định. Qwen tool action đạt/final sai schema,DeepSeeknonJSON,Llama2guard
controls đạt. Không notebook terminal audit/new submission. Kernel version và
remote source commit: **chưa xác minh**; không dùng Git base local làm nguồn
remote. Dataset riêng: launcher khai báo không có; mount Model versions như
trên là self-report, chưa weight-hash attestation. Không đưa endpoint/key hoặc
ntfy topic vào memory. Resources không chuyển public; owner access không suy
ra quyền người khác. Batch-only preference bên dưới là lịch sử đã được cập nhật.

### Tham khảo mới 2026-09-25 — chưa triển khai cho dự án

Owner chọn batch Kaggle, không public endpoint. [Đánh giá và kế hoạch](../docs/evaluation/phase5_field_model_bridge_v1_report.md).
[kaggle-tpu-lab](https://github.com/ARahim3/kaggle-tpu-lab) là repo bên ngoài;
[Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) là model card đã đọc,
chưa pin immutable revision/download. Hai Dataset theo notebook user gửi:
[weights rahim3/qwen3-8-27b-bf16](https://www.kaggle.com/datasets/rahim3/qwen3-8-27b-bf16),
[cache rahim3/qwen38-tpu-env-v5e8](https://www.kaggle.com/datasets/rahim3/qwen38-tpu-env-v5e8).
Dataset versions/access/cache hashes chưa xác minh; URL từ mô tả không phải
receipt mount thành công. Không có source commit/notebook version/submission
của đồ án dùng chúng. Không thay thế các notebook lịch sử dưới đây. Không lưu key.

**Dev32 v2 COMPLETE/audit; không resubmit.** Actual
[notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
version1/ID135499833, source commit
`ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e`, private/offline/T4;
[Guard Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version1/private. [Terminal report](../docs/evaluation/phase5_clause_dev_gpu_v2_terminal_report.md),
[receipt](../experiments/manifests/phase5_clause_dev_v2_gpu_terminal01.json),
[release02](../experiments/manifests/phase5_clause_dev_package_v2_release02.json),
[submission](../experiments/manifests/phase5_clause_dev_v2_gpu_submission01.json).
Before/after remote identity khớp; 32/32 tasks, 8/8 shards, 2.073 raw và
2 remote hashes, 222 committed source pins; hai audits giống byte-for-byte.
Raw `results/phase5_clause_dev_v2_gpu_monitor01/raw`, audit01/02 và report01/02
dưới `results/phase5_clause_dev_v2_gpu_*`. Chưa Dev-oracle quality/utility,
formal Phase5 chưa nghiệm thu; private link cần quyền Kaggle riêng, GitHub
access không đủ. Không đưa credential vào repo, không chuyển public.

Mốc trước — v2 RUNNING lúc submit (không phải trạng thái hiện hành):

**Dev32 v2 RUNNING lúc 09:55:43 UTC 2026-09-23; chỉ monitor read-only.**
Actual=requested [notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
version 1/ID 135499833, source commit
`ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e` đã push GitHub main.
Private/offline/T4/timeout 14400s; fixed 32 public Dev A2/A6,
model Qwen2.5-7B mount. [Guard Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version 1/private/ready đã kiểm tra ngày 2026-09-23. Remote source/settings/
version khớp [submission receipt](../experiments/manifests/phase5_clause_dev_v2_gpu_submission01.json)
và [release02](../experiments/manifests/phase5_clause_dev_package_v2_release02.json).
[Report](../docs/evaluation/phase5_clause_dev_package_v2_report.md); raw push
`results/phase5_clause_dev_v2_gpu_submission01`, read-only admission
`results/phase5_clause_dev_v2_kaggle_preflight01`. Chưa terminal download,
quality score hoặc acceptance. Link private cần quyền Kaggle; GitHub access
không đủ. Không gửi lại version/job này; release01 bị từ chối trước upload.

Mốc trước — v1 terminal ERROR (không phải job hiện hành):

**Dev32 v1 ERROR trước worker start**,terminal thấy08:39:20UTC2026-09-22.
[Notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1)
version1/ID135340687,source`5a23528`xác thực,Dataset guard15v1/private.
[Failure report](../docs/evaluation/phase5_clause_dev_gpu_v1_failure_report.md).
Raw12files `results/phase5_clause_dev_gpu_monitor01`,hai failure audits;
0/32ca có result,không model-generation receipt. [V2 QA03](../experiments/manifests/phase5_clause_dev_package_v2_qa03.json)
đạt; requested alias `huylmhuhu/react-vn-clause-dev32-v2` **chưa phải actual
remote notebook**. Read-only preflight `results/phase5_clause_dev_v2_kaggle_preflight01`
ngày 2026-09-23: GPU còn 29,73h, Dataset guard15 private/ready/v1.
Committed release01 qua hai CPU layouts nhưng [bị từ chối](../experiments/manifests/phase5_clause_dev_package_v2_release01_rejected.json)
vì host validator nhận nhầm cache launcher v1; chưa có GPU/submission v2.
V1 link giữ làm lịch sử;không submit lại v1 hoặc biến
notebook private thành public. Link private cần quyền Kaggle riêng.

Mốc trước — v1 RUNNING chỉ là quan sát lúc submit:

**Dev32 clause candidate v1 RUNNING**,live2026-09-22 07:10:42UTC,submit một lần.
Actual=requested [huylmhuhu/react-vn-clause-dev32-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1),
version1/ID135340687;source`5a2352834a791b11824a7c0c69e82f2390a03ca0`đãpushmain.
[Guard Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1,private/ready verified;notebookprivate/offline/T4/timeout14400s,modelQwen7Bv1.
32DevA2/A6,8shards tuần tự,không Test. Remote source/settings/version khớp.
[Report](../docs/evaluation/phase5_clause_dev_package_v1_report.md),
[package](../experiments/manifests/phase5_clause_dev_package_release01.json),
[submission](../experiments/manifests/phase5_clause_dev_gpu_submission01.json),
[QA](../experiments/manifests/phase5_clause_dev_package_qa02.json).
Raw`results/phase5_clause_dev_gpu_submission01`;read-onlyadmission
`results/phase5_clause_dev_kaggle_preflight03`. Chưa terminal download/nativequality.
Không resubmit;privateaccess vẫn cần quyềnKaggle riêng,khôngpublic. Nextmonitorv1,
authenticate trước-sau download rồi độc lập audit,không commit status lẻ.

Mốc trước (không phải job pending hiện tại):

**ExitPair GPU v1 COMPLETE/audit**, post-download2026-09-21 07:28:29UTC.
Actual=requested
[huylmhuhu/react-vn-exit-milestones-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-exit-milestones-v1),
v1/ID135130970, source `6d039e255a0a0a91f6e514cfebe889c4b7ae8aed`.
[Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1; private/offline/T4/timeout3600s và source/model/image settings khớp.
[Report](../docs/evaluation/phase5_exit_gpu_v1_report.md),
[terminal](../experiments/manifests/phase5_exit_gpu_terminal01.json),
[audit](../experiments/manifests/phase5_exit_gpu_audit01.json),
[summary](../experiments/manifests/phase5_exit_gpu_summary01.json).
4completed/8validguard,8GRACEFUL/0forced,4VRAM recoveries. Hai audits khớp,
182source/242raw/2remote; không root cause/fix hoặc guard quality claim.
Raw `results/phase5_exit_gpu_monitor01`; không pending, không resubmit notebook.
Private access vẫn cần quyền Kaggle riêng; không chuyển public. Evidence/memory
local, không commit trạng thái lẻ.

Mốc submission lịch sử (không phải trạng thái RUNNING hiện tại):

**ExitPair exit milestones GPU v1 RUNNING**, live check 2026-09-20 16:57:50 UTC.
Actual=requested
[huylmhuhu/react-vn-exit-milestones-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-exit-milestones-v1),
version1/ID135130970, source `6d039e255a0a0a91f6e514cfebe889c4b7ae8aed` đã push main.
[Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1/private/ready đã xác minh; notebook private/offline/T4/timeout3600s,
Qwen2.5-7B revision1 và Docker image giữ nguyên. Remote source/settings/version
khớp package. Đây là mốc RUNNING, chưa terminal/output audit hoặc root cause.
[Report](../docs/evaluation/phase5_exit_pair_package_v1_report.md),
[release package](../experiments/manifests/phase5_exit_pair_package01.json),
[submission](../experiments/manifests/phase5_exit_gpu_submission01.json),
[QA](../experiments/manifests/phase5_exit_pair_package_qa01.json).
Raw admission `results/phase5_exit_kaggle_preflight02`; raw push/remote source
`results/phase5_exit_gpu_submission01`. API trả ref `/code/owner/slug`, host
equality check dừng sau push đã thành công; read-only verification hoàn tất,
không gửi thêm version/job. Không resubmit khi pending. Terminal bước tiếp:
tải vào thư mục mới, xác thực version/source trước-sau rồi hai release audits.
Quyền private Kaggle riêng, không tự cấp theo GitHub. Biên bản sau source freeze
giữ local đến meaningful closeout, không status-only commit.

Mốc trước (câu “không còn pending” dưới đây chỉ tại thời điểm lịch sử):

**Constrained guard GPU v1 COMPLETE/audit**, post-download 2026-09-17 03:43:34 UTC.
Actual=requested
[huylmhuhu/react-vn-constrained-guard-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-constrained-guard-v1),
version 1 / ID 134673914, source `0d4e82f50b65ac8eaf86193f1a8147321626bb68`.
[Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version 1/private/ready; notebook private/offline, T4, timeout 3600s,
Qwen2.5 7B v1 mount authenticated. Remote source hash and version match.
[Report](../docs/evaluation/phase5_constrained_gpu_v1_report.md),
[submission](../experiments/manifests/phase5_constrained_gpu_submission02.json),
[package](../experiments/manifests/phase5_constrained_probe_package01.json).
[Terminal](../experiments/manifests/phase5_constrained_gpu_terminal01.json),
[audit](../experiments/manifests/phase5_constrained_gpu_audit01.json),
[summary](../experiments/manifests/phase5_constrained_gpu_summary01.json).
4 completed tasks/8 valid guard responses; 8 workers reaped/4 recoveries,
nhưng 4 TERMINATE/4 GRACEFUL. Hai audits khớp, không acceptance/quality claim.
Raw `results/phase5_constrained_gpu_submission02`; preparation01 stopped before
push on CLI metadata envelope, no GPU consumed there. Raw terminal tại
`results/phase5_constrained_gpu_monitor02`. Không còn pending job, không submit lại.
Private access is
not granted by GitHub membership. No quality/acceptance claim yet.

Mốc trước:

**Constrained generation CPU v2 COMPLETE/audit**, post-download check
2026-09-16 08:25:13 UTC. Actual=requested
[huylmhuhu/react-vn-constrained-generate-cpu-v2](https://www.kaggle.com/code/huylmhuhu/react-vn-constrained-generate-cpu-v2),
version 1/ID 134579648, source `b4ae0f7ff8ba698cc09bbd10a08ab4fb9156d2aa`.
[Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version 1/private, unchanged; notebook private/offline/CPU/no model mounts.
Hai success + hai negative controls đạt; chỉ tiny random Qwen, không guard quality.
[Report/raw paths](../docs/evaluation/phase5_constrained_generate_cpu_v2_run.md),
[submission](../experiments/manifests/phase5_constrained_generate_cpu_submission02.json),
[terminal](../experiments/manifests/phase5_constrained_generate_cpu_terminal01.json),
[audit](../experiments/manifests/phase5_constrained_generate_cpu_audit01.json).
Không còn job pending ở lịch này; không submit lại. Quyền private không tự cấp
qua GitHub; không khẳng định tài khoản khác mở được link. V1 ERROR giữ bên dưới.

Mốc trước:

**Constrained generation CPU v1 ERROR**, live-check2026-09-16 07:58:28UTC.
Actual=requested [huylmhuhu/react-vn-constrained-generate-cpu-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-constrained-generate-cpu-v1),
v1/ID134578096, source999d658; private/offline/CPU, không model mounts.
[Datasetguard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1 ready; không thay Dataset.4fixed tiny-random-Qwen cases, không pretrained weights
hay quality/production guard latency. Source tải ngược khớp;0completed cases,
success01 lỗi trước processor admission, hook restored. Raw đã tải và giữ nguyên.
[Failure audit](../experiments/manifests/phase5_constrained_generate_cpu_failure01.json),
[typed-policy diagnosis](../experiments/manifests/phase5_constrained_policy_diagnosis01.json).
[Submission](../experiments/manifests/phase5_constrained_generate_cpu_submission01.json),
[preflight](../experiments/manifests/phase5_constrained_generate_cpu_preflight01.json),
[report](../docs/evaluation/phase5_constrained_generate_cpu_v1_run.md).
Rawsubmission: `results/phase5_constrained_generate_submission01`.

Mốc trước:

**Guard language CPU v1 COMPLETE/audit**, xác minh sau download lúc
2026-09-15 18:36:08UTC; actual=requested
[huylmhuhu/react-vn-guard-language-cpu-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-language-cpu-v1),
v1/ID134521565, source2269fef, private/offline/CPU/no external model mount.
[Datasetguard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1/private. [Terminal](../experiments/manifests/phase5_guard_language_cpu_terminal01.json),
[audit](../experiments/manifests/phase5_guard_language_cpu_audit01.json),
[report/summary/QA/raw paths](../docs/evaluation/phase5_guard_language_native_v1_run.md).
Qwentokenizer3069combinations/max36tokensinclEOS;248actualCPUmask checks.
10raw/2remote/86sourcepins; hai local audits khớp. Không model.generate/GPU/Test.
Không còn jobpending ở lịch này, không gửi lại. Quyền private giữ nguyên;
QUEUED/RUNNING bên dưới là lịch sử, không dùng làm trạng thái mới.

**Guard language native-library CPU v1 QUEUED**, kiểm2026-09-15 18:28:13UTC.
Actual=requested [huylmhuhu/react-vn-guard-language-cpu-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-language-cpu-v1),
version1/ID134521565, source `2269fefa979a6027531516560c838a478c331914`,
GitHub evidencecfd1dd9 trước submit. [Submission](../experiments/manifests/phase5_guard_language_cpu_submission01.json),
[report/preflight](../docs/evaluation/phase5_guard_language_native_v1_run.md).
[Datasetguard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1/private/ready. CPU/no accelerator, noInternet/modelmount,3600s; chỉ tokenizer
và synthetic logits, không model.generate. Code tải ngược khớp. Không submit lại.
Private access không tự có từ tài khoản GitHub; không chuyển public. Các mốc dưới
là lịch sử, không ghi đè raw/identity hoặc dùng làm chỉ dẫn retry.

**Bare-JSON candidate v1 ERROR, inference đã recovery-audit đủ**, kiểm
2026-09-15 17:10:52UTC. Actual=requested
[huylmhuhu/react-vn-guard-bare-json-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-bare-json-v1),
version1/ID134511636, source `f7492fae80876891237fcd37084e79ed5af60a2e`.
[Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version1/private; offline T4×2/14400s. Source tải ngược khớp submission.
[Terminal identity](../experiments/manifests/phase5_guard_bare_json_terminal01.json),
[audit](../experiments/manifests/phase5_guard_bare_json_recovered_audit01.json),
[report, summary và raw paths](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md).
4model_error,2/6valid/4fenced guard responses; auditCLI lỗi sau khi đã chạy4ca.
Hai local audits giống nhau; không mới inference. **Không submit gói v2 đã chuẩn bị**;
requested alias `huylmhuhu/react-vn-guard-bare-json-v2` chỉ là local artifact,
không có actual notebook/version đã xác minh. Quyền private giữ nguyên; không
khẳng định người cùngGitHub mở đượcKaggle. Các mục dưới là lịch sử.

**Observer native v2 v1 COMPLETE/audit**, kiểm2026-09-15 11:52:53UTC;
ID134481763. [Notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-observer-native-v2),
[report và đường dẫn raw](../docs/evaluation/phase5_observer_native_v2_run.md),
[submission](../experiments/manifests/phase5_observer_native_v2_submission01.json),
[terminal/version/source receipt](../experiments/manifests/phase5_observer_native_v2_terminal01.json),
[releaseaudit](../experiments/manifests/phase5_observer_native_v2_audit01.json),
[summary](../experiments/manifests/phase5_observer_native_v2_summary01.json).
Requested=actual `huylmhuhu/react-vn-observer-native-v2`, source`c0930bf`,v1.
[Datasetguard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1ready, private; GitHubcf871a3pushed trước gửi.4tasksCALC/DOC×A2/A6,T4x2/offline.
Mã tải ngược khớp trước/sau download;159source/158raw/2remote verified.
4model_error;2valid/4fenced guardresponses,8reaped/4recovered nhưng3forcedshutdown.
Raw `results/phase5_observer_native_v2_terminal02`, hai reports01/02 đã đóng;
chi tiết timing/receipts trong report. Không gửi lại. Quyền truy cập private giữ nguyên.

### Bare-JSON candidate preflight

Source `f7492fae80876891237fcd37084e79ed5af60a2e`; [CPU preflight report](../docs/evaluation/phase5_guard_bare_json_preflight_v1.md)
and [manifest](../experiments/manifests/phase5_guard_bare_json_package_v1_preflight01.json).
Requested notebook `huylmhuhu/react-vn-guard-bare-json-v1`, submitted once
private/offline T4×2/14.400s, same guard15 Dataset v1 and Qwen mounts. Access check
2026-09-15: GPU22.80h remaining, Dataset ready/current v1. CPU package has no
model loads/GPU/Test access; candidate valid=4/4, injected trailing/fenced=0/4
as expected plumbing controls. Submission v1/ID134511636 was RUNNING at receipt;
[receipt](../experiments/manifests/phase5_guard_bare_json_submission01.json).
Preserve candidate failure identities and do not submit another version.

Lịch112ca trước đó:

**Cả8notebooks đã terminal/audit,112/112ca; không còn jobpending.**
[Báo cáo tổng](../docs/evaluation/phase5_grouped_v3_complete_report.md).
ROWLIST R3 đã COMPLETE lúc2026-09-15 05:53:41UTC, v1/ID134443063;
[terminal/version/hashes](../experiments/manifests/phase5_grouped_v3_s7_terminal01.json),
[audit](../experiments/manifests/phase5_grouped_v3_s7_audit01.json).
Actual notebook/Dataset/source vẫn như dưới;614raw/2remote hashes khớp.
Nguồn `0d86536`, Datasetguard15v1, GitHubevidence875399d trước submit giữ nguyên.
Không dùng các câuRUNNINGlịch sử dưới đây để submit/tải lại.

### Lịch sử admission trước terminal

**Shard7 ROWLIST R3 v1 RUNNING**, kiểm2026-09-15 05:06:57UTC:
[notebook thật](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-rowlist-r3),
kernel ID134443063; [submission03](../experiments/manifests/phase5_grouped_v3_s7_submission03.json),
[admission report](../docs/evaluation/phase5_grouped_v3_s7_admission_report.md).
Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub evidence875399d trước
push; [Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1private/ready, modelv1, offlineT4x2/14.400s/image pins giữ nguyên. Quota trước
attempt02/03 snapshot23,83h. Source tải ngược khớp. R3=admissionattempt3,
không phải securitylevelA3; vẫn đủ14taskA0–A6 của shard7. Không submit lại.
Giữ hai attempt cũ: hết2GPUslots rồiHTTP409; chúng không có confirmed run/version.
Tên mới chỉ thay id/title để phục hồi admission, chưa có terminal result.

### Shards5/6 đã terminal audit

**Grouped v3 shards5/6 v1 COMPLETE/audit**, kiểm2026-09-15 04:51UTC:

| Notebook thật | Version / ID | Bằng chứng |
|---|---|---|
| [shard-5 QUERYLEAK](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-5) | v1 / 134393202 | [submission](../experiments/manifests/phase5_grouped_v3_s5_submission01.json) |
| [shard-6 QUOTED](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-6) | v1 / 134393213 | [submission](../experiments/manifests/phase5_grouped_v3_s6_submission01.json) |

[Report và raw paths](../docs/evaluation/phase5_grouped_v3_batch56_report.md).
Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub evidence `80a8bae` trước
push; [Dataset guard15](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
private/ready/v1; quota25,34h trước gửi. Offline T4x2/model v1/14.400s/image pins
không đổi. Mã tải ngược khớp. Requested `...-s5`/`...-s6` khác actual handles.
Terminal/audit:502+662raw/4remote hashes khớp;scan1168files/0credentials.
[Terminal5](../experiments/manifests/phase5_grouped_v3_s5_terminal01.json),
[terminal6](../experiments/manifests/phase5_grouped_v3_s6_terminal01.json); report
có audits/summaries/timing. Tổng98/112audited, không phải semantic success.
Không submit lại5/6. Shard7 hai lượt đầu lỗi: hết2GPUslots rồiHTTP409;
[admission report](../docs/evaluation/phase5_grouped_v3_s7_admission_report.md).
Tên launcher03 `huylmhuhu/react-vn-grouped-dev-v3-rowlist-r3` đã v1RUNNING
theo mục đầu trang; giữ nguyên danh tính hai attempt lỗi trước.

### Grouped v3 shards3/4 — terminal đã kiểm

**Grouped v3 shards 3/4 v1 COMPLETE/audit**, kiểm 2026-09-14 20:02 UTC:

| Notebook thật | Version / ID | Bằng chứng |
|---|---|---|
| [shard-3 ENCODED](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-3) | v1 / 134383821 | [submission/status/source hash](../experiments/manifests/phase5_grouped_v3_s3_submission01.json) |
| [shard-4 LINKPAGE](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-4) | v1 / 134383829 | [submission/status/source hash](../experiments/manifests/phase5_grouped_v3_s4_submission01.json) |

[Report và raw paths](../docs/evaluation/phase5_grouped_v3_batch34_report.md).
Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub evidence `7078593` trước
push. Cùng [Dataset guard15 v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
đã live ready/v1; private/offline T4x2, model v1, timeout 14.400s; quota snapshot
26,79h trước submit. Mã tải lại khớp bản khóa; live current_version=1 đúng IDs.
Requested aliases `...-s3`/`...-s4` không phải handle thật.
[Terminal3](../experiments/manifests/phase5_grouped_v3_s3_terminal01.json),
[terminal4](../experiments/manifests/phase5_grouped_v3_s4_terminal01.json) có status/
version/hash/scan; report liên kết audit và summaries. 380+534 raw/4 remote hashes
khớp, scan918files/0credentials. Shard3 0tools; shard4 10 model_error do guard JSON.
Tổng70/112 audited, chưa Phase5 acceptance. API last_run_time bất thường không
dùng cho thời gian chạy; giữ nguyên để đối chiếu. Shards5/6 RUNNING ở đầu trang.
Shards0–2 COMPLETE/audit ở dưới; không submit trùng. Quyền GitHub không cấp quyền
Kaggle private; không đổi public hoặc lưu credentials để chia sẻ.

### Mốc trước — document runtime và security runtime

Ngày 2026-09-14 đã gửi **version 1** notebook private mới
[react-vn-document-runtime-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-document-runtime-v1).
Source `54aa3ec`, GitHub evidence `8836e9c` đã push trước submit; T4/7200s/offline.
Dataset [react-vn-guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1 đã kiểm live private/ready. [Submission receipt](../experiments/manifests/phase5_document_gpu_v1_submission01.json),
[report](../docs/evaluation/phase5_document_diagnostic_v1_report.md) và
[memory](document_diagnostic_v1.md). **Terminal COMPLETE, audit đạt** ngày 2026-09-14:
[GPU receipt](../experiments/manifests/phase5_document_gpu_v1_audit01.json),
[terminal summary](../experiments/manifests/phase5_document_gpu_v1_terminal01.json).
261raw/2remote hashes khớp; 7 reads, A0/A1 completed, A2–A6 model_error do guard
INVALID_OUTPUT rồi pair retirement. 8GRACEFUL/4TERMINATE, 7recovered; chưa quality/
Phase5 acceptance. Không submit trùng. Quyền GitHub không tự cấp quyền notebook.

Chuẩn bị local mới nhất: [shutdown package v2](shutdown_package_v2.md) đã đạt
CPU/exact mounts ngày 2026-09-14, **chưa submit**. Tên v2 trong metadata là tên
dự kiến, không có notebook URL/version mới để thay mốc native v1 bên dưới.

| Tài nguyên | Link | Phiên bản/bằng chứng |
|---|---|---|
| Notebook runtime A0–A6 | [react-vn-security-runtime-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-security-runtime-v1) | v1 COMPLETE; [GPU report](../docs/evaluation/phase5_security_runtime_gpu_v1_report.md), [receipt](../experiments/manifests/phase5_security_runtime_gpu_v1_audit01.json) |
| Dataset dùng chung Phase 5 | [react-vn-guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1) | v1 private/ready đã kiểm trước run; source bundle, guard snapshot và offline wheels; [preflight](../experiments/manifests/phase5_security_runtime_v1_preflight03.json) |
| Model mount agent hiện hành | [Qwen2.5 7B Instruct / Transformers / v1](https://www.kaggle.com/models/qwen-lm/qwen2.5/transformers/7b-instruct/1) | Model mount, **không phải Dataset của nhóm**; identity/file hashes nằm trong receipt |

V1 hoàn tất không có nghĩa Phase 5 đã nghiệm thu: 7 terminal/recovery, nhưng
0 tool calls/0 guard calls, 12 worker TERMINATE/-15. Không chạy lại để chọn câu
trả lời đẹp hơn. Source inference `372d685`; raw local
`results/phase5_security_runtime_gpu_v1_output01`; source tải ngược
`results/phase5_security_runtime_gpu_v1_remote02`. Raw generated không track Git;
người clone mới lấy output từ notebook, đối chiếu hash với receipt trước dùng.

## Notebook lịch sử Phase 5

Không chọn notebook chỉ vì tên mới hoặc status COMPLETE. Đọc cột bằng chứng;
model quality, lỗi hạ tầng, native OOM và thử nghiệm transport là các mục khác nhau.
Những notebook này dùng Dataset Phase 5 chung ở trên; kiểm mount/version trong
receipt của đúng lượt, không tự nâng phiên bản.

| Notebook | Vai trò / tài liệu đối chiếu |
|---|---|
| [guard15-probe-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard15-probe-run-v1) | [Guard GPU đầu tiên](guard_gpu_probe_v1.md); không dùng làm chứng nhận chất lượng guard |
| [guard-cancel-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-cancel-run-v1) | [Cancellation và recovery](guard_cancellation_v1.md) |
| [pair-gpu-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-gpu-v1) | [Agent/guard cùng GPU](pair_gpu_v1.md) |
| [pair-cancel-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-cancel-v1) | [Pair cancellation](pair_cancellation_v1.md) |
| [pair-ipc-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-ipc-v1) | [IPC diagnostic](pair_ipc_v1.md) |
| [pair-progress-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-progress-v1) | [Progress-lock diagnostic](pair_progress_v1.md) |
| [policy-native-compat-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-policy-native-compat-v1) | [Native-library CPU compatibility](policy_native_compat_v1.md), không phải GPU benchmark |
| [context-policy-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-context-policy-v1) | [Lỗi factory topology lịch sử](context_policy_gpu_v1.md) |
| [context-policy-v2](https://www.kaggle.com/code/huylmhuhu/react-vn-context-policy-v2) | [OOM sau readiness](../docs/evaluation/phase5_context_policy_v2_oom_review.md) |
| [sdpa-tensor-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-sdpa-tensor-v1) | [SDPA tensor diagnostic](sdpa_tensor_v1.md) |
| [efficient-stress-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-efficient-stress-v1) | [Efficient stress](efficient_stress_v1.md) |
| [ordinary-pair-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-ordinary-pair-v1) | [Lượt lỗi giữ nguyên](../experiments/manifests/phase5_ordinary_pair_gpu_v1_error01.json) |
| [ordinary-pair-t4x2-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-ordinary-pair-t4x2-v1) | [A/B/A native transport evidence](ordinary_pair_gpu_v1.md) |

## Terminal audit ngày 2026-09-14

### Grouped Dev native v3 — shards 1/2 COMPLETE/audit

Kiểm 2026-09-14 18:41 UTC (2026-09-15 tại Việt Nam):

| Notebook thật | Version / ID | Trạng thái / bằng chứng |
|---|---|---|
| [shard-1 SOURCEBINDING](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-1) | v1 / 134350547 | COMPLETE; [submission](../experiments/manifests/phase5_grouped_v3_s1_submission01.json), [audit](../experiments/manifests/phase5_grouped_v3_s1_audit01.json) |
| [shard-2 DATABASE](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-2) | v1 / 134350561 | COMPLETE; [submission](../experiments/manifests/phase5_grouped_v3_s2_submission01.json), [audit](../experiments/manifests/phase5_grouped_v3_s2_audit01.json) |

Source `0d865365b7881144756f804441ca24ed48935f7f`, GitHub push `2a8df8d` trước
submit. Cùng [Dataset guard15 v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1),
private/offline T4x2, Qwen model v1. Requested aliases `...-s1`/`...-s2` không phải
handle thật. 566+678 raw/4 remote hashes verified. [Report/summary/scan links](../docs/evaluation/phase5_grouped_v3_batch12_report.md).
Shard1 10 model_error do guard JSON syntax; shard2 21 valid guard responses.
Không retry; chưa suy ra utility/ASR/FPR. Shards 3/4 đã RUNNING theo mục hiện hành.

### Grouped Dev native v3 — shard 0 COMPLETE/audit

[Notebook thực tế](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-0)
**v1, COMPLETE**, kiểm ngày 2026-09-14 lúc 15:02:53 UTC; kernel ID `134340826`.
Alias yêu cầu `huylmhuhu/react-vn-grouped-dev-v3-s0` đã được Kaggle đổi theo title.
Source `0d865365b7881144756f804441ca24ed48935f7f`, push GitHub qua `93dc9a2` trước
submission. Dataset guard15 v1 private và model Qwen v1 như dưới. 14 ca/shard0,
T4x2/offline/private, timeout 14.400s. [Submission receipt](../experiments/manifests/phase5_grouped_v3_s0_submission01.json),
[report](../docs/evaluation/phase5_grouped_package_v3_report.md).
Remote source hash khớp; pull có `/1` trả 403 nhưng pull handle không version
thành công. [Terminal report](../docs/evaluation/phase5_grouped_v3_s0_report.md),
[audit](../experiments/manifests/phase5_grouped_v3_s0_audit01.json),
[summary](../experiments/manifests/phase5_grouped_v3_s0_summary01.json),
[preservation](../experiments/manifests/phase5_grouped_v3_s0_terminal01.json):
380 raw/2 remote hash khớp, 14 completed/recovered, 0 tool/guard requests;
22 graceful/2 terminate, 24 reaped. Không coi đây là utility/guard quality.
Quota sau shard 0 còn 28,23h; Dataset vẫn ready/v1. Chuẩn bị shards 1/2 theo lịch
đã chọn, không retry shard 0. Chưa có URL/version của hai job tiếp theo.

Kiểm tra đúng owner cho grouped package v3:
[live receipt](../experiments/manifests/phase5_grouped_package_v3_live01.json).
`huylmhuhu` còn 29,02/30h GPU, refresh 2026-09-19; Dataset
[guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
**private, ready, v1**; Qwen model instance v1 truy cập được. Source package
`0d86536`; [preflight](../experiments/manifests/phase5_grouped_package_v3_preflight01.json)
đã đạt; [full QA 3.113 pass/1 skip](../experiments/manifests/phase5_grouped_package_v3_cpu01.json)
đã chốt. Shard 0 đã submit như trên; bảy shard khác chưa có URL/version thực tế.
Không suy đoán notebook tồn tại/không tồn tại từ lỗi status của tên dự kiến.

Đính chính: snapshot quota và lỗi permission dưới đây được lấy bằng credential
mặc định, **không xác thực owner `huylmhuhu`**; không dùng chúng làm quota/quyền
của dự án. Chọn explicit owner từ credential project đã kiểm lại status notebook
document v1 thành công: **COMPLETE**. Không cần tài khoản hoặc quyền mới vì lỗi
403 trước đó. Quota đúng owner phải đọc live trước submission tiếp theo.

Nội dung lịch sử giữ lại (không phải gate quyền/quota hiện hành):

CLI dùng credential path của project, không in credential values. Quota live:
GPU used `0.09h`, remaining `29.91h`, total `30.00h`, refresh
`2026-09-19T00:00:00`; TPU remaining `20.00h`. Đây là snapshot tại thời điểm
audit, không phải reservation. Kiểm tra status notebook private
`huylmhuhu/react-vn-document-runtime-v1` trả permission denied; không đổi URL
hoặc suy đoán COMPLETE mới. Native grouped v2 chưa có notebook/Dataset URL hay
version thực tế; compile-only preflight vẫn ghi `native_submission_ready=false`.

## Phase 1/2 và pilot nhiều model

| Thực nghiệm | Notebook | Dataset | Bằng chứng |
|---|---|---|---|
| Phase 1 smoke | [phase-1-real-model-smoke](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-agent-phase-1-real-model-smoke) v4 | [phase1-bundle](https://www.kaggle.com/datasets/huylmhuhu/react-vietnamese-agent-phase1-bundle) v5 | [Receipt](../experiments/manifests/phase1_kaggle_v4.json) |
| Phase 2 v1 cũ | [phase-2-clean-dev-pilot](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-agent-phase-2-clean-dev-pilot) | [phase2-dev-bundle](https://www.kaggle.com/datasets/huylmhuhu/react-vietnamese-agent-phase2-dev-bundle) | [Receipt lịch sử](../experiments/manifests/phase2_kaggle_v2.json); không thay clean_v1.1 |
| Phase 2 clean_v1.1 | [vietnamese-clean-v1-1-dev-pilot](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-clean-v1-1-dev-pilot) v1 | [clean-v11-dev](https://www.kaggle.com/datasets/huylmhuhu/react-vn-clean-v11-dev) v1 | [Receipt](../experiments/manifests/phase2_clean_v11_kaggle_v1.json); dùng **actual_kernel**, không alias tên yêu cầu |
| Gemma 4 measured Dev | [gemma4-measured-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-gemma4-measured-run-v1) v1 | [gemma4-measured-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-gemma4-measured-data-v1) | [Completion](../experiments/manifests/measured_pilot_completion.json), [submission](../experiments/manifests/measured_pilot_submission.json) |
| Qwen 7B measured Dev | [qwen7b-measured-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-qwen7b-measured-run-v1) v1 | [qwen7b-measured-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-qwen7b-measured-data-v1) | [Báo cáo measured Dev](../docs/evaluation/measured_dev_pilot_report.md) |

Llama chưa chạy tại mốc measured pilot vì thiếu quyền Meta; không có notebook
kết quả Llama để dẫn. Các alias/preflight draft không phải lượt được nghiệm thu
không được nâng thành kết quả chỉ vì tìm thấy handle trong source.

## Cách duy trì sổ

Sau mỗi submission thêm URL notebook, version, Dataset/version, source commit,
report/receipt và trạng thái có ngày kiểm. Sau terminal bổ sung raw path và giới
hạn; giữ riêng lỗi và lượt thay thế. Không ghi credentials/private GT/Test payload.
Chạy `make knowledge-check` sau sửa liên kết. URL ngoài repo được lưu từ receipts;
knowledge-check chỉ kiểm link local/cấu trúc, không xác nhận quyền mở trên Kaggle.

[Kaggle lessons](kaggle_lessons.md) · [Runbook](runbook.md) · [Handoff](handoff.md).

## 2026-09-29 — v3 source-only package, not submitted

Local package: `build/kaggle/request_worker_v3_candidate_20260929_03`.
Preflight receipt: `preflight_v3/receipt.json`, 4/4 role/layout passed. Source
identity is working tree/development with nine module hashes; no committed
release claim. No new Dataset or notebook version. Requested candidate slugs
in local metadata are not actual published handles and no remote URLs are
asserted. Existing actual notebooks remain the release04a v8/v6 historical
identities above; live availability was not checked in this repair turn.
See [root-fix report](../docs/evaluation/phase5_root_fix_20260929.md).

### 2026-09-29 — local candidate04, chưa submit

`build/kaggle/request_worker_v3_candidate_20260929_04` đã prepare/preflight
4/4, thêm kiểm từ chối symlink và SHA launcher/probe trong receipt.
Không có notebook URL/version hoặc Dataset URL/version mới; các handle v3
trong metadata chỉ là requested targets. Source commit là `development`,
working-tree hashes trong prepared/receipt; không suy Git base chứa source mới.
[QA receipt](../experiments/manifests/phase5_root_fix_cpu_20260929.json).
Không network/model/GPU/submission trong lượt QA này; live availability chưa
kiểm lại. Credentials không nằm trong receipt.


## 2026-09-30 — candidate v3 mới, chưa triển khai

`build/kaggle/request_worker_v3_candidate_20260930_01`:4/4CPUpackageQA;
source `development` với từng hash trong receipt. Không notebook/Dataset URL
hoặc version mới. Credential directory nhận diện thêm lamhuy8904/meanalways;
không query quota hoặc submit hai tài khoản này để vượt quota đã hết.
CLI ở lượt trước trả buiquocviet38.60hused/0remaining và huylmhuhu38.42hused/
0remaining, refreshAt2026-10-03T00:00:00. Đây không phải current health.
Lệnh status trước bị ngắt, không receipt thành công. Actual notebook identities
release04a v8/v6 giữ nguyên lịch sử; chưa source-pull/nativev3.
[Report](../docs/evaluation/phase5_native_closure_v2_preparation_20260930.md),
[receipt](../experiments/manifests/phase5_native_closure_v2_preparation_20260930.json).


## 2026-10-01 — gói review cho từng chủ tài khoản, chưa upload

Owner làm rõ lamhuy8904/meanalways là hai người bạn, không phải yêu cầu tạo
account mới. Chỉ chuẩn bị local để từng chủ tài khoản xem và tự vận hành trong
phạm vi quota của họ; không dùng credential của họ, không query quota, không
submit/discover hoặc tự luân phiên account. Không đổi default deployment roles.

- Package: `build/kaggle/collaborator_pair_review_20261001_01`.
- Intended owner/role: lamhuy8904/Qwen3-8B agent; meanalways/Llama3.2-3B guard.
- Requested handles chỉ ở metadata: `lamhuy8904/react-vn-qwen3-agent-api-v3-candidate`,
  `meanalways/react-vn-llama3-guard-api-v3-candidate`; **chưa có actual URL/version**.
- Không Dataset URL/version mới; hai model input version1 giữ nguyên.
- Source `development`, chưa Git freeze/push. Mỗi notebook ghi review-only,
  không hướng dẫn chạy trước khi có release frozen. Native/GPU chưa kiểm.
- CPU exact-package preflight4/4; codecell ipynb bằng từng byte với source đã
  preflight; compile2/2; ZIP chỉ gồm notebook, metadata, README. Private discovery
  key0600 giữ local, Git ignored; không đưa vào gói share.
- Chưa có worker API keys/endpoint. Không suy READY từ preflight.

[Receipt và hashes](../experiments/manifests/phase5_collaborator_review_20261001.json).


## 2026-10-01 — source freeze đã push, owner notebooks chưa upload

- GitHub worker commit `e4078d7d5d2fe66a881e53ec5f194e3f9aa66b47`, nhánh
  `codex/phase5-worker-v3-source-freeze-20261001`; main giữ nguyên.
- Package `build/kaggle/collaborator_pair_frozen_20261001_01` preflight4/4;
 71tests passed;2notebooks×9modules đối chiếu Git bytes đạt. Không secret trong ZIP.
- Intended owner/role: lamhuy8904/Qwen3-8B agent, meanalways/Llama3.2-3B guard.
  Requested handles giữ `react-vn-qwen3-agent-api-v3-candidate` và
  `react-vn-llama3-guard-api-v3-candidate`; **chưa actual notebook URL/version**.
- Dataset:none; model inputs Qwen8b/v1 và Llama3b-instruct/v1 giữ nguyên.
- Không account login/quota query/submission/discovery ở lượt freeze. Không API
  keys/endpoint mới. Chủ tài khoản tự vận hành trên quota hợp lệ; không account cycling.
- [Receipt/hash](../experiments/manifests/phase5_owner_notebooks_frozen_20261001.json).
  Private discovery key giữ local0600/ignored, không có trong owner ZIP.

## 2026-10-02 — đã đọc discovery, chưa nhận API

- Package `build/kaggle/collaborator_pair_frozen_20261001_01`, source commit
  `e4078d7d5d2fe66a881e53ec5f194e3f9aa66b47`.
- Discovery qua mạng hoàn tất, exit 0: agent và guard đều `waiting_discovery`.
  Chưa connection files hoặc pair endpoints; chưa thể probe model/boot identity.
- Requested handles vẫn là `lamhuy8904/react-vn-qwen3-agent-api-v3-candidate`
  và `meanalways/react-vn-llama3-guard-api-v3-candidate`;
  actual notebook URL/version chưa biết. Dataset: none; model input versions
  giữ nguyên như gói frozen. Không đăng nhập Kaggle/query quota/submit/inference.
- Không có thông báo kết nối phù hợp không chứng minh notebook đang tắt.
  Pending: owners chạy gói frozen, cung cấp actual URL/version và tín hiệu READY.
- [Receipt](../build/evaluation/phase5_owner_discovery_20261002_01.json).


## 2026-10-02 — direct deployment và model access blocker

Owner đã yêu cầu trực tiếp vận hành hai worker. Actual private notebooks:
- [lamhuy8904 agent](https://www.kaggle.com/code/lamhuy8904/react-vn-qwen3-agent-api-v3-candidate):
  v1/ID136686959, source e4078d7d5d2fe66a881e53ec5f194e3f9aa66b47,
  authenticated READY, last probe lượt kiểm quyền Llama. Connection0600/local.
- [meanalways guard](https://www.kaggle.com/code/meanalways/react-vn-llama3-guard-api-v3-candidate):
  v1/ID136686965 cùng source e4078d7 ERROR; v2 source
  d6cc4fcee37b009751b94a7535b12690e257166c ERROR EXACT_MODEL_MOUNT_MISSING,
  log input_directories=[]; chưa API. Cả hai phiên lỗi giữ nguyên evidence.
- Dataset:none. Model inputs vẫn Qwen8b/v1 và Meta Llama3.2 3b-instruct/v1;
  remote source 3 submissions khớp byte và metadata private/T4 đúng.
- Read-only file access Llama: meanalways403, lamhuy8904 cũng403; public metadata
  vẫn đọc được. Chờ chủ tài khoản giải quyết quyền model. Không GPU retry tiếp.
- [Deployment receipt](../experiments/manifests/phase5_api_deployment_20261002.json),
  [lamhuy Llama check](../build/operations/phase5_pair_20261002/lamhuy_llama_access_20261001T180657Z.json).


## 2026-10-02 — public guard v3 READY, pair authenticated

- [meanalways guard](https://www.kaggle.com/code/meanalways/react-vn-llama3-guard-api-v3-candidate):
  actual version3/ID136686965, source77bc456469ec58fb3543931066f365b15292f5f3,
  private/T4, no Kaggle model input or Dataset. Remote source bytes exact.
  Public HF input unsloth/Llama-3.2-3B-Instruct revision
  006f5dcd1393c3add266de40994ba96225e9689d. Download manifest fingerprint matches
  authenticated live model revision. v1/v2 ERROR retained, not overwritten.
- [lamhuy8904 agent](https://www.kaggle.com/code/lamhuy8904/react-vn-qwen3-agent-api-v3-candidate):
  actual version1/ID136686959, sourcee4078d7d5d2fe66a881e53ec5f194e3f9aa66b47,
  unchanged private/T4, Qwen input qwen-lm/qwen-3/transformers/8b/1, no Dataset.
- Both authenticated READY after local power interruption; keys recovered through
  encrypted discovery, local pair snapshot0600, never recorded in project memory.
- Pair directory:build/kaggle/phase5_public_guard_pair_20261002_01.
  Native Dev epoch:build/evaluation/phase5_native_public_guard_20261002_01,
  declared84conditions before inference. Startup/health is not Phase5 acceptance.
- [Ready receipt](../experiments/manifests/phase5_public_guard_ready_20261002.json),
  [deployment source/QA](../docs/evaluation/phase5_public_guard_deployment_20261002.md).

## 2026-10-02 — native partial audit, worker versions unchanged

Agent lamhuy8904 v1/source e4078d7 and guard meanalways v3/source77bc456 remain
the exact notebook identities linked above; no new submission or Dataset.
Native run stopped16/84:15 normal,1 network/model_error,68never-started.
Read-only authenticated same-agent probe19:10:40UTC returned404 REQUEST_UNKNOWN;
no cached result or terminal proof. Journal remains blocked. This is not a
fresh guard health check or evidence that either notebook has shut down.
[Report](../docs/evaluation/phase5_public_guard_partial_20261002.md) and
[receipt](../experiments/manifests/phase5_public_guard_partial_20261002.json).
