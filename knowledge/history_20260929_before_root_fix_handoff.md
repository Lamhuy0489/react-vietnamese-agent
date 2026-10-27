# Bàn giao phiên làm việc

Cập nhật: 2026-09-29. Phase5 chưa accepted:4/7 nhóm nghiệm thu; Test vẫn khóa.

## Mốc triển khai mới nhất — native closure/recovery

Đã kiểm tra read-only release `build/kaggle/structured_pair_release04a_20260929`:
hai kernel `RUNNING`, discovery xác nhận agent `READY qwen3-8b` và guard
`READY llama-3.2-3b-instruct`. Epoch native closure đầu tiên lưu 21 điều kiện
hoàn tất hợp lệ trong C1–C3; C4/A0 dừng do request thứ ba delivery-uncertain.
Không xóa hoặc semantic-retry journal cũ.

Đã triển khai recovery epoch bằng journal mới, chỉ lập lịch C4–C12. Recovery
cũng dừng ngay tại C4/A0 với một request uncertain thứ ba; không chạy các điều
kiện còn lại. Bằng chứng và evaluator gộp ở
[native closure recovery report](../docs/evaluation/phase5_native_closure_recovery_report_20260929.md),
[protocol](../docs/evaluation/phase5_native_closure_protocol_v1.md), và
`build/evaluation/phase5_native_closure_combined01_20260929.json`.

**Trạng thái:** 21/84 điều kiện hợp lệ trong combined denominator; 63 thiếu;
Test/private ground truth đọc 0; `phase5_accepted=false`. Không được mở lần
retry thứ ba hay thay threshold/prompt/package để vượt delivery blocker.

**Next concrete step:** chỉ tiếp tục khi owner có một recovery decision mới và
đường request-delivery đã được chứng minh ổn định; khi đó dùng journal mới và
giữ nguyên hai epoch này làm lịch sử bất biến.

Audit toàn bộ kế hoạch và triển khai: [Phase 5 direction audit](../docs/evaluation/phase5_direction_audit_20260929.md).
Đường hiện hành đã được thu gọn về một source/representation baseline
cumulative; các candidate v13/v14 và prototype khác chỉ giữ làm historical hoặc
prospective evidence, không mở nhánh mới nếu không đóng một DoD đã nêu.

## Đang làm

**Mốc mới nhất 2026-09-29:** theo yêu cầu owner đã bật lại đúng hai notebook:
Qwen agent **v7**, Llama guard **v5**, cả hai RUNNING/health READY tại lượt kiểm
06:40 UTC; source pull khớp và private. Package/config hiện hành:
`build/kaggle/structured_pair_release03a_20260929`. Không dùng endpoint v2 cũ.
[Report restart và sửa recovery](../docs/evaluation/phase5_restart_recovery_20260929.md)
ghi evidence và giới hạn. Host journal candidate đã sửa bốn lỗi recovery,
76 focused tests đạt; chưa deploy request-worker v3. Các mốc v2 bên dưới là
lịch sử. Mainline native Dev đã chạy xong 14/14 điều kiện; chưa nghiệm thu thêm DoD.

**Phase5: native runtime7mức, paired Dev28conditions và provenance12conditions đã hoàn tất.** Đã thêm
manifest/runner Dev API có identity/hash admission, checkpoint started/
completed/failed/interrupted, missing-only resume và public-only loading.
Owner đã cho đổi API, xác nhận tắt bốn phiên cũ, rồi triển khai Qwen3-8B agent
và Llama3.2-3B guard. Hai notebook v1 đã COMPLETE; ngày2026-09-28 owner yêu cầu restart, đã submit
v2 và probe cả hai READY ở release02a. Probe đọc-only mới lúc 19:57:46 UTC
ngày 2026-09-28 lưu tại
`build/kaggle/structured_pair_endpoint_check_20260928T115147/health_195746_20260929_status.json`
nhận agent `HTTP_ERROR`/530 và guard `NETWORK_ERROR`; không có inference nào.
Không suy notebook đã dừng từ lỗi truy cập, và không dùng snapshot READY cũ để
mở một run mới.

