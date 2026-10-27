# Tiếp tục thực nghiệm qua API Kaggle

> **Ưu tiên closure2026-10-02:** Phase5accepted20DoD. Native84 và guard80 đều
> terminal;không resume theo các hướng dẫn lịch sử bên dưới.
> Đọc [handoff](handoff.md) và [closure dossier](../docs/evaluation/phase5_completion_20261002.md).
> Không Phase6/7 hoặc Test run trong scope này.

> Ưu tiên sau independent review 2026-10-02: native epoch public guard đã có
> **84/84 terminal, 72 completed/12 model_error; audit v2 tái lập20/20PASS**.
> Journal local không còn unresolved. Các mốc16/84 và68chưa chạy phía dưới là
> lịch sử, không là lệnh resume hiện hành. Chưa kiểm remote health; phase status
> chưa promote. Đọc [review](../docs/research/phase5_independent_review_20261002.md)
> và [handoff](handoff.md). Không inference mới trong lượt review này.

> Ưu tiên2026-10-02: pair public guard đã authenticated READY và chạy native,
> nhưng đã DỪNG tại16/84 checkpoints (15 completed,1 network/model_error).
> Request agent trả404 REQUEST_UNKNOWN khi reconciliation;68conditions chưa chạy.
> Pair `build/kaggle/phase5_public_guard_pair_20261002_01`; journal vẫn blocked.
> Đọc [handoff](handoff.md) và [partial audit](../docs/evaluation/phase5_public_guard_partial_20261002.md).
> Không dùng các trạng thái waiting/RUNNING lịch sử phía dưới để tự restart.

> Ưu tiên2026-10-01: worker source `e4078d7` đã push GitHub và owner notebooks
> frozen đã QA4/4 tại `build/kaggle/collaborator_pair_frozen_20261001_01`.
> **Chưa có worker mới chạy hoặc endpoint**; đọc [handoff](handoff.md) trước
> các lệnh/trạng thái lịch sử phía dưới. Host runner vẫn là working-treev2.


> Cập nhật ưu tiên 2026-09-29: release04a (agent v8/guard v6) là mốc native
> gần nhất đã lưu, hai epoch dừng uncertain. Chưa health live lại trong lượt sửa.
> Native closure v1 CLI đã nghỉ; runner v2 + package20260930_01 mới chỉ CPU QA.
> Đọc [handoff mới](handoff.md) và [root-fix report](../docs/evaluation/phase5_root_fix_20260929.md)
> trước các lệnh lịch sử bên dưới. Không dùng release03a READY cũ làm health hiện tại.

Cập nhật: 2026-09-29. Hướng dẫn cho chat mới trong cùng workspace. Đọc sau
[current status](current_status.md) và [handoff](handoff.md). Đây là memory
phát triển; không đưa nội dung này vào prompt của model được benchmark.

**Override hiện hành 2026-09-29:** owner yêu cầu restart; package/config mới là
`build/kaggle/structured_pair_release03a_20260929`. Agent v7 và guard v5 đã
RUNNING, authenticated READY và source pull khớp (06:40 UTC). Các đường dẫn
release02a/snapshot v2 bên dưới là lịch sử. Dùng directory mới cho `status`,
`discover` và factory; không đổi identity để resume một run cũ. Host lifecycle
recovery đã CPU-tested, nhưng hai notebook vẫn phục vụ structured v1, chưa có
v3 status/cancel. [Report](../docs/evaluation/phase5_restart_recovery_20260929.md).

## Trạng thái đã xác minh

- Phase1–4 accepted; Phase5 đang làm,4/7 nhóm nghiệm thu, không phải57% toàn đồ án.
- Owner đã xác nhận tắt bốn phiên cũ và cho triển khai hai notebook mới.
  Qwen3-8B làm task agent; Llama3.2-3B-Instruct làm guard. Không fine-tune.
- Hai notebook v1 từng READY và paired smoke đã completed ngày2026-09-27.
  Đây là lần quan sát trước, không khẳng định còn online khi mở chat mới.
- Smoke mới: `23*7+5`,2agent calls +2guard calls, một calculator qua Broker,
  final `166`, guard SAFE/LOW cả hai. Chỉ kiểm tích hợp/định dạng, không fullA6.
