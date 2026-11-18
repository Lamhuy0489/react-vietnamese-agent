# Prompt cho phiên sau

Cập nhật: 2026-11-18 (tối). Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: pin đã sửa (17/11). Không render hình/biên dịch PDF trên máy (owner dùng Overleaf), không tự khởi động lại
OmniRoute. IPv6 Wi-Fi đang TẮT (18/11, tránh địa chỉ trycloudflare chập chờn); trước khi chạy Kaggle lần sau kiểm lại.

Trạng thái (18/11 18:40): Test-4 đã chạy xong một lần dưới final_config_v5. H1 KHÔNG ĐẠT: v1 6/48 → v3 2/48 họ (gộp 3 mô
hình), McNemar 4–0, p một phía 0,0625 (hiệu ứng sàn: nền v1 thấp hơn giả định 14/48). H2–H4 chỉ mô tả. v3: 0 vi phạm sink,
0/24 ca thích nghi; C1/C2 chặn đúng 4 họ v1 lọt; M5 sửa số/đơn vị lọt cả hai. Số: results/rebuild_c/test4_analysis_v1.json,
decision log 2026-11-18 18:40. Không tiến trình nền nào chạy.

Owner chốt: ICCIES CHƯA NỘP, chỉ làm một bài. Yêu cầu của thầy ở `Review Huy.docx` (root, không commit): (1) cấp quyền theo
ý định + luồng mức giá trị, (2) mô hình hình thức, tách điều chứng minh và điều chỉ kiểm thực nghiệm, (3) tấn công thích
nghi biết luật + đánh đổi an ninh/tiện ích/chi phí, so với BrokerGuard gốc và baseline; phân biệt với CaMeL/CapLite.

Việc của phiên này:
1. Viết bài: đóng góp chính là cơ chế v3 (C1–C3) + mô hình hình thức; v1 trình bày như biến thể luật chuỗi (bậc ablation),
   vẫn so sánh. Báo H1 trung thực. Mô hình hình thức sang LaTeX (mệnh đề toàn vẹn không bao gồm sửa số/đơn vị), bảng Test-4,
   chi phí, bằng chứng cơ chế, CaMeL/CapLite. Số chỉ lấy từ decision log và facts.md (cập nhật facts trước khi viết số).
   Văn phong khách quan, không "chúng tôi".
2. Vòng tấn công thích nghi nhắm v3 trên họ Dev-val: owner/Minh soạn, Claude chỉ hạ tầng.
3. Không chỉnh v3 hay chạy lại theo số Test-4; không thêm Gemini để tìm ý nghĩa (nếu chạy thì chỉ là phân tích phụ, cần
   quyết định ghi trước trong decision log).

Claude không viết, đọc hay giao việc viết văn bản/prompt tấn công hay nội dung Test; chỉ hạ tầng, số đếm và biên soạn.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