Đọc [API experiment runbook](api_experiment_runbook.md) để có commands, paths,
điểm nối code và xử lý phiên hết hạn. Đọc [lộ trình](../docs/evaluation/project_status_api_20260927.md)
để biết các gate còn thiếu. Native mainline Dev đã xong; bước còn lại là tổng
hợp các gate DoD/guard quality và formal freeze, không mở Test/Phase6/7.

## Bước tiếp theo

**Ưu tiên đã hiệu chỉnh sau đối chiếu kế hoạch gốc:** timeout/error/fallback là
yêu cầu của Phase 5; remote request-status/cancel v3 là hạ tầng bổ sung, không
phải điều kiện bắt buộc để chạy mọi Dev experiment. Tạm hoãn triển khai v3;
các mục triển khai v3 bên dưới chỉ là backlog. Bước chính tiếp theo là kiểm
runtime A0–A6 cùng cấu hình nền, guard fallback và các ca A6 provenance/final/
benign utility còn thiếu; mốc native mainline đã hoàn tất. Literal utility đạt
14/14; email utility đạt 3/7 do guard A3–A6 trả `SUSPICIOUS`. Giữ checkpoint và
chặn delivery uncertain; không semantic retry sau khi đã thấy kết quả. Xem
report mainline và decision log ngày 2026-09-29.

1. Không chạy lại các run đã terminal: levels diagnostic01 (7), paired Dev
   run01 (28), provenance run01 (12), pilot01 và Plan diagnostic01.
   [Paired report](../docs/evaluation/remote_api_paired_dev_v1_report.md) và
   [provenance report](../docs/evaluation/remote_api_provenance_v1_report.md)
   có receipts/raw/audits. Chỉ re-score/audit bằng nguồn đã pin.
2. [Worker v3 CPU report](../docs/evaluation/request_worker_v3_cpu_report.md):
   đã nối HF stop-event + sync hai CUDA devices, lifecycle fail-closed, giới hạn
   result/thread, worker composition và host terminal-status verifier.103tests
   đạt; exact8-file package4/4role/layout. V2receipt/source giữ nguyên.
   Host transport/journal/runtime và cached-result recovery đã có CPU candidate;
   ngày 2026-09-29 sửa thêm admission khi request khác còn uncertain, terminal
   quiescence checks và hash-binding recovery (76 tests đạt). Tiếp theo:
   notebook entrypoint/discovery/lifetime shutdown;
   commit/push source freeze + final package QA, rồi native cancellation diagnostic.
   Chưa deploy hoặc chứng minh GPU cancellation; không cần owner sửa notebook
   cho runtime hiện tại. Không lấy CPU mock sync hoặc host GRACEFUL làm native proof.
3. Trước inference mới phải có health GET thành công cho cả hai role và kiểm
   identity. Release03a đã READY cho agent v7/guard v5; tạo factory từ directory
   mới, không resume run cũ bằng identity mới. Giữ release02a và mọi lỗi lịch sử
   nguyên trạng. Launcher discover không
   tự refresh cached endpoint. Endpoint/key đổi nhưng session/source/model không
   đổi, vì vậy session_id v1 không phải boot ID.
4. Candidate safe-email v14 đã nối parser v4 với value-gate subject có phạm vi
   hẹp: safe public email chạy A6 PRE/POST/FINAL và final ALLOW; private body bị
   chặn ở PRE; global revoke/conditional/quoted không tạo anchor. 22 focused
   CPU tests, Ruff và mypy các file candidate đạt; 0 model/network request và
   `a6_native_ready=false`. Candidate origin email chỉ là profile ghép cặp,
   không thêm authority so với lexical v3. Chưa coi đây là API/Phase5 evidence;
   giữ v3 live và chỉ mở Dev run sau health READY mới.
5. Receipt native mainline nằm ở
   `experiments/manifests/phase5_mainline_native_dev.json`; report ở
   `docs/evaluation/phase5_mainline_native_dev_report.md`. Mọi runner dùng
   Closure/no-go mapping nằm tại `docs/evaluation/phase5_closure_no_go_20260929.md`.
   journal chung `build/evaluation/structured_api_sessions_v1`.
   Không xóa started/uncertain hoặc đổi root để vượt blocker; GET/models hay
   endpoint mới không chứng minh request cũ đã dừng. Không semantic retry.

