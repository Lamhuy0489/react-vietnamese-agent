# Bàn giao phiên làm việc

Cập nhật: 2026-09-06. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Theo yêu cầu owner: củng cố knowledge rồi tiếp tục Phase 3. Memory đã được
tổ chức lại theo chỉ mục → trạng thái → bàn giao → bằng chứng, không cài thêm
dịch vụ và không thay đổi benchmark agent.

Phase 3: bản v1 có 70 family/350+350 variants nhưng chưa accepted. Workbench
riêng đã có bốn cặp executable, chưa split/review, không tính vào quota chính.
16 lượt Replay đã chứng minh reachable overlay, safe utility và nhận diện
negative fixtures; schema/oracle còn bị giới hạn ở các fixture này.
Đọc [tiến độ Phase 3](phase3_progress.md) để xem những thiếu sót đã xác minh.

## Bước tiếp theo

1. Đọc [Phase 3](../plan/phase3.md),
   [adversarial contract](../docs/benchmark/adversarial_contract.md) và
   [split rules](../docs/benchmark/split_rules.md).
2. Chạy `make phase3-audit`: hiện cố ý không cấp acceptance; không retry GPU
   hoặc đổi dữ liệu tại chỗ để làm xanh gate.
3. Đọc [contract workbench](../docs/benchmark/adversarial_workbench_contract.md),
   mở rộng schema canonical/data-scope và QA ngoài bốn fixture. Sau đó author
   canonical đa dạng với matched benign và bằng chứng thực thi.
4. Review nhóm semantic/template, xác định split rồi mới sinh variants. Giữ
   bản draft cũ làm bằng chứng; không âm thầm reseal/move family.
5. Chỉ cập nhật acceptance khi có kiểm tra thực sự. Đọc [runbook](runbook.md)
   và chạy các kiểm tra trước commit/push.

## Bằng chứng

- Nguồn trạng thái: [phase status](../docs/project/phase_status.md).
- Phase 1 accepted; Phase 2 clean_v1.1 accepted dưới owner automated-QA waiver:
  [v1.1 progress](clean_v11_progress.md).
- Gemma 4/Qwen 7B pilot đã hoàn tất, source inference `58fdeb5`, source report
  `3b7527a`, release `2301a12`:
  [completion receipt](../experiments/manifests/measured_pilot_completion.json),
  [báo cáo](../docs/evaluation/measured_dev_pilot_report.md).
- Strict success 6/21 và 3/21; đây là Dev diagnostic, không final model ranking.
  Không cần chạy lại pilot chỉ vì điểm thấp.
- Quyết định và waiver: [decision log](../docs/project/decision_log.md).
- [Audit Phase 3](../experiments/manifests/phase3_draft_audit_20260906.json)
  xác minh số lượng/hash nhưng ghi rõ lỗi template/surface/stratification và
  gate chưa thực thi. Không có inference mới trong lượt củng cố knowledge.
- Kiểm tra lượt trước: 130 tests pass; setup/Ruff/mypy (98 source files) và
  `make knowledge-check` pass. clean_v1.1 sealed-read-only validation pass;
  hash draft v1, auditor và measured releases khớp, không thay input đã khóa.
- [Workbench receipt](../experiments/manifests/phase3_workbench_v2_validation_01.json):
  source implementation `b7ae80c`, bốn cặp, 16 Replay, tám safe/tám negative đạt
  điều kiện fixture. Test có
  chặn network và lặp lại observable traces. Kiểm tra mới nhất: 143 tests,
  setup/Ruff/mypy 103 source files pass; không thay dữ liệu/release đã khóa.

## Giới hạn

- Phase 3 đang authoring; Phase 4–5 chưa được triển khai trong lượt này.
- Không có held-out model run; QA split tĩnh không được dùng để tuning.
- Llama chưa chạy vì Meta access pending; không cần hỏi lại quyền Google.
- Owner đã bỏ yêu cầu Minh peer-review trong workflow dùng chung máy; không
  giả reviewer hoặc coi automated QA là bằng chứng human semantic review.
- Không đổi bytes clean_v1/v1.1 hoặc measured releases. Không đưa credentials,
  private GT, held-out payloads hay hidden reasoning vào memory.
- GitHub là source of truth; remote push chỉ sau kiểm tra. Không ghi “đã push”
  nếu chưa có xác nhận thành công.
