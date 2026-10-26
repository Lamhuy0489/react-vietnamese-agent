@AGENTS.md

## Claude Code — quy trình phiên chuẩn

Dự án chỉ dùng Claude Code. Mục này là quy trình duy nhất cho mọi phiên và ưu tiên hơn
mục "Start here" của `AGENTS.md` cũng như các runbook lịch sử. Trả lời owner bằng tiếng Việt.

**Đầu phiên, đọc theo thứ tự:**

1. `knowledge/next_session_prompt.md`: việc đầu tiên của phiên này.
2. `knowledge/current_status.md`, rồi `knowledge/handoff.md` (mục "Đang làm" có lệnh resume).
3. 3 mục cuối của `knowledge/session_log.md`.
4. `knowledge/rebuild_a_runbook.md`, mục "Bản đồ": chạy ở đâu, kết quả lưu ở đâu, file nào
   ghi gì. Làm đúng theo đó; thêm runner hay đổi chỗ lưu thì sửa Bản đồ trước.
5. Khi cần: `docs/project/roadmap_v2_rebuild.md`, `docs/project/decision_log.md`,
   `knowledge/kaggle_resources.md`.

Không suy ra notebook Kaggle còn sống từ file cũ; kiểm bằng `kaggle kernels status`.

**Cuối phiên (khi có thay đổi đáng kể):**

1. Thêm một mục vào cuối `knowledge/session_log.md`.
2. Cập nhật `knowledge/handoff.md` (đang làm, lệnh resume, bước tiếp theo) và
   `knowledge/current_status.md`; cập nhật `knowledge/kaggle_resources.md` nếu đã bật notebook.
3. Viết lại khối `text` trong `knowledge/next_session_prompt.md`. Prompt phải nằm trong file;
   đưa trong chat là chưa đủ.
4. Chạy `make knowledge-check`, rồi commit và push.