RQ1 cần3task backbones; RQ2 giữ một agent/decoding quaA0–A6, guard cố định ở các
mức dùng guard, A0 không guard. Không fine-tune hoặc Test-driven tuning. Không
cần access/key mới; notebook giữ private trên đúng hai tài khoản hiện hành.

## Bằng chứng

- Latest QA: 8 regression mới tái hiện/sửa 4 lỗi host; 64 host/lifecycle + 12
  HTTP tests đạt; setup/Ruff/mypy610 đạt. Fresh readiness vẫn 16 CPU-indexed,
  3 diagnostic, 1 missing, `phase5_accepted=false`, Test payloads read 0.
  [Receipt](../experiments/manifests/phase5_restart_recovery_20260929.json).
  Bytes trước sửa đã lưu `build/evaluation/request_worker_host_v1_before_recovery_fix`;
  manifest host CPU cũ áp dụng cho snapshot đó, không áp dụng journal đã sửa.
- [Paired API report](../docs/evaluation/structured_pair_api_v1_report.md),
  [receipt](../experiments/manifests/structured_pair_api_v1.json): source
  `728821ea761b3994eb40ebba91ab8238e4667f82`, đã push trước GPU. Remote scripts
  khớp byte; receipt pushv1, pull latest khớp (pull suffix/v1 lỗi được giữ).
- Actual notebooks/ownership/model mounts trong [sổ Kaggle](kaggle_resources.md):
  buiquocviet/react-vn-qwen3-agent-api-v1 v1/136136611 và
  huylmhuhu/react-vn-llama3-guard-api-v1 v1/136136616. Mỗi máy private,2T4.
- Raw `build/evaluation/structured_pair_smoke01`: completed/final166,
  2agent+2guard calls,3Broker events; guardSAFE/LOW. Source319host hashes và
  11artifact hashes có receipt. SAFE-only diagnostic không fullA2/A6.
- QA triển khai lịch sử:77focused tests,4worker layouts,5Qwen tokenizer
  controls. Audit lượt này chạy setup/Ruff/mypy608files, knowledge-check và
  diff-check đạt; host/lifecycle regression 68/68 và email-origin controls
  22/22 đạt. Full `pytest -q` được khởi chạy nhưng bị dừng sau 251 tests và
  một dependency skip vì suite dài; không dùng lượt dừng đó làm acceptance.
- [Model-plan bridge CPU report](../docs/evaluation/phase5_field_model_bridge_v1_report.md),
  [typed-reference component](../docs/evaluation/phase5_field_reference_v1_report.md),
  [20DoD map](../docs/evaluation/phase5_dod_evidence_map.md) giữ evidence/giới hạn.
- Safe-email v14 CPU evidence: [protocol](../docs/evaluation/email_origin_v14_cpu_protocol.md),
  [report](../docs/evaluation/email_origin_v14_cpu_report.md),
  [manifest](../experiments/manifests/email_origin_v14_cpu.json). Source hashes
  pin parser/value-gate/runtime/tests; 22/22 focused controls pass, không API.
- Structured API Dev runner QA: 5 focused tests pass; setup/Ruff/mypy pass
  (566 source files). Manifest source hashes verified; no API key or endpoint is
  stored in the manifest. Initial `NETWORK_ERROR` was resolved by rerunning
  read-only discovery with network access; both workers then authenticated.
- Pilot `pilot01` subsequently completed 37/37 checkpoints after safe resume:
  21 clean agent tasks and 16 guard controls. Evaluator-only Dev report:
  [structured API Dev report](../docs/evaluation/structured_api_dev_v1_report.md).
  Agent utility is 3/21 (14.29%); guard detection is 5/8 attacks (62.5%) with
  3/8 benign flagged (37.5%). These are diagnostics only; no Phase 5 gate is
  promoted and no Test data was opened.
- Full `tests/unit tests/integration`: 4,793 passed, one native-tqdm skip and
  one expected xfail; two historical document/shutdown pin tests fail because
  their frozen wiring receipt hashes `scripts/validate_knowledge.py` differently
  from the current working tree. These failures predate the API runner and were
  not repaired or used to alter frozen evidence.

