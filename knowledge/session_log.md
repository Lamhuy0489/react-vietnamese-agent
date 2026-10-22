# Nhật ký phiên chat

Mỗi phiên ghi một mục, mới nhất ở cuối. Mỗi mục gồm: mục tiêu, quyết định, việc đã
làm, việc còn dở. Chỉ ghi các dữ kiện đã xác minh. Không ghi credential, GT hay payload Test.
[Prompt cho phiên sau](next_session_prompt.md) · [Handoff](handoff.md).

## 2026-10-23 — Claude Code: đánh giá đồ án, dọn repo, lộ trình v2

- **Mục tiêu owner:** đánh giá tính khả thi, bỏ phần thừa, "đập đi xây lại" với lộ
  trình mới, lưu context để các phiên sau làm tiếp.
- **Đánh giá:** đề tài khả thi; benchmark và runtime A0–A6 là phần giá trị. Điểm yếu
  là quy trình bằng chứng quá nặng (287 script, 170 báo cáo, 348 manifest) và chưa
  có kết quả cho RQ1–RQ3.
- **Đã làm:**
  - Commit `a402772` (250 file còn dở, quét credential không thấy giá trị nào).
  - Dọn storage: xóa 3 file tar guard giống hệt nhau, trọng số Qwen2.5-1.5B, venv
    API và cache; nén `build/pytest_*` và `results/*preflight*` vào `archive_local/`.
  - Commit `8a2419e`: lộ trình v2.
  - Commit `6509ae0`: các quyết định R0.
- **Quyết định:** model RQ1 là Qwen3-8B, Gemma 4 12B, Llama 3.1 8B; RQ2 cố định
  Qwen3-8B; guard A2 chọn bằng bake-off trên Dev; ASR tính hành động thực thi,
  model_error tính thất bại.
- **Kiểm dữ liệu:** seal adversarial_v2 hợp lệ; clean v1.1 khớp 23 hash. Phát hiện:
  repo public chứa GT private, owner chưa quyết.
- **Còn dở:** merge vào main, tag, dọn script, metrics_spec; owner xin quyền HF Llama.
- **Bổ sung:** owner cho phép đập đi; chọn mức A, tức chạy lại pipeline từ Phase 1, giữ data và runtime. Không viết lại runtime, không làm lại data.
