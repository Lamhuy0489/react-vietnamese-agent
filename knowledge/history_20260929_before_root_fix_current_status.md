# Trạng thái hiện tại

Cập nhật 2026-09-29. Phase1–4 đã accepted; **Phase5 đang làm,4/7 nhóm nghiệm
thu**. Không dùng57% làm phần trăm toàn đồ án. Test vẫn khóa.

**Native closure deployment mới nhất:** release04a được kiểm tra read-only ngay
trước inference, hai notebook RUNNING và identity discovery READY. Epoch đầu
đã hoàn tất C1–C3 ở A0–A6 (21 condition records hợp lệ), rồi dừng tại C4/A0
vì một request agent delivery-uncertain. Recovery epoch dùng journal mới và
chỉ chạy C4–C12, nhưng lặp lại đúng blocker C4/A0 và dừng fail-closed. Combined
evaluator giữ nguyên cả hai journal, loại mọi uncertain record khỏi denominator,
và ghi 21/84 completed, 63 missing, `phase5_accepted=false`. Xem
[closure recovery report](../docs/evaluation/phase5_native_closure_recovery_report_20260929.md),
[combined evaluation](../build/evaluation/phase5_native_closure_combined01_20260929.json)
và [protocol](../docs/evaluation/phase5_native_closure_protocol_v1.md).
[Acceptance chính thức](../docs/project/phase_status.md),
[tiến độ và đường hoàn thiện](../docs/evaluation/project_status_api_20260927.md).
Đợt audit tổng thể ngày 2026-09-29 đã chốt đường đóng Phase 5 tại
[phase5_direction_audit_20260929.md](../docs/evaluation/phase5_direction_audit_20260929.md):
v12 chỉ là source/representation baseline, các prototype còn lại là lịch sử
hoặc prospective, không mở thêm candidate song song.

## Công việc hiện hành

**Hiệu chỉnh ưu tiên:** kế hoạch gốc yêu cầu guard timeout/error handling và
deterministic fallback, không yêu cầu xây một remote request-cancel service.
V3 lifecycle là hạ tầng tùy chọn, tạm hoãn deployment; tập trung local runtime
A0–A6, provenance/final protection và benign utility. Giữ API journal và
unresolved-delivery safeguards hiện có; không thay tiêu chí nghiệm thu.

**Mới nhất 2026-09-29 06:40 UTC:** restart theo yêu cầu owner thành công:
agent notebook v7, guard notebook v5, cả hai RUNNING/health READY; source pull
khớp, private. Dùng config ở `build/kaggle/structured_pair_release03a_20260929`.
Mốc lỗi truy cập v2 bên dưới là lịch sử. Host recovery candidate đã sửa bốn lỗi
với 76 focused tests đạt; lifecycle v3 chưa deploy, còn native mainline Dev đã
chạy xong theo receipt riêng.
Đọc [report restart/recovery](../docs/evaluation/phase5_restart_recovery_20260929.md).

**Native mainline Dev đã hoàn tất 2026-09-29:** local runner chạy đủ 14/14
điều kiện (hai task benign × A0–A6) qua Qwen agent và Llama guard. Private→public
read order đúng 14/14, literal utility 7/7 mức, email utility 3/7 mức; A3–A6
email bị guard đánh dấu `SUSPICIOUS`, giữ nguyên và không rerun. Không có private
marker trong final/mock payload, evaluator01/02 byte-identical, Test/private GT
vẫn 0. Đây là Dev diagnostic, chưa phải acceptance. Xem [mainline report](../docs/evaluation/phase5_mainline_native_dev_report.md)
và [receipt](../experiments/manifests/phase5_mainline_native_dev.json).

Closure audit hiện hành: [no-go report](../docs/evaluation/phase5_closure_no_go_20260929.md). DoD20 vẫn mở; không chạy lại 14 condition đã terminal.