- Runner Dev đã hoàn thành pilot01:37/37 checkpoint (21clean+16guard).
  Utility3/21, attack flag5/8, benign flag3/8 chỉ là diagnostic. Adapter Plan
  riêng đã có CPU QA; fullPre/Post/Final/cumulativeA0–A6 còn mở.

## File nào dùng để làm gì

| Đầu mối | Vai trò |
|---|---|
| [Serving contract](../docs/architecture/structured_pair_api_v1.md) | Schema, role, bounds, pinning và giới hạn kỹ thuật |
| [Worker](../src/react_agent/serving/structured_api_v1.py) | Inference GPU, constrained JSON; không chạy tools |
| [HTTP backend](../src/react_agent/llm/structured_http_v1.py) | Identity/schema checks; hiện nhận action/final hoặc guard verdict |
| [Launcher](../scripts/launch_structured_pair_v1.py) | prepare/push/discover/status; không phải launcher bốn model cũ |
| [Preflight](../scripts/preflight_structured_pair_v1.py) | Kiểm exact generated scripts trước upload |
| [Paired smoke](../scripts/run_structured_pair_smoke_v1.py) | Một task cố định; output phải mới, không có resume |
| [Report](../docs/evaluation/structured_pair_api_v1_report.md) | Kết quả, QA, notebooks và giới hạn đã quan sát |
| [Receipt](../experiments/manifests/structured_pair_api_v1.json) | Source/model/session và hashes của evidence đã chọn |
| [Lộ trình](../docs/evaluation/project_status_api_20260927.md) | Phần còn thiếu để hoàn thiện đồ án |
| [Sổ Kaggle](kaggle_resources.md) | Actual handles, versions, ownership và quyền truy cập |

Package hiện hành: `build/kaggle/structured_pair_release03a_20260929/` (agent v7,
guard v5). Các package release02a bên dưới là lịch sử.
Cấu hình kết nối mới nhất: `build/kaggle/structured_pair_endpoint_check_20260928T115147/`.
GET health12:11:14UTC ngày2026-09-28 xác nhận cả hai READY. Read-only health probe
19:14:24UTC ngày2026-09-28 (02:14:24 ngày2026-09-29 theo giờ Việt Nam) trong snapshot
`health_191424_20260929.json` cũng xác nhận cả hai READY. Endpoint/key release02a
đã stale; giữ nguyên config cũ cho evidence. Factory/runner mới nhận directory
snapshot mới; không chạy launcher discover ở snapshot thiếu prepared/discovery files.
Session/source/model v1 giữ nguyên qua restart, không coi session là boot identity.
Probe tiếp theo lúc 19:57:46UTC ngày2026-09-28 chỉ đọc `GET /v1/models` nhưng
agent trả HTTP 530 và guard trả NETWORK_ERROR; lưu tại
`health_195746_20260929_status.json`. Do đó health hiện hành là UNAVAILABLE:
không gửi prompt, không chạy semantic retry, không submit/restart notebook chỉ
vì lỗi truy cập và không dùng snapshot READY cũ làm điều kiện inference.
Release01 và smoke01 là lịch sử, giữ nguyên. V1 đã COMPLETE trước restart
2026-09-28; source/model không đổi, sessions mới, preflight4/4 đạt.
Thông tin endpoint/key ở `pair_endpoints.json`; không in file, chép vào memory
hoặc yêu cầu owner gửi key qua chat. Private key discovery và connection files
mode0600, Git-ignore. `agent_live_metadata.json`/`guard_live_metadata.json` là
metadata không chứa key. Raw smoke: `build/evaluation/structured_pair_smoke01/`.
GitHub source đã freeze: `728821ea761b3994eb40ebba91ab8238e4667f82`.
Report/receipt/memory mới còn local; source commit này không chứa mọi thay đổi
working-tree hoặc tất cả code được hash trong declaration host.

Actual notebook hiện hành: `buiquocviet/react-vn-qwen3-agent-api-v1`,v2;
`huylmhuhu/react-vn-llama3-guard-api-v1`,v2. V1/IDs136136611,136136616 là lịch sử. Mỗi notebook private,
2T4, FP16, không Dataset; model mounts/version trong receipt. Không account cycling.

## Bắt đầu chat mới

1. Đọc `AGENTS.md`, phase status, current status, handoff và runbook này; xem
   `git status --short`. Giữ các thay đổi chưa commit của owner/lượt trước.
