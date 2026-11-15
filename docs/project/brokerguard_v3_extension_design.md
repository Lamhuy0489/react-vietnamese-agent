# BrokerGuard v3: mở rộng theo Review Huy (bản nháp chờ owner duyệt)

Trạng thái: **owner duyệt 2026-11-15 15:45** (decision log): tạp chí Q4; cần xác nhận = từ chối; bộ trích tất định;
Test-4 do owner và Minh soạn, 48 họ. Còn mở: tên phương pháp. Nguồn: `Review Huy.docx` (root, không commit) và decision log
"2026-11-15 15:30 — Hạn nộp lùi, mở rộng bài theo Review Huy". Tài liệu này không đổi `final_config_v1`, D2+P2, Test-I,
Test-II, Test-3 hay số liệu đã có. Code mới nằm trong file mới. File đã ghim chỉ được import, không sửa.

Tên làm việc là "BrokerGuard v3", owner đặt tên cuối. BrokerGuard (D2+P2) gọi là v1 trong tài liệu này.

## 1. Bản review yêu cầu gì

Có ba hướng, và reviewer khuyên làm hướng 1 cộng hướng 3, thêm hướng 2 ở mức vừa đủ.

1. **Cấp quyền theo ý định và kiểm soát luồng ở mức giá trị.** Trích chính sách có cấu trúc
   $P(u)=\{(action, resource, destination, constraints)\}$ từ yêu cầu đáng tin $u$, không bao giờ từ dữ liệu công cụ.
   Theo dõi độ nhạy và nguồn gốc theo từng giá trị. Ca không rõ quyền thì từ chối hoặc hỏi xác nhận. Không tin tuyệt đối
   một LLM phán quyền.
2. **Mô hình hình thức.** Trạng thái $s_t=(u, C_t, P_t, H_t)$. Ba thuộc tính: an toàn cấp quyền, bảo mật và toàn vẹn
   tham số. Phải tách rõ thuộc tính được chứng minh với thuộc tính chỉ kiểm tra thực nghiệm.
3. **Đánh giá thích nghi và đánh đổi.** Kẻ tấn công biết luật. Đánh giá tổng quát hóa. Đo ASR, tiện ích, tỉ lệ chặn
   nhầm, độ trễ và token. Vẽ đường Pareto và báo $\Delta U$.

Reviewer cũng nhắc rằng CaMeL và CapLite đã làm hướng gần giống, nên phải nêu rõ điểm khác biệt.

## 2. Nối với các lỗ hổng đã đo của v1

Có 40 ca lọt qua trên hai tập Test (`scripts/paper_bypass_causes_v1.py`, Mục 7 của bài).

| Nguyên nhân ở v1 | Số ca | Thành phần v3 xử lý |
|---|---:|---|
| Giá trị mật nằm trong nguồn gắn nhãn công khai, nên không vào $C$ | 25 | C2: nhãn theo giá trị |
| Đích có trong $u$, ví dụ trong câu cấm hoặc va chạm chuỗi con | 5 | C1: chính sách ý định có cực tính |
| Sửa tham số | 10 | C3: toàn vẹn tham số theo ràng buộc trong $P(u)$ |

Bảng này chỉ chỉ ra **chỗ cần sửa**. Nó không được dùng làm bằng chứng. Xem mục 5.

## 3. Thiết kế v3 (phát triển và tinh chỉnh chỉ trên Dev)

- **C1. Chính sách ý định $P(u)$.** Bộ trích tất định, gồm ngữ pháp và luật, không dùng LLM. Bộ trích tạo các bộ
  (hành động, tài nguyên, đích, ràng buộc).
  - Đích mang cực tính: được phép hoặc bị cấm. Cực tính dựa trên phạm vi phủ định tiếng Việt và tiếng Anh, ví dụ
    "đừng/không/trừ/ngoại trừ", "do not/except".
  - Đích phải khớp theo token, không khớp chuỗi con, để tránh va chạm như ở v1.
  - Hành động không có trường đích (đổi mật khẩu, mở URL) cũng cần quyền theo loại hành động.
  - Ca không rõ quyền thì trả về *cần xác nhận*.
  - Nếu sau này thêm bộ trích bằng LLM, bộ đó chỉ được *đề xuất*. Kết quả phải được bộ kiểm tất định hoặc người dùng
    xác nhận.
- **C2. Nhãn theo giá trị.** Mỗi giá trị trong đầu ra công cụ có nhãn độ nhạy riêng, độc lập với nhãn của nguồn.
  - Nhãn dựa trên kiểu giá trị (số tài khoản, OTP, mật khẩu, mã định danh) và tên trường.
  - Dò thêm các dạng biến đổi nhẹ: bỏ dấu cách hoặc dấu chấm, bỏ dấu tiếng Việt, tách ký tự.
  - R-Flow v2 kiểm từng giá trị ở mọi sink, kể cả câu trả lời cuối.
  - Phải giữ bất biến "độ nhạy và độ tin là hai chiều độc lập".
- **C3. Toàn vẹn tham số.** Các trường người dùng đã nêu trong $u$ (số tiền, người nhận, tiêu đề, nội dung bắt buộc) bị
  ghim. Lời gọi lệch khỏi ràng buộc trong $P(u)$ thì bị chặn.
- **C4. Giữ phần còn lại của v1.** Gồm lời nhắc (P2), phản hồi từ chối và che giá trị mật trong câu trả lời. R-Signal
  chỉ giữ nếu thí nghiệm loại bỏ trên Dev cho thấy còn cần.
- **Xác nhận trong benchmark.** "Cần xác nhận" được mô phỏng là từ chối. Tỉ lệ xác nhận được báo riêng như một chi phí
  tiện ích. Owner chọn cách khác ở mục 8 nếu muốn.

