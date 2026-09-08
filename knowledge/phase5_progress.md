# Phase 5 — Task-local warm guard/runtime v5

## Hiện hành

[Warm guard/runtime v5](../docs/architecture/phase5_warm_guard_contract.md) đã qua preflight:
model load một lần/task, bounded JSON IPC, cold/warm timing riêng và deadline
tính đủ cold load. Không cache/worker xuyên task, không tự restart/retry. Worker
lỗi hoặc guard output invalid bị loại, cache xóa. V5 close ở terminal và exception.
Preflight01: **891 tests pass**, 46 mới; setup/Ruff/mypy 194 files/knowledge pass.
22 cold/warm pairs = 44 Replay + chín lifecycle conditions; 140 mock Broker calls,
240 fake runtime guard classifications. 138 source/370 raw hashes kiểm lại,
1.038 prior entries giữ nguyên. Paired worker starts 53 cold → 18 warm, không GPU
throughput claim. Chưa selected receipt/Phase 5 acceptance. A6 Post source IDs chỉ được đối chiếu
qua source binding; context gốc vẫn lưu nguyên. Chưa guard/model/GPU thật.

## Lịch sử: A6 runtime v4

Runtime v4 A0–A6 theo [contract](../docs/architecture/phase5_a6_runtime_contract.md)
đã qua preflight01: **845 tests pass** (76 mới), setup/Ruff/mypy 190 files/knowledge
pass. 26 synthetic conditions + 12 A0–A5 parity pairs = 50 Replay, 56 Broker mock
calls, 121 fake guard classifications. 135 source/435 raw hashes kiểm lại,
903 prior source entries giữ nguyên.
[Selected reproduction](../experiments/manifests/phase5_a6_runtime_v1_validation01.json)
từ source sạch `04ae4c8` khớp preflight, 845 tests pass trong 178,29 giây;
135 source/435 raw hashes kiểm lại. 25 A6 finals: 23 ALLOW/1 REDACT/1 DENY;
một A5 final pass-through. Đây là predeclared synthetic conditions, không ASR.
Coarse verdict/value/composed verdict lưu riêng; chỉ thay coarse sensitivity
veto khi đủ nguồn public. Guard/control veto không bị vượt qua. Actual Post view
vào context; final proposed/released tách biệt và chỉ released text được trả ra.
Không sửa source đã hash, không dùng Test hoặc chạy model thật.
Guard production/revision/GPU lifecycle, A4 scope, grouped Dev validation/freeze
và general final entitlements vẫn chưa hoàn tất; không nghiệm thu Phase 5.

## Lịch sử: value PreGate/Post-view components

PreGate component nhận host user/proposal artifacts, yêu cầu exact raw-user anchors
và origin của critical leaves; protected/unknown/coverage failures chặn external.
Kiểm tra hai chiều index↔exposure để không bỏ sót nguồn S2 hoặc dùng public chưa
được thấy. Post-view giữ raw và nhãn, dùng JSON data envelope cho untrusted source.
[Contract](../docs/architecture/phase5_value_gates_contract.md).

Preflight02: **769 tests pass**, 73 mới; setup/Ruff/mypy 186 files/knowledge pass.
24 Pre cases (4 ALLOW/20 DENY) + sáu Post cases; bốn Broker mock calls, zero model/
guard/Replay runs. 771 prior source entries nguyên vẹn, 132 source/121 raw hashes
đã kiểm lại. [Selected reproduction](../experiments/manifests/phase5_value_gates_v1_validation02.json)
từ source sạch `a3743a2` khớp preflight; 769 tests pass trong 138,14 giây.
Preflight01 source-changed bị loại. Validation01 gián đoạn trước receipt; giữ
nguyên thư mục và chạy validation02 mới, không ghi đè hoặc chọn kết quả từng ca.

Vẫn chưa runtime A6: phải kết hợp guard/control risks, arbitration coarse session,
critical-field bindings, Post context và released-final accounting/authorization.
Không coi value ALLOW là full A6 ALLOW. Còn guard thật/GPU lifecycle, A4 scope và
grouped Dev validation. Không ASR/utility claim hoặc Test payload parsing.

## Lịch sử: value-origin/final-release

