# Phase 5 — runtime A0/A1 đã tích hợp

## Hiện hành

Source `d2ec2d5`, [receipt](../experiments/manifests/phase5_runtime_v1_validation01.json),
[contract runtime](../docs/architecture/phase5_runtime_contract.md).
366 tests pass (66 mới), setup/Ruff/mypy 170 files pass. 20 smoke exact A0 parity
pairs với Phase 4 + 24 synthetic A0/A1 conditions, 64 fresh Replay. 655 artifacts
trong các run Phase 5, sáu denials đúng micro-case expectations; không diễn giải
6/12 thành benchmark ASR. 120 source và 369 raw hashes khớp; 270 prior hash entries
giữ nguyên. Stable summary khớp preflight. Không benchmark Dev/Test inference.

Vòng ReAct chung đã có actual context/model/argument/final lineage. Policy denial
không gọi Broker, không tạo ToolResult/call ID giả; phản hồi chính sách có artifact
và các parent liên quan. Lặp denial tiêu thụ step budget; parse retry tiếp tục đúng
context. Detector lỗi ghi class-only, read-open/external-closed; final A0/A1 vẫn
pass-through, không giả A6. Có validator thứ tự proposal/pre/denied-or-call/post/final.
Runtime chỉ hỗ trợ A0/A1 và từ chối A2–A6 trước khi tạo output.

Tiếp theo: grouped Dev tune/validation trước tuning; chốt guard model/revision và
bounded inference, tích hợp A2; session enforcement A3–A5 rồi value-origin A6.
Không sửa các module/config/receipt đã hash; thêm version tiếp theo. Rules/anchors
chưa được tune trên benchmark, giữ giới hạn lexical/JSON-escape và grammar đã ghi.
Không cần tài khoản mới cho local implementation; chưa có guard model run thật.

## Lịch sử: mốc component đầu tiên

Owner authorized 2026-09-07. Source `4bddd23`,
[receipt](../experiments/manifests/phase5_components_v1_validation01.json),
[contract](../docs/architecture/phase5_policy_contract.md).

Đã triển khai bảy config cumulative strict, decision/reason/stage enums và public
observation schemas từ chối GT fields. A1 scan raw + normalized detector view,
post TAG và pre deny external sau signal nếu thiếu user destination authorization.
Adapter A0/A1 gọi Tool Broker cho mọi call được phép; deny không tạo ToolResult giả.
Raw user anchors có grammar giới hạn; không lấy addresses trong nguồn truy xuất.
A2 mới có backend interface, prompt/parser/cache và fail-open read/fail-closed sink.
Không dùng fake/Replay guard để tuyên bố chất lượng LLM.

300 tests pass, gồm 56 micro-tests mới; setup/Ruff/mypy 166 files pass.
Validator kiểm tra 153 Phase 4 source hashes, hai seals/hash-only Test và bảy config
hashes. Không benchmark Dev run, Test parsing hoặc model inference. Các source
đã chọn tiếp tục bất biến; thay đổi sau milestone cần module/version kế tiếp.

Tiếp theo:

1. Shared ReAct runtime riêng cho Phase 5: gắn policy ở Pre/Post/Final, giữ đầy đủ
   raw model output/context lineage, proposed/executed distinction và A0 parity.
2. Chốt guard model/revision dùng chung A2–A6, bounded timeout/cancellation thực,
   tích hợp A2. Hiện backend adapter chỉ xử lý TimeoutError, chưa tự ngắt inference.
3. Session sensitivity/trust/A5 và value-origin A6, unknown critical deny/final protection.
4. Chia grouped Dev tune/validation theo protocol trước tuning; không mở Test.
5. Differential utility/security QA rồi freeze theo 20 DoD; không lấy config count
   làm tỷ lệ hoàn thành hoặc claim A1/A2 đã end-to-end qua agent loop.

Giới hạn: lexical detector có false positives khi trích dẫn hướng dẫn; anchor parser
không hiểu mọi câu tiếng Việt. Adapter hiện chỉ host-proposal lineage, không phải
runner để đánh giá LLM. Không thay điểm pilot cũ; Meta access vẫn là việc pilot riêng.