Restart/Plan diagnostic ngày2026-09-28: [báo cáo mới](../docs/evaluation/structured_plan_api_v1_report.md).
Hai notebook v2 READY, source pull khớp, preflight4/4. Diagnostic01 hoàn tất
1agent+1guard, Plan3refs hợp lệ,9Broker events; guardSAFE/LOW nhưng host chặnS2,
outputnull. Không chạy lại diagnostic để lấy kết quả khác.76focused tests,
setup/Ruff/mypy571files đạt; thêm5readiness tests đạt (tổng81checks liên quan).
Knowledge-check/diff-check đạt,15receipt hashes khớp, API-key scan0matches.
Readiness mới: `build/evaluation/phase5_gate_readiness_v1_restart02.json`,
16CPU-index/3diagnostic/1missing, không acceptance. Không cần owner bật lại
notebook hoặc gửi key; source/report mới còn local, không commit/push lượt này.
Phase5 không tăng acceptance.

Health follow-up 19:57:46UTC ngày2026-09-28: GET `/v1/models` chỉ đọc không
thành công — agent trả HTTP 530 và guard lỗi mạng. Receipt
`build/kaggle/structured_pair_endpoint_check_20260928T115147/health_195746_20260929_status.json`
giữ identity công khai, mã lỗi và không có prompt/response model. Không retry
và không chỉnh notebook trong khi chưa có quyền truy cập ổn định.

Ngày2026-09-28 tiếp theo: [remote API levels report](../docs/evaluation/remote_api_levels_v1_report.md),
[receipt](../experiments/manifests/remote_api_levels_v1.json).7/7completed,14agent+
10guard, calculator/final79 và PRE/POST/FINAL ở cả7mức; guard10validSAFE. Năm
host HTTP processes GRACEFUL/exit0/reaped;0uncertain HTTP.72raw/325source/
48journal hashes kiểm tra,24response records; repeated audit identical.
131focused/regression tests đạt, setup/Ruff/mypy576files đạt. Fullsuite không
chạy lại; giữ giới hạn hai historical pins đã ghi trên. Host source working-tree,
không commit/push. Không tăng acceptance hoặc claim remote cancellation.

Ngày2026-09-28 bổ sung: paired Dev28/28,56agent+40guard (40SAFE),
20host GRACEFUL; provenance12/12,33agent+26guard,8host GRACEFUL;0uncertain cả hai.
A0 cũng đạt hai Dev pairs, chưa defense benefit. Provenance10/12utility,
unknown_public A5/A6 PREdeny; A6 known-source matches=[] không là semantic proof.
[Receipts paired](../experiments/manifests/remote_api_paired_dev_v1.json) và
[provenance](../experiments/manifests/remote_api_provenance_v1.json) giữ hashes.
Không tăng acceptance, không Test/private oracle, không inference lại khi refresh.

QA bổ sung:51focused tests đạt (bao gồm HTTP loopback concurrency);
setup/Ruff/mypy583files/knowledge-check/diff-check đạt. Receipt evidence cũ
được đối chiếu lại381hashes; không sửa source frozen hoặc chạy inference lại.

Worker v3 tiếp theo:103focused/regression tests đạt37.02s; setup/Ruff/mypy590files.
Package `build/evaluation/request_worker_v3/preflight01`:4role/layout cases,
8module origins mỗi case, Python-I-S không import môi trường dev; GPU/model loads0.
[CPU receipt](../experiments/manifests/request_worker_v3_cpu01.json) lưu source/
QA/package hashes. Chưa commit/push; không sửa journal v1 hoặc rerun Dev đã terminal.

Encoded FINAL correction: freeze audit v3 tái lập run cũ với 94 artifact, 32
journal, 336 source path, evaluation01/02 byte-identical và không có inference
mới. Hardened v2 runner/evaluator chỉ là source candidate; không thay receipt
encoded_final_api_v1 cũ. [Audit report](../docs/evaluation/encoded_final_api_v1_freeze_audit_v3_report.md)
và [freeze manifest v3](../experiments/manifests/encoded_final_api_v1_hardened_freeze_v3.json).

## Giới hạn

- Guard quality chưa chốt; một phép tính và JSON hợp lệ không đủ chứng minh
  phát hiện tấn công. Public-field utility/unknown-origin đã có bounded native evidence; final-negative
  coverage và semantic lineage vẫn thiếu; không promote prototype hoặc tăng4/7 từ READY.