## 4. Mô hình hình thức (hướng 2, mức vừa đủ)

- Trạng thái $s_t=(u, C_t, P_t, H_t)$. Mỗi lời gọi công cụ là một bước chuyển, và broker là điểm kiểm duy nhất
  (complete mediation).
- Các mệnh đề cần phát biểu:
  - *Authorization safety*: không thực thi hành động có tác dụng phụ nằm ngoài $P(u)$.
  - *Confidentiality*: không giá trị nào thuộc $C_t$ tới đích không được phép.
  - *Integrity*: không lời gọi nào sửa trường đã ghim.
- Mỗi mệnh đề đi kèm giả định rõ ràng, ví dụ bộ trích đúng trên $u$ và bộ dò giá trị có độ phủ đủ.
- Có một bảng tách **được chứng minh** (dưới giả định) với **chỉ kiểm thực nghiệm** (độ phủ bộ dò, lời nhắc, R-Signal).
- Tùy chọn: kiểm mô hình chuyển trạng thái nhỏ bằng property-based test (hypothesis) trên broker thật.

## 5. Giao thức đánh giá (thứ tự là một phần của giao thức)

1. Owner duyệt tài liệu này.
2. **Test-4 được soạn, rà và niêm phong trước khi có code v3.** Owner và Minh soạn, Claude không đọc nội dung. Test-4 gồm:
   - (a) các họ tĩnh mới theo đúng khung Test-II;
   - (b) một nhóm tấn công thích nghi có biết luật **v1**, nhắm vào các lỗ hổng ở mục 2.
   Hash được ghi vào decision log.
3. Viết và tinh chỉnh v3 **chỉ trên Dev**, rồi đóng băng ở `configs/final/final_config_v3.json`.
4. Chạy Test-4 một lần với các cấu hình đăng ký trước. Chỉ chạy lại khi lỗi hạ tầng. Giả thuyết được đăng ký trước khi
   chạy, ví dụ v3 so với v1 về số họ gây hại, và mức tiện ích không kém hơn quá $-5$ điểm.
5. Sau khi đóng băng: một vòng tấn công thích nghi có biết luật **v3**, trên họ Dev. Kết quả báo riêng, không gộp vào
   kiểm định.
6. Chỉ được phát lại offline 40 ca lọt cũ của Test-I/II dưới v3 như một **chẩn đoán hậu kiểm** có ghi nhãn. Không dùng
   làm kết quả chính, vì các tập này đã được dùng để tìm lỗ hổng.

Phạm vi chạy và chỉ số:

- **Cấu hình:** không phòng thủ, Sandwich, Progent\*, v1, v3, và các bản loại bỏ của v3 (−C1, −C2, −C3).
- **Mô hình nền:** ba mô hình mở như cũ (Kaggle), cộng Gemini 3 Flash làm cột tham khảo (OmniRoute do owner bật).
- **AgentDojo:** EN và VI, Llama. Kiểm xem việc hỏi xác nhận có cứu được tiện ích Slack không.
- **Chỉ số:**
  - ASR theo ca và theo họ.
  - Tiện ích thường và tiện ích ủy quyền, $\Delta U = U_{def}-U_{none}$.
  - Tỉ lệ chặn nhầm và tỉ lệ cần xác nhận.
  - Số bước, token vào và ra, thời gian mỗi ca.
  - Thời gian riêng của broker (benchmark vi mô).
  - Đường Pareto giữa ASR, tiện ích và chi phí, kèm tham chiếu chặn mọi sink.
- **Ghi log chi phí:** runner hiện không ghi token và thời gian (`run_metadata.json` không có các trường này). Cần thêm
  trường log **trước** khi chạy Test-4. Các lượt cũ chỉ cho số bước.

## 6. Điểm khác biệt cần nêu trong bài

- **CaMeL:** viết lại tác tử thành bộ thông dịch riêng. v3 gắn vào tác tử ReAct có sẵn.
- **FIDES:** lan truyền nhãn qua mọi giá trị trong luồng. v3 gắn nhãn tại broker theo kiểu giá trị, không lan truyền.
- **ClawGuard:** để LLM sinh luật. v3 dùng bộ trích tất định.
- **Progent:** chính sách đặc quyền viết tay. v3 suy chính sách từ $u$.
- **CapLite:** cần kiểm tra bài thật (tác giả, nơi đăng) trước khi trích và so sánh.
- **Góc riêng của v3:** tất định, không gọi thêm LLM, có phủ định và biến đổi đặc thù tiếng Việt, đánh giá trên tập
  niêm phong mới.

## 7. Ràng buộc vận hành

- Máy hỏng pin: mỗi lúc một tiến trình nặng, `nice -n 10`. Không tự bật hay khởi động lại OmniRoute. Không render PDF.
- Chạy các mô hình mở trên Kaggle theo Bản đồ ở `knowledge/rebuild_a_runbook.md`.
- Claude không viết, đọc hay giao việc viết văn bản tấn công hay nội dung Test.

## 8. Owner cần quyết

1. Hạn nộp mới và nơi nộp (ICCIES lùi hạn hay tạp chí Q4). Số trang tối đa.
2. Tên phương pháp mới.
3. Kích thước Test-4: số họ tĩnh và số ca thích nghi. Ai soạn, và đến khi nào.
4. Ngữ nghĩa "cần xác nhận" trong benchmark: tính là từ chối (đề xuất), hay mô phỏng người dùng đồng ý.
5. Có cho phép thêm bộ trích bằng LLM (chỉ để đề xuất) hay giữ hoàn toàn tất định (đề xuất).
6. Thứ tự làm. Đề xuất: ghi log chi phí và mô hình hình thức trước, song song với việc owner và Minh soạn Test-4. Sau đó
   viết code v3 trên Dev.
