# Prompt cho phiên sau

Cập nhật: 2026-10-28 10:30. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A. R4 security Test v1 xong (2026-10-28), kết quả yếu và đã chẩn đoán
(decision log 2026-10-28: oracle tính đọc vô hại là harm, agent chọn sai tool, scope A4 overfit
câu chữ Dev, guard vô dụng). Owner chọn A+B+C: phòng thủ v2 (user tin cậy, tách control/data
flow, chỉnh trên Dev), chỉ số harm có tác dụng phụ, Test-2 khoảng 20 family mới seal trước khi chạy
v2. Test v1 không chạy lại, không dùng để chỉnh. Không sửa file trong manifest v1.

B (side-effect harm) xong. C xong: Test-2 đã seal (seal.json 1576b89a…), là held-out, không dùng
để chỉnh. E2 code xong (tools/doc_search_v2.py, scripts/run_adversarial_e2_api_v1.py, decision log "E2").
Việc đầu tiên: bật notebook theo bảng trong handoff mục "Đang làm" (Qwen trên huylmhuhu, buiquocviet,
meanalways; guard trên huylmhuhu; HF token đọc từ ~/.hf_token_r5, không in ra), chạy A0, A1, A6 × 400 Dev
trong E2 song song, chấm bằng cả hai evaluator, ghi bảng vào decision log. Sau đó viết D2 và chỉnh
≤3 vòng trên Dev E2, rồi final_config_v2. Không sửa pyproject.toml hay requirements-dev.txt (seal ghim
hash). Song song: RQ3 250 biến thể robustness. Việc phụ: PR sửa 21 test chỉ hỏng trên CI.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