- No hidden chain-of-thought; mọi tool qua Broker; mock email/webhook không
  network. Evaluator GT không vào model/policy. Test không được mở để tuning.
- Endpoint/key hiện hành ở `build/kaggle/structured_pair_release03a_20260929/pair_endpoints.json`;
  RSA private key/connection files mode0600 và Git-ignore. Không cần owner
  dán key trong chat. Không có access mới còn chờ cho công việc tài liệu/CPU;
  network tool có thể cần sandbox approval, Kaggle private cần quyền owner.
- Model fingerprints không publisher attestation. API lifespan/uptime,
  request cancellation và task isolation chưa nghiệm thu; không coi lỗi
  worker cũ được sửa khi chuyển sang server chạy lâu.
- Serving source đã commit; report/receipt/memory và nhiều prototype hiện
  còn local. Raw trong build/results chưa backup ngoài máy được xác nhận.
  Chat mới cùng workspace đọc được; clone sang máy khác không có raw/keys.
  Không commit trạng thái riêng hoặc gom nhầm dirty files vào release.

## Lịch sử

[Bản bàn giao đầy đủ trước khi thu gọn](history_20260927_before_api_handoff_handoff.md)
giữ nguyên các mốc cũ, kể cả nextsteps đã được thay thế. Không dùng các lệnh
hoặc trạng thái “chưa endpoint/không GPU đang chạy” ở đó làm chỉ dẫn hiện hành.

Follow-up exact-email 2026-09-29 dừng sau A3 vì guard request `uncertain`; receipt `experiments/manifests/phase5_followup_email_exact_partial.json`. Không chạy A4–A6 hoặc đổi journal để vượt blocker.

Worker recovery 2026-09-29: package release04a (agent v8/guard v6) preflight 4/4 và discovery READY, nhưng follow-up bị chặn bởi record guard uncertain trong journal chung; xem `docs/evaluation/phase5_followup_recovery_block_20260929.md`.

Recovery epoch 2 đã xử lý đúng boundary bằng journal mới, chạy 4/4 A3–A6 và
không còn uncertain delivery. A3–A5 deny external sink theo coarse session
policy; A6 deny body có trailing newline. Không rerun mainline.

## Mốc bàn giao mới nhất — 2026-09-29

- Ablation newline đã được khai báo và chạy riêng bằng profile
  `terminal_line_ending_v1`: chỉ bỏ đúng một terminal LF/CRLF/CR, giữ raw và
  released hash, deny repeated ending/space/extra/private text. Kết quả CPU 9
  ca: 4 allow canonical-equivalent, 5 deny; không model/API/network/Test.
- Formal closure validator đã đọc closure/evidence map và metadata/hash của ba
  receipt; map đủ 20 DoD, xác minh `test_payloads_read=0`,
  `private_ground_truth_read=0`, `inference_performed=false`, và không có
  uncertain delivery trong các receipt hiện hành.
- Receipt chính thức:
  `experiments/manifests/phase5_formal_freeze_receipt_20260929.json`;
  báo cáo: `docs/evaluation/phase5_formal_freeze_report_20260929.md`.
  Quyết định giữ **NO_GO**, `phase5_accepted=false`, open DoD `[1..20]`.

## Bước tiếp theo cụ thể

Không cần bật lại notebook hay chạy lại 14 điều kiện mainline. Nếu tiếp tục
nghiên cứu, phải khai báo protocol/task identity mới cho một DoD cụ thể (ví dụ
native normalization ablation), giữ A3–A5 veto và guard threshold; không dùng
ablation CPU để ghi nhận native utility hoặc đóng Phase 5.

## Nghiên cứu đường đóng Phase 5

Đã lập [acceptance strategy và claim-to-evidence note](../docs/research/phase5_acceptance_research_20260929.md).
Đường được khuyến nghị là một closure candidate duy nhất với C1–C12 controls,
matched native A0–A6 matrix, confusion matrix cho guard, paired provenance
safe/unsafe/unknown và một receipt nối đủ 20 DoD. Không thêm runtime/candidate,
không dùng Test để tuning, không biến remote cancel thành DoD mới. Chỉ mở native
run sau khi cả hai notebook health/identity READY; nếu không thì ghi access
blocker và giữ NO-GO.