Owner chọn **local điều phối thí nghiệm, Kaggle phục vụ inference qua API**.
Qwen3-8B là task agent; Llama3.2-3B-Instruct là guard candidate. Đã thay bốn
phiên cũ bằng hai notebook structured v1 sau khi owner xác nhận tắt hết.
Ngày2026-09-28 đã xác nhận hai phiên v1 COMPLETE và restart cùng notebook lên
v2, release02a. Snapshot 19:14 UTC trước đó vẫn ghi cả agent và guard `READY`,
nhưng health probe đọc-only mới lúc 19:57:46 UTC ngày 2026-09-28
(`build/kaggle/structured_pair_endpoint_check_20260928T115147/health_195746_20260929_status.json`)
nhận agent `HTTP_ERROR`/530 và guard `NETWORK_ERROR`. Đây là lỗi truy cập tại
thời điểm kiểm, không đủ để kết luận notebook đã dừng hay endpoint đã đổi
identity; không chạy inference, không retry semantic và không submit lại.

[Hướng dẫn tiếp tục thực nghiệm](api_experiment_runbook.md) là runbook hiện hành;
[bàn giao](handoff.md) ghi next action/access. UI8765/config/launcher bốn model
cũ chưa chuyển sang hai notebook này. Batch-only preference là lịch sử.

## Đã có bằng chứng

- Source serving/client/launcher freeze `728821ea761b3994eb40ebba91ab8238e4667f82`
  đã push trước GPU. Hai notebook private,2T4 mỗi máy, không Dataset; v1 là evidence lịch sử,
  v2 là phiên restart hiện hành.
- Paired task23*7+5:2agent+2guard calls, một calculator qua Broker, final166 đúng
  schema; guard SAFE/LOW cả hai lượt. Không retry, không hidden reasoning.
- 77focused tests,4exact worker layouts,5tokenizer controls và native warmup
  đạt trong lượt triển khai. [Report](../docs/evaluation/structured_pair_api_v1_report.md),
  [receipt](../experiments/manifests/structured_pair_api_v1.json),
  [actual notebook URLs/versions](kaggle_resources.md).

## Phần đang chờ triển khai

**Manifest + runner Dev nhỏ đã hoàn thành ở local** với 21 clean tasks và 8
attack/benign pairs, checkpoint/fault QA, identity/hash admission và resume
missing-only. Pilot `build/evaluation/structured_api_dev_v1/pilot01` đã chạy
37/37 terminal checkpoints qua hai API sau khi discovery xác nhận READY. Dev
evaluator ghi agent utility 3/21 (14.29%), guard attack detection 5/8 (62.5%)
và benign flag 3/8 (37.5%). Đây là diagnostic của profile mới, chưa đóng DoD
hay Phase5; không dùng one-task smoke như benchmark.
Đã nối HTTP factory qua public candidate runtime và chạy một synthetic task
qua đủA0–A6 với PRE/POST/FINAL. Dev differential và provenance nhỏ đã hoàn tất; quality/20DoD vẫn chưa nghiệm thu.

Readiness audit 20 DoD đã chạy fail-closed: 16 mục có CPU evidence, 3 mục
diagnostic-only (A2, A6 provenance, benign utility), DoD20 chưa đủ evidence;
20/20 vẫn mở vì blocker native. Xem [báo cáo readiness](../docs/evaluation/phase5_gate_readiness_v1_report.md).

Typed-reference component/model-plan bridge đã có CPU controls nhưng host
Grant vẫn là giả định; chưa fullReAct/nativeA6. Đã bổ sung adapter Plan riêng và diagnostic theo
[protocol](../docs/evaluation/structured_plan_api_v1_protocol.md); client action/final frozen giữ nguyên. Guard quality, benign utility,
API lifecycle/isolation/resume và formal freeze còn mở. Không thay baseline
chính thức hoặc cộng điểm lịch sử sang model/profile mới.

RQ1 vẫn cần3task backbones (có thể chạy tuần tự); cặp agent/guard chưa đáp ứng
ba model trả lời. RQ2 giữ một task backbone/decoding quaA0–A6, A0 không guard.
Không fine-tune thực nghiệm chính; không Test-driven tuning.

## Kết quả mới nhất ngày 2026-09-29

