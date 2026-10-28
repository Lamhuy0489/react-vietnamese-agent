# Prompt cho phiên sau

Cập nhật: 2026-10-28 06:40. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A. R4 security Test v1 xong (2026-10-28), kết quả yếu và đã chẩn đoán
(decision log 2026-10-28: oracle tính đọc vô hại là harm, agent chọn sai tool, scope A4 overfit
câu chữ Dev, guard vô dụng). Owner chọn A+B+C: phòng thủ v2 (user tin cậy, tách control/data
flow, chỉnh trên Dev), chỉ số harm có tác dụng phụ, Test-2 khoảng 20 family mới seal trước khi chạy
v2. Test v1 không chạy lại, không dùng để chỉnh. Không sửa file trong manifest v1.

Việc đầu tiên: Test-2 đã sinh nhưng chưa seal (data/adversarial/release_test2). Owner xem 20 câu
lệnh gốc (data/adversarial/test2_authoring_v1/canonicals.json), rồi seal bằng
scripts/build_test2_release_v1.py seal --approved-by owner và ghi hash vào decision log. Sau đó E2
doc_search_v2, chạy lại Dev mốc, rồi D2. B (side-effect harm) đã xong.
Song song: RQ3 250 biến thể robustness. Việc phụ: PR sửa 21 test chỉ hỏng trên CI.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
