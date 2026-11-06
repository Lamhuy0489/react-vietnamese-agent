# Study 2: đóng góp nghiên cứu (bản nháp cho luận văn và bài báo)

Cập nhật: 2026-11-06. Số liệu là Dev vòng 1 (decision log 06/11 "WP7: kết quả Dev v3 vòng 1"); kết luận chính thức chờ Test v3 chạy một lần.

## Vấn đề
Benchmark prompt injection cho agent (AgentDojo, InjecAgent, ASB) và các phòng thủ (Prompt Guard, MELON, spotlighting,
SecAlign) gần như chỉ đánh giá trên tiếng Anh. Agent tiếng Việt đọc email/tài liệu/web tiếng Việt chưa có cách đo.

## Đóng góp
1. **VN-AgentInject v3**: benchmark tấn công gián tiếp tiếng Việt cho agent dùng công cụ.
   - 6 cơ chế M1–M6, nên chỉ ra phòng thủ hở ở cơ chế nào.
   - 5 biến thể: canonical, paraphrase, no_diacritic, code_mix, english.
   - Cặp benign_plain và benign_auth để đo cả chặn nhầm.
   - Pilot 12, Dev 48, Test 72 family.
2. **Chấm theo hậu quả thực thi**: side-effect (gửi, ghi DB, lộ dữ liệu) và tamper M5, không chấm theo lời văn.
3. **Bằng chứng thực nghiệm** (Dev, 3 backbone × 9 cấu hình × 560 lượt):
   - Prompt Guard 2 và MELON gần như bằng A0 trên tiếng Việt.
   - Spotlighting có thể phản tác dụng: Qwen3.5 tăng từ 40 lên 43 family.
   - Sandwich và D2+P1 giảm hại mạnh nhất.
   - M3–M5 lọt qua mọi phòng thủ.
   - D2 đổi utility benign_auth lấy an toàn.
4. **AgentDojo-VI** (Banking, Slack): dùng nguyên bộ chấm gốc qua bảng tương đương, ground truth 100%.
   So EN với VI trực tiếp; utility Llama gần bằng nhau.

## Câu đóng góp (nháp)
"Chúng tôi xây dựng VN-AgentInject, benchmark tấn công prompt injection gián tiếp đầu tiên cho agent tiếng Việt, phân
loại theo cơ chế và chấm theo hậu quả thực thi, cùng AgentDojo-VI; các phòng thủ phổ biến như Prompt Guard 2 và MELON
gần như mất tác dụng trên tiếng Việt, và một số cơ chế lọt qua mọi phòng thủ hiện có."

## Hạn chế phải nêu
- Số Dev chưa có CI; kết luận cần Test (một lần, bootstrap theo family, McNemar).
- Dữ liệu tổng hợp, môi trường mô phỏng trường đại học, model 8–12B.
- Llama có nhiều OUTPUT_TRUNCATED, tính là thất bại, nên utility thấp.
- Test v3 phải do người viết; nếu có dùng công cụ AI thì ghi rõ trong decision log.