- Candidate grammar `authorization_anchors_v4_cpu`: 8/8 controls CPU đạt; v3
  frozen không đổi. Chained reads và prohibition gắn với resource riêng không
  còn biến một destination công khai thành global revoke. Global revoke,
  cancel, conditional, quoted/reported instruction và exact-destination checks
  vẫn fail-closed. Runtime v13 chỉ là binding opt-in cho A2/Dev; metadata ghi
  `a6_native_ready=false` vì value-origin/index v3 chưa được version/audit đồng
  bộ. 70 focused tests, setup/Ruff/mypy đạt; matrix có 0 model/network request.
  Xem [protocol](../docs/evaluation/authorization_anchors_v4_cpu_protocol.md),
  [report](../docs/evaluation/authorization_anchors_v4_cpu_report.md),
  [receipt](../experiments/manifests/authorization_anchors_v4_cpu.json).
- Candidate safe-email A6 v14 đã được khóa thành một CPU/Dev control riêng:
  parser v4 + subject value-gate chỉ cho phép subject xuất hiện trong affirmative
  send clause, còn body/destination/private/unknown/revoke/quote/conditional vẫn
  fail-closed. 22 focused tests pass; safe public email có PRE/POST/FINAL và
  final ALLOW, private body bị PRE deny. 0 model/network request,
  `a6_native_ready=false`; origin profile ghép cặp không thêm authority so với
  lexical v3. Xem [protocol](../docs/evaluation/email_origin_v14_cpu_protocol.md),
  [report](../docs/evaluation/email_origin_v14_cpu_report.md) và
  [manifest](../experiments/manifests/email_origin_v14_cpu.json). Chưa phải
  native/API evidence hay Phase5 acceptance.
- Encoded FINAL historical run đã được freeze audit v3 read-only: 94 artifact,
  32 journal và 336 source path khớp; evaluation01/02 giống nhau và saved
  evaluator tái lập đúng kết quả. V2 runner/evaluator chỉ bổ sung hash terminal
  checkpoint và chống symlink, không chạy inference mới. Xem [audit report](../docs/evaluation/encoded_final_api_v1_freeze_audit_v3_report.md)
  và [hardened freeze v3](../experiments/manifests/encoded_final_api_v1_hardened_freeze_v3.json).

Restart/Plan diagnostic ngày2026-09-28: [báo cáo mới](../docs/evaluation/structured_plan_api_v1_report.md).
Hai notebook v2 READY, source pull khớp, preflight4/4. Diagnostic01 hoàn tất
1agent+1guard, Plan3refs hợp lệ,9Broker events; guardSAFE/LOW nhưng host chặnS2,
outputnull. Không chạy lại diagnostic để lấy kết quả khác.76focused tests,
setup/Ruff/mypy571files đạt. Phase5 không tăng acceptance.

## Bước mới nhất: remote runtime7mức

[Report](../docs/evaluation/remote_api_levels_v1_report.md): journal bền vững,
factory dựng TLS trong child process, public runtime không bypass gate. Native
7/7completed,14agent+10guard,7calculator/final79;5host workers GRACEFUL/reaped,
0uncertain,131tests đạt. Đây chỉ là diagnostic. Tiếp theo là worker request-status/cancel; hai diagnostic tiếp theo đã hoàn tất như dưới đây.
Journal chung: `build/evaluation/structured_api_sessions_v1`; không xóa uncertain.

## Kết quả bổ sung ngày2026-09-28

- [Paired Dev report](../docs/evaluation/remote_api_paired_dev_v1_report.md):
  run01 hoàn tất28/28conditions,56agent+40guard,0uncertain. Hai attack/benign
  pairs đủA0–A6 đều có utility/exposure,0bounded violations/leaks. A0 cũng đạt,
  chưa có bằng chứng lợi ích defense. Audit lặp khớp; resume tạo0condition mới.
- [Provenance report](../docs/evaluation/remote_api_provenance_v1_report.md):
  run01 hoàn tất12/12conditions,33agent+26guard,0uncertain.10/12utility;
  unknown_public bị A5/A6 chặn ởPRE. Không chứng minh FINAL leak blocking hoặc
  typed semantic lineage. Giữ nguyên hai run và source đã pin, không retry.
- [Lifecycle candidate](../docs/evaluation/request_lifecycle_v2_cpu_report.md):
  state machine và HTTP auth/status/cancel đã có CPU tests, chưa deploy.
  V3 tiếp theo đã nối native adapter + CUDA sync hai thiết bị, result/thread bounds,
  worker composition và verifier host. [Report v3](../docs/evaluation/request_worker_v3_cpu_report.md):
  103tests đạt,4/4exact package cases,8modules isolated. Chưa native/GPU proof.
  Host transport/journal/runtime và cached-result recovery đã có CPU candidate,
  được sửa/test bổ sung ngày 2026-09-29. Bước tiếp: notebook entrypoint/discovery/
  lifetime shutdown; source freeze/final QA rồi native lifecycle diagnostic.
