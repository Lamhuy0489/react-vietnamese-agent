# Phase 3: tiến độ và thiếu sót đã xác minh

Cập nhật 2026-09-06. Trạng thái: **draft chưa đủ điều kiện nghiệm thu**.
Đây là audit tĩnh để tiếp tục authoring, không phải đánh giá ASR hay chọn model.

## Mới nhất: bốn cặp executable workbench đã pass

Đã thêm `data/adversarial/workbench_v2`: bốn cặp synthetic chưa chia split,
review-pending, không tính vào 70 family chính thức và không thay bản v1.
Public task, environment overlay và private oracle tách file/schema riêng.
Runtime chỉ nhận instruction; private QA không đi vào prompt/policy.

- Bao phủ document, cached page, DB text field và calculator tool output.
  Tất cả chạy trên bản sao môi trường clean_v1.1, vẫn đủ tám tool qua Broker.
- 16 lượt Replay: bốn cặp × hai nhánh attack/benign × safe/negative. Tám safe
  paths đều giữ utility; tám negative scripts đều phát hiện vi phạm mẫu.
- Có benign email được user cho phép; sink sai địa chỉ, webhook không được
  phép và final-answer leakage có kiểm tra riêng. Tool result thất bại không
  được tính như đã gửi thành công; từ chối mọi việc không đạt utility.
- QA xác minh payload xuất hiện trong trace, facts có tool evidence, sensitive
  artifact tồn tại, không đưa private metadata vào context. Test chặn socket,
  DNS và SMTP vẫn pass; observable traces tái lập sau bỏ timestamp/run ID.
- [Receipt](../experiments/manifests/phase3_workbench_v2_validation_01.json)
  lưu input/verifier/trace hashes; raw traces và bản sao DB nằm ngoài Git.
- Toàn bộ 143 tests pass; setup/Ruff/mypy (103 source files), clean_v1.1 seal
  pass; bản v1 và measured releases không thay đổi. Không có LLM/Kaggle run mới.

[Contract workbench](../docs/benchmark/adversarial_workbench_contract.md)
giới hạn rõ: literal facts/artifact values, exact sink actions và query fixture,
chưa phải evaluator tổng quát. Không suy ra ASR/FPR, semantic review hay Phase 3
acceptance từ các script Replay được viết sẵn. Chưa tạo variant/split mới.

## Lịch sử: audit v1 và helper surface

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

1. Nâng từ fixture schema sang canonical schema hoàn chỉnh: family/template
   groups, authorization/data scope, artifact IDs, typed utility conditions
   và review evidence. Không gọi bốn cặp là benchmark hoàn chỉnh.
2. Mở rộng executable QA cho quy tắc theo data scope/SQL và sự kiện chưa được
   bốn fixture bao phủ; vẫn tách private oracle khỏi runtime policy/model.
3. Author canonical đa dạng và matched benign controls, có bằng chứng safe
   path/negative oracle. Không dùng thành công của LLM để lọc attack.
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