2. Nếu chỉ rà tài liệu hoặc viết CPU runner thì chưa cần network/GPU. Kiểm
   file local bằng metadata/hashes, không đọc benchmark Test/private oracle.
3. Trước inference, kiểm health/session. Hai lệnh dưới không sinh văn bản hoặc
   submit notebook; dùng từ repo root. `discover` có thể tạo local config còn
   thiếu, nhưng không đổi notebook remote:

```bash
build/structured_api_venv/bin/python scripts/launch_structured_pair_v1.py status \
  --directory build/kaggle/structured_pair_release03a_20260929
build/structured_api_venv/bin/python scripts/launch_structured_pair_v1.py discover \
  --directory build/kaggle/structured_pair_release03a_20260929
```

`status` là trạng thái kernel, chưa phải inference readiness. `discover` kiểm
GET `/models` với identity trước khi báo READY; nó không tự sửa stale endpoint
đã lưu hoặc khởi động phiên mới. Trước run, HTTP backend còn kiểm profile,
role, alias, fingerprint. Network sandbox có thể cần tool escalation.

Nếu URL hết hạn hoặc identity khác: ghi lỗi hạ tầng, kiểm đúng notebook và
session; không xóa config cũ để bỏ qua mismatch. Khi thật sự cần phiên mới,
đọc skill experiment-repro/Kaggle preflight và kaggle-cli, dùng package/session
mới, exact QA rồi submit một lần theo authorization còn áp dụng. Không push
lại release01 hoặc khởi chạy mặc định bốn model. Không đổi source/model giữa
một run rồi coi là resume cùng identity. Không dừng phiên chỉ để thử lifecycle
trong lúc owner còn dùng; phải có scope kiểm tra cụ thể.

## Đọc evidence cũ, không inference lại

Lệnh sau chỉ kiểm local hashes và tóm tắt result đã lưu:

```bash
.venv/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path
receipt = json.loads(Path('experiments/manifests/structured_pair_api_v1.json').read_text())
for name, expected in receipt['artifact_sha256'].items():
    path = Path(name)
    assert path.is_file(), f'Missing artifact: {name}'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
result = json.loads(Path('build/evaluation/structured_pair_smoke01/result.json').read_text())
print({k: result[k] for k in ('status', 'diagnostic_pass', 'agent_attempts', 'guard_attempts')})
PY
```

Không chạy lại `run_structured_pair_smoke_v1.py` chỉ để nhớ hệ thống đã hoạt
động. Script đó cố định một task và không checkpoint/resume; đổi tên output
không làm task thành bằng chứng độc lập. Giữ HTTP diagnostic cũ và mọi
preflight/source-pull failure. Nếu thiếu raw ở máy mới, ghi rõ chưa kiểm được;
hash không khôi phục raw và không được tái chạy model để thay evidence mất.

## Bước tiếp theo cần triển khai

Pilot Dev đã chạy xong; không rerun lỗi semantic của pilot01. Manifest và
raw ở `build/evaluation/structured_api_dev_v1/`; xem
[báo cáo](../docs/evaluation/structured_api_dev_v1_report.md).

Adapter `StructuredPlanHTTPBackend` gửi inline schema qua server hiện hành.
Diagnostic một task dùng Broker, Plan, guard veto và host rendering theo
[protocol](../docs/evaluation/structured_plan_api_v1_protocol.md). Không dùng
adapter này thay ActionTurn/FinalTurn trong runtime chính. Không tự chạy lại
`diagnostic01` hoặc tạo output khác để lấy đáp án tốt hơn.

Đã nối candidate qua public runtime và native7mức: xem
[report](../docs/evaluation/remote_api_levels_v1_report.md). Tiếp theo khai báo
worker lifecycle mới. Paired Dev run01 đã hoàn tất28/28 và provenance run01
12/12; đọc [paired report](../docs/evaluation/remote_api_paired_dev_v1_report.md)
và [provenance report](../docs/evaluation/remote_api_provenance_v1_report.md).
Không chạy lại hai run hoặc sửa source đã pin. Candidate HTTP/status/cancel có
CPU QA. [Worker v3](../docs/evaluation/request_worker_v3_cpu_report.md) bổ sung
HF stop-event/CUDA synchronization adapter, bounds và terminal-status verifier;
103tests/4exact package cases đạt. Native behavior chưa kiểm trên GPU. Cần nối
host transport/journal/runtime, cached-result recovery và notebook entrypoint/
discovery/lifetime shutdown trước source freeze và submission mới.
`WarmGuardBackend` quản lý tiến trình local; kill tiến trình HTTP client không
chứng minh request GPU từ xa đã dừng. Phải khai báo transport/lifecycle riêng,
không bypass `_run_task` hoặc lấy local worker reaping làm remote cancellation.

