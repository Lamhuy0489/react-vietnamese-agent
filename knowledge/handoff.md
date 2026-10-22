# Bàn giao phiên làm việc

Cập nhật: 2026-10-23. Đang ở **R0 (Reset)** của
[lộ trình v2](../docs/project/roadmap_v2_rebuild.md). Đã chốt 3 quyết định R0;
phần dọn repo của R0 chưa làm.

## Đang làm

R0, tuần 24/10–30/10. Đã xong:

- Commit/push toàn bộ việc còn dở.
- Dọn local storage: khoảng 18 GB xuống 2,3 GB; xem [storage](storage_and_obsidian.md).
- Chốt model, guard và chỉ số.
- Kiểm tính toàn vẹn của dữ liệu.

## Bước tiếp theo

1. Owner xin quyền HF gated cho Llama 3.1 8B Instruct và Llama Prompt Guard 2 86M,
   rồi xem hạn mức GPU Kaggle trong Settings.
2. Merge branch hiện tại vào `main` (qua PR), gắn tag `phase5-closure` trên `6509ae0`.
3. Dọn trên `main`: gom các script cũ, chưa dùng (v1/v2, preflight, chẩn đoán) vào
   `scripts/legacy/` hoặc xóa, chỉ giữ dưới 30 script đang dùng. Chạy
   ruff/mypy/pytest sau khi dọn. Không đổi các đường dẫn mà manifest hash vẫn tham chiếu
   nếu receipt còn cần audit lại; lịch sử khôi phục qua tag.
4. Viết `docs/metrics_spec.md` theo các quyết định trong decision log ngày 2026-10-23.
5. Sang R1–R2 theo mức rebuild A: harness mới (1 worker API và 1 evaluator), rồi chạy lại
   A0 smoke → clean Dev × 3 model → bake-off guard → A0–A6 Dev. Xem mục 2b của lộ trình.

## Bằng chứng

- Quyết định: [decision log](../docs/project/decision_log.md), mục ngày 2026-10-23.
- Kiểm dữ liệu: `scripts/assemble_adversarial_release.py --action check`
  cho kết quả valid, test_sealed, 700 biến thể; 23 file clean v1.1 khớp hash.
- Phase 5: [completion receipt](../experiments/manifests/phase5_completion_20261002.json).

## Giới hạn

- **Repo GitHub đang PUBLIC** và chứa `data/clean/v1_1/private/*` (GT clean, gồm cả
  Test) cùng payload Test của adversarial. Owner cần quyết định có chuyển repo sang
  private trước Phase 7 hay không. Không tự đổi visibility.
- Không được sửa dữ liệu đã seal. Muốn tinh chỉnh dữ liệu phải tạo version mới
  và chỉ làm trên Dev.
- Guard recall 52,5%, 12/84 model_error, C6 bị chặn dư. Các điểm này để R2 xử lý trên Dev.
- Chưa có reviewer thứ hai; Minh chưa nhận lời mời GitHub.
- [Handoff trước lộ trình v2](history_20261023_before_roadmap_v2_handoff.md).
