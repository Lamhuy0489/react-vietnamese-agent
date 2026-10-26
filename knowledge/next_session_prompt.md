# Prompt cho phiên sau

Cập nhật: 2026-10-26 17:45. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A, R1 xong, R2 khoảng 85%. Lượt A0–A6 Dev đầy đủ (Qwen3-8B, A6 v2,
guard Llama-3.2-3B) đã xong 2.800/2.800, 0 model_error; kết quả ở
results/rebuild_a/adv_dev_qwen3_8b_a6v2_eval.json, bảng trong decision log.

Việc đầu tiên: xử lý cảnh báo đo lường trong decision log (mục "Rebuild A0–A6 Dev result").
40 ASR còn lại ở A4–A6 cũng xảy ra ở biến thể benign, phần lớn là doc_search trả [] bị
tính vi phạm. Trình bày cho owner các cách tính ASR rồi để owner chọn. Sau đó phân tích vì
sao A6 v2 chạy thật benign 55/200 so với replay 115/200. Chưa đóng băng R3 khi chưa quyết.
Kiểm PR #4 đã merge và tag phase5-closure chưa.
Không sửa prompt v3, không đụng Test, không sửa dữ liệu đã seal.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