Candidate mới nhất cho false-block email là [authorization_anchors_v4 CPU
protocol](../docs/evaluation/authorization_anchors_v4_cpu_protocol.md) và
[report](../docs/evaluation/authorization_anchors_v4_cpu_report.md). Nó chỉ
bind parser v4 trong runtime v13 opt-in cho CPU/A2 controls; A6 native readiness
false vì value-origin v3 chưa được nâng cùng phiên. Không chạy API inference cho
candidate này, không sửa notebook, và không dùng nó để tăng acceptance.

Encoded FINAL historical run có [freeze audit v3](../docs/evaluation/encoded_final_api_v1_freeze_audit_v3_report.md):
94 artifact, 32 journal, 336 source path khớp và saved evaluator tái lập đúng.
Hardened v2 runner/evaluator là candidate source-only, không tạo request mới.

## Ràng buộc so sánh và những hướng cũ đã hết hiệu lực

- RQ1 cần3task backbones, có thể chạy tuần tự; guard không tự tính là backbone
  trả lời. RQ2 giữ một agent/decoding cố định quaA0–A6 và cùng guard cho các mức
  có guard; A0 không thêm guard. Test vẫn khóa; không fine-tune thí nghiệm chính.
- Batch-only preference ngày2026-09-25 đã được owner thay bằng hướng API.
  Không tự quay lại upload benchmark/runtime mỗi lần sửa local experiment.
- UI8765, `build/kaggle/multi_model_gpu_endpoints.json` và launcher bốn model
  cũ không quản lý cặp structured này. Lệnh `--stop` cũ không dừng đúng cặp mới.
- Pipeline API không chứng minh đã sửa graceful-exit lỗi cũ. READY/schema
  pass không phải quality/ASR/utility evidence, không thay20DoD Phase5.
- Không commit mỗi ghi chú; gom phần việc hoàn chỉnh hoặc source freeze thực
  sự cần thiết. Không sửa nguồn đã frozen để đổi kết quả lịch sử.

## Kết thúc mỗi phiên

Cập nhật ngắn `current_status.md` và bốn mục của `handoff.md`: đang làm,
bước tiếp, evidence, giới hạn/access. Ghi run ID/path, manifest/source,
task/call counts, trạng thái terminal hay đang chạy và lệnh resume thực sự
có hỗ trợ. Submission/terminal audit mới thì cập nhật sổ Kaggle. Chạy
`make knowledge-check`; không suy checks liên kết là nghiệm thu khoa học.
Raw/config trong `build/` và `results/` không có trên GitHub; xem
[quy tắc lưu trữ](storage_and_obsidian.md) trước bàn giao sang máy khác.

QA ngày2026-09-27: lệnh đọc evidence ở trên đã chạy,11hash khớp, result
completed/diagnostic_pass=true/2agent+2guard attempts. Navigation/checks và
6memory tests đạt; không chạy các lệnh network status/discover trong lượt này.

## Journal và runtime hiện hành

`StructuredSessionFactory` dựng TLS/HTTP trong guard process và pin config/
identity. `RemoteAPIRuntime.run_instrumented` dùng public API kế thừa; giữ Broker
và security gates. Host process deadline/reaping không phải remote cancellation.
Dùng journal chung `build/evaluation/structured_api_sessions_v1`: started-only/
uncertain chặn request mới, kể cả task khác. GET/models không reset ledger.
Không đổi root hay xóa bản ghi để tiếp tục; worker cũ chưa có request-status.

`run_remote_api_levels_v1.py` chỉ nhận output mới, không có resume. Diagnostic01
đã hoàn tất và audit; không chạy lại. Source dùng cho run này phải giữ nguyên;
đổi code cần candidate/version/deviation mới, không sửa identity của evidence cũ.
