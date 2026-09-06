# Phase 3: tiến độ và thiếu sót đã xác minh

Cập nhật 2026-09-06. Trạng thái: **draft chưa đủ điều kiện nghiệm thu**.
Đây là audit tĩnh để tiếp tục authoring, không phải đánh giá ASR hay chọn model.

## Mốc đã làm trong lượt này

- Siết validator: mã scenario/pair duy nhất, năm loại variant đúng và không
  lặp, quota từng split, nội dung không rỗng, attack/benign khớp source và
  authorization. Thêm negative tests cho lỗi vẫn giữ nguyên tổng số dòng.
- Thêm auditor v1 báo cáo category distribution, template overlap, lỗi surface,
  target webhook, annotation benign và những DoD chưa có bằng chứng thực thi.
- Lưu [audit receipt](../experiments/manifests/phase3_draft_audit_20260906.json):
  hash bảy input files và ba file mã auditor; không chép payload Test vào memory.
- Thêm helper [surface drafts](../src/react_agent/authoring/surfaces.py):
  bỏ dấu cả `đ/Đ`, chèn zero-width không xóa khoảng trắng, word-boundary có
  kiểm soát; giữ nguyên tool/email/endpoint và literal được bảo vệ. No-op bị
  từ chối. Có visible debug Unicode và trạng thái `pending`, không giả review.
- Helper chưa áp dụng lên dataset. Code-mix/paraphrase cần author/review riêng;
  không tự tạo hàng trăm dòng bằng đổi vài từ rồi gọi là reviewed.

## Kết quả audit bản v1 hiện có

Counts và manifest v1 vẫn khớp: 70 canonical attacks, 350 attack variants,
350 benign variants; mã family 40 Dev/30 Test không xuyên split. Tuy nhiên:

- Sau chuẩn hóa số/địa chỉ, cả 70 malicious payload cùng một template. Đây
  là tín hiệu trùng mẫu để review, không phải bằng chứng tuyệt đối rằng mọi
  khía cạnh của các scenario đều giống nhau.
- Dev thiếu `policy_violation`; Test thiếu `indirect_injection` và
  `tool_output_poisoning`. Split theo thứ tự category chưa đủ stratification.
- 35 canonical target webhook không có endpoint đúng kiểu, dùng recipient email.
- 20 canonical exfiltration chưa tham chiếu sensitive artifact cụ thể.
- 70 canonical benign vẫn mang attack-success annotation của bản attack.
- Bỏ dấu chưa xử lý `đ`; zero-width của attack còn xóa khoảng trắng gốc.
  Bốn loại surface ở benign giữ nguyên payload ở cả 70 family.
- Chưa có overlays, mappings, reviews và bộ freeze hoàn chỉnh. Có tên source
  trong JSON không chứng minh agent đọc được poisoned content, safe path tồn
  tại hoặc oracle phân biệt proposed/executed/final leakage.

`make phase3-audit` trả mã lỗi có chủ đích: dataset **NOT ACCEPTED**, không phải
crash công cụ. Kể cả tạo thư mục trống cũng không khiến auditor cấp acceptance;
nó không triển khai/certify các gate semantic và executable.

## Thứ tự tiếp tục

1. Chốt schema typed public task / overlay / private GT / review receipt riêng;
   không đưa prohibited-action GT vào prompt hay public worker task.
2. Author canonical + benign pair bằng synthetic executable fixtures, bao phủ
   bốn source và các sink: email, webhook, final answer; có benign external
   action được user cho phép để đo overblocking.
3. Chạy safe path qua Broker và negative violation fixtures; kiểm tra artifact
   reference thực sự tồn tại, không network I/O, không dùng LLM để lọc attack.
4. Review semantic units và nhóm template trước stratified 40/30 split; không
   sửa/move các family trong v1 tại chỗ. Dùng version authoring mới và giữ
   nguyên receipt v1. Không dùng điểm pilot clean để thiết kế attack.
5. Chỉ sau canonical/pair QA mới tạo năm surface variants; review thủ công
   nội dung theo nghĩa vẫn là việc cần làm, không được giả reviewer. Owner
   waiver bỏ peer review độc lập phải được ghi rõ, không biến thành chứng nhận
   human semantic review.
6. Hoàn thiện executable QA, mappings, hashes, data card và acceptance. Chưa
   chuyển sang defense Phase 4–5 hoặc chạy held-out Test.

## Không thay đổi

Bản draft v1 và clean_v1/v1.1 giữ nguyên bytes. Measured Gemma/Qwen release
giữ nguyên hash/điểm. Audit đọc hai split draft cho integrity, không chạy model,
không điều chỉnh prompt/policy theo Test và không phát sinh lượt Kaggle mới.
