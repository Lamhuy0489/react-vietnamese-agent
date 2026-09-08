# Bộ nhớ dự án

Đây là bộ nhớ phát triển đồ án, được quản lý phiên bản cùng GitHub; không phải
memory của agent đang được benchmark. Không cần tài khoản hoặc graph database.

## Bắt đầu phiên làm việc

1. [Trạng thái phase chính thức](../docs/project/phase_status.md).
2. [Tóm tắt hiện tại](current_status.md).
3. [Bàn giao: đang dở và bước tiếp theo](handoff.md).
4. [Contract](../docs/project/research_contract.md),
   [invariants](../docs/project/invariants.md), rồi chỉ đọc tài liệu của phần
   đang làm theo [phase map](../docs/project/phase_map.md).

Phase 1, clean_v1.1 Phase 2 và adversarial_v2 Phase 3 đã accepted; Test đã khóa.
Phase 4 đã nghiệm thu runtime pass-through, deep Dev parity và overhead;
[báo cáo 12 DoD](../docs/architecture/phase4_report.md). Phase 5 đã được mở;
xem [tiến độ hiện hành](phase5_progress.md).
Pilot Gemma 4/Qwen 7B đã hoàn tất; Llama chưa chạy.

## Tra theo công việc

- Lệnh kiểm tra và chạy local: [runbook](runbook.md).
- Quyết định, lý do và ngoại lệ: [decision log](../docs/project/decision_log.md).
- Pilot LLM: [nhật ký](multimodel_dev_pilot.md),
  [báo cáo measured Dev](../docs/evaluation/measured_dev_pilot_report.md).
- Phase 2 đang có hiệu lực: [clean_v1.1](clean_v11_progress.md).
- Phase 3 đang làm: [tiến độ và thiếu sót đã audit](phase3_progress.md).
- Release Phase 3 hiện hành: [nghiệm thu v2 và giới hạn](../docs/benchmark/adversarial_release_v2_summary.md).
- Phase 4 hiện hành: [nền tảng và phần còn lại](phase4_progress.md).
- Phase 5 hiện hành: [cấu hình, guard và tích hợp còn lại](phase5_progress.md).
- Canonical/split hiện hành: [70 canonical cho authoring, grouped 40/30](../docs/benchmark/canonical_selection_summary.md).
- Phần trăm Phase 3 và tiêu chí còn thiếu: [readiness theo DoD](phase3_readiness.md).
- Tránh lặp lỗi Kaggle: [lessons](kaggle_lessons.md).
- Guard model/GPU preflight: [nguồn ứng viên và giới hạn](guard_model_preflight_evidence.md).
- Guard GPU probe đang triển khai: [upload, audit và bước tiếp](guard_gpu_probe_v1.md).
- Guard cancellation/VRAM recovery: [protocol và tiến độ](guard_cancellation_v1.md).
- Agent/guard cùng GPU: [placement admission và giới hạn](coexistence_placement_v1.md).
- Model agent trên Kaggle: [read-only mount authentication](agent_mount_v1.md).
- Bằng chứng lịch sử: [Phase 1](phase1_evidence.md),
  [Phase 2 v1 cũ](phase2_evidence.md),
  [audit v1 và withdrawal](integrity_audit_20260905.md).

## Quy tắc cập nhật

- `docs/project/phase_status.md` quyết định acceptance; bộ nhớ chỉ tóm tắt.
- `current_status.md` cần trạng thái mới nhất; mục lịch sử phải ghi rõ.
- `handoff.md` ghi việc đã kiểm tra, việc đang dở, bước kế tiếp và điều kiện
  được tiếp tục. Không ghi “đã xong” khi chỉ mới có file.
- Kết quả phải liên kết report/manifest; giữ riêng lỗi hạ tầng và lỗi ngữ nghĩa.
- Cuối mỗi mốc: cập nhật bàn giao, chạy `make knowledge-check`, rồi commit
  những thay đổi đã kiểm tra. Không giả định toàn bộ lịch sử chat sẽ còn sẵn.
- Không chép token, credentials, private GT, nội dung held-out Test hoặc hidden
  chain-of-thought vào bộ nhớ. Chỉ giữ trạng thái/quy trình/bằng chứng cho phép.
- Validator chỉ kiểm tra cấu trúc/link, không tự chứng minh nội dung còn đúng;
  cần đối chiếu trạng thái với bằng chứng sau mỗi thay đổi.