Source `3b9f565`: [component contract](../docs/architecture/phase5_value_origin_contract.md)
cho typed origin index và deterministic final release. Đây là phần nền A6, chưa
bật A6 runtime hoặc thay A0–A5. Index chỉ nhận raw roots do host quan sát, giữ mọi
nguồn trùng giá trị và nhãn sensitivity/trust độc lập; hỗ trợ DB columns/rows,
numeric equivalence có giới hạn, kiểm soát tài nguyên và admission atomic.
Final mới liên kết proposal/nguồn, raw và nhãn gốc giữ nguyên. Normalized-only hit,
scan failure hoặc protected value chuẩn hóa thành rỗng dẫn tới DENY.

Preflight **696 tests pass** (103 mới), setup/Ruff/mypy 183 files/knowledge pass.
24 synthetic conditions: 12 ALLOW, 8 REDACT, 4 DENY; không fresh Replay hoặc guard
classification. 130 source/101 raw hashes ghi, 641 prior source entries nguyên vẹn.
[Selected reproduction](../experiments/manifests/phase5_value_origin_v1_validation01.json)
từ commit sạch khớp stable preflight, 696 tests pass; 130 source/101 raw hashes
đã kiểm lại. Kiểm tra riêng serialized artifacts đã đối chiếu
ID/hash/labels/proposed/released cho cả 24 ca.

Không benchmark Dev tuning/Test parsing hoặc model inference. ALLOW chỉ là không
khớp profile hiện hành; không chứng minh không có rò rỉ ngữ nghĩa/encoded/paraphrase.
Final authorization và unknown critical relations cần runtime policy riêng, không GT.
Tiếp theo: A6 Pre/Post/Final/veto arbitration, A4 general processing scope, guard
production/revision/GPU lifecycle và grouped Dev protocol. Phase 5 chưa nghiệm thu.

## Lịch sử: A3–A5 session runtime

Runtime v3 hỗ trợ A0–A5 với policy cumulative, không tạo ablation ngầm. A3 chặn
external sau S1/S2; A4 thêm authorization raw-user sau untrusted; A5 thêm joint
rule/LLM SUSPICIOUS/MALICIOUS/error veto. Session snapshot riêng từng task, không
vào agent prompt; zero-call có guard trace rỗng. [Contract](../docs/architecture/phase5_session_contract.md).

Preflight **593 tests pass** (147 mới), setup/Ruff/mypy 179 files/knowledge pass.
44 exact A0–A2 pairs + 30 session conditions = 118 fresh Replay. Riêng session
matrix: 165 fake guard classifications, 225 snapshots, 15 expected denials.
127 source/780 raw hashes đã kiểm, 514 prior source entries nguyên vẹn. Source
`8a4ca3d`, [selected receipt](../experiments/manifests/phase5_session_v1_validation01.json)
khớp stable preflight, 593 tests pass. Đây không phải ASR hoặc model quality.

Còn A4 general processing scope ngoài grammar external anchors; A6 value-origin,
Post/Final; guard LLM thật/revision/GPU lifecycle; grouped Dev validation/freeze.
Coarse policy chủ động overblock unrelated S0 sau S1/S2; final chưa leak protection.
Không Dev tuning/Test payload parsing, không đổi điểm pilot, chưa nghiệm thu Phase 5.

## Lịch sử: A2 process guard

Preflight A2 v2: **446 tests pass** (80 mới), setup/Ruff/mypy 175 files pass.
40 exact smoke pairs A0/A1 đối chiếu v1 + chín A2 synthetic trajectories = 89
fresh Replay, 31 fake guard classifications. Validator kiểm tra source/action/
proposal linkage, cache identity, error/result schema, counters và worker reap.
124 source/548 raw hashes ghi trong preflight, 390 prior source entries bất biến.
Selected source `15ed921`, [receipt](../experiments/manifests/phase5_a2_v2_validation01.json)
khớp preflight; toàn bộ source/raw hashes kiểm lại thành công.

Đã có A2 Pre/Post trong ReAct, cumulative A1, sticky MALICIOUS/error external veto,
read-open, SUSPICIOUS tagging, final pass-through. Guard inference riêng process;
timeout thực + terminate/kill/reap, failure retirement, fresh task cache, typed
output và cold end-to-end latency. [Contract](../docs/architecture/phase5_a2_runtime_contract.md).

**Chưa xong Phase 5:** chốt guard thật/revision cố định A2–A6 và worker GPU hiệu quả,
A3–A5 session enforcement, A6 value-origin/Post/Final, grouped Dev validation.
Cold process mỗi cache miss chưa phù hợp đo warm throughput. Chưa có model-quality
evidence hoặc benchmark Dev/Test run mới. Quy tắc/cache đã khóa không tune theo Test.

## Lịch sử: runtime A0/A1

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