- Health GET lúc12:11:14UTC và 19:14UTC trước đó từng ghi cả agent/guard READY;
  probe mới 19:57:46UTC đã được lưu như một bằng chứng lỗi truy cập riêng trong
  cùng endpoint snapshot. Chỉ probe mới nhất được dùng làm điều kiện mở API run.
  release02a là package/config lịch sử; endpoint/key cũ đã hết hiệu lực.
  Source/model/session metadata giữ nguyên dù endpoint/key đổi: session_idv1
  không chứng minh boot mới hoặc request cũ đã dừng. Không reset journal.

QA bổ sung:51focused tests đạt (bao gồm HTTP loopback concurrency);
setup/Ruff/mypy583files/knowledge-check/diff-check đạt. Receipt evidence cũ
được đối chiếu lại381hashes; không sửa source frozen hoặc chạy inference lại.

## Lưu trữ và lịch sử

Endpoint/key hiện hành chỉ local ở `build/kaggle/structured_pair_release03a_20260929/pair_endpoints.json`;
không in hoặc gửi qua chat. Raw/config trong build không có trên GitHub.
Report/receipt/memory mới còn local; chưa backup ngoài máy được xác nhận.
Giữ dirty working tree; không routine commit/push ghi chú hoặc sửa nguồn frozen.

[Lịch sử trước khi thu gọn](history_20260927_before_api_handoff_current_status.md)
giữ đầy đủ thất bại/Dev32/prototype, không làm next action hiện hành.

Follow-up exact-email 2026-09-29 dừng sau A3 vì guard request `uncertain`; receipt `experiments/manifests/phase5_followup_email_exact_partial.json`. Không chạy A4–A6 hoặc đổi journal để vượt blocker.

Worker recovery 2026-09-29: package release04a (agent v8/guard v6) preflight 4/4 và discovery READY, nhưng follow-up bị chặn bởi record guard uncertain trong journal chung; xem `docs/evaluation/phase5_followup_recovery_block_20260929.md`.

Recovery epoch 2 đã hoàn tất 4/4 A3–A6 với agent v8/guard v6 và journal mới:
A3–A5 giữ veto coarse, A6 fail-closed vì model thêm trailing newline, không có
email nào được gửi. Evaluator lặp lại byte-identical, resume tạo 0 request.
Xem [epoch 2 report](../docs/evaluation/phase5_followup_email_exact_epoch2_report.md)
và [receipt](../experiments/manifests/phase5_followup_email_exact_epoch2.json).

Hai hạng mục còn lại của closure đã được hoàn thiện ngày 2026-09-29. Ablation
CPU `terminal_line_ending_v1` chạy 9 ca (4 canonical equivalents ALLOW, 5
mismatch DENY), giữ raw/released SHA-256 và không gọi model/API/network; xem
[protocol](../docs/evaluation/phase5_terminal_normalization_ablation_v1_protocol.md),
[report](../build/evaluation/phase5_terminal_normalization_ablation_v1/report.md)
và [receipt](../experiments/manifests/phase5_terminal_normalization_ablation_v1.json).
Bộ validator formal đã map đủ 20/20 DoD và xác nhận hash các receipt mainline,
epoch2 và ablation; quyết định được đóng băng là **NO_GO**, `phase5_accepted=false`,
20/20 DoD vẫn mở. Xem [formal report](../docs/evaluation/phase5_formal_freeze_report_20260929.md)
và [freeze receipt](../experiments/manifests/phase5_formal_freeze_receipt_20260929.json).

Đường nghiên cứu để chuyển từ NO-GO sang acceptance được ghi ở [Phase 5
acceptance strategy](../docs/research/phase5_acceptance_research_20260929.md):
freeze một candidate duy nhất, chạy matched native C1–C12 qua A0–A6, đo guard
confusion matrix và A6 safe/unsafe/unknown provenance. Không mở thêm runtime,
không dùng Test để tuning, và không coi remote cancellation là DoD mới.
