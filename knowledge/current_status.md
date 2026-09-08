# Trạng thái hiện tại

## Hiện hành: guard HF adapter qua CPU preflight — 2026-09-08

Thêm adapter riêng, không sửa runtime/policy/source đã khóa. Snapshot pin gồm
HF revision và hash/size mọi file; native local-only Qwen2, FP16/single GPU,
allocator budget riêng trong guard subprocess. Fresh messages/generation config/
dynamic cache mỗi call; không truncation, lỗi retire. Metrics không lưu prompt/
response/exception text. [Contract](../docs/architecture/phase5_guard_hf_contract.md).
Preflight01: **942 tests pass** (51 CPU fake tests mới), 228,00 giây; setup/Ruff/
mypy 197 files/knowledge pass. 134 source hashes, 1.176 prior source entries
nguyên vẹn; selected clean-source reproduction là bước kế tiếp.
[Nguồn ứng viên](guard_model_preflight_evidence.md): Qwen2.5-1.5B-Instruct,
HF revision đã xác minh tồn tại, chưa tải/xác thực weights hoặc chốt guard luận văn.
Chưa GPU/coexistence/statelessness thật; không benchmark Dev/Test hoặc thay điểm cũ.
Phase 5 chưa nghiệm thu. [Bước tiếp theo](handoff.md).

## Lịch sử: warm guard/runtime v5 đã tái lập — 2026-09-08

Worker mới tải backend một lần trong mỗi task, tái dùng giữa các request; không
chia sẻ worker/cache giữa tasks. Deadline tính cả cold load; lỗi/timeout/identity
drift/invalid guard JSON loại worker và cache, có close/terminate/kill/reap.
Runtime v5 sở hữu worker bằng try/finally. [Contract](../docs/architecture/phase5_warm_guard_contract.md).
Preflight01 valid: **891 tests pass**, 46 mới, trong 226,45 giây; setup/Ruff/mypy
194 files/knowledge pass. 22 cold/warm pairs = 44 Replay, chín lifecycle conditions,
140 mock Broker calls và 240 fake guard classifications trong runtime matrix.
138 source/370 raw hashes kiểm lại, 1.038 prior source entries nguyên vẹn.
Trong paired runs, worker process starts 53 cold → 18 warm; không phải GPU speedup.
[Selected receipt](../experiments/manifests/phase5_warm_guard_v1_validation01.json)
từ source sạch `2300751` khớp preflight: **891 tests pass** trong 225,80 giây;
138 source/370 raw hashes kiểm lại, số worker starts vẫn 53/18.
Tiếp theo là guard model/revision, adapter GPU có memory budgets riêng và kiểm
statelessness/VRAM khi chạy đồng thời agent. Chưa nghiệm thu Phase 5.
Không model/GPU/Kaggle hoặc Test payload; giữ nguyên source v4 đã khóa.

## Lịch sử: A6 runtime integration đã tái lập

Runtime v4 nối Pre/value/guard composition, Post context view và Final release.
[Contract](../docs/architecture/phase5_a6_runtime_contract.md). A0–A5 giữ hành vi
cũ; A6 chỉ gỡ coarse sensitivity veto khi value ALLOW, không gỡ rule/LLM veto.
Final clearance cố định S0, không tự cấp quyền dữ liệu riêng; trả released text.
`phase5_a6_runtime_v1_preflight01` đạt: **845 tests pass**, 76 mới, trong 178,13 giây;
setup/Ruff/mypy 190 files/knowledge pass. 26 synthetic conditions + 12 parity pairs
= 50 Replay, 56 Broker mock calls, 121 fake guard classifications. 135 source/435
raw hashes đã kiểm lại, 903 prior source entries và hai seals giữ nguyên.
[Selected receipt](../experiments/manifests/phase5_a6_runtime_v1_validation01.json)
từ source sạch `04ae4c8` khớp preflight; 845 tests pass trong 178,29 giây,
135 source/435 raw hashes đã kiểm lại. Không đọc payload Test hoặc chạy model thật.
Tiếp theo: guard worker dùng lại model với timeout/identity/cancellation an toàn,
chốt model/revision, rồi grouped Dev validation và rà A4 scope. Phase 5 chưa xong.

## Lịch sử: A6 value PreGate/Post-view components

PreGate mới kiểm tra quyền raw-user, nguồn typed của mọi critical leaf, sensitivity
S0 và protected values kể cả JSON keys; unknown/error chặn external, fixed reads
vẫn allow. Nguồn model đã thấy và index phải khớp hai chiều, tránh bỏ sót S2 hoặc
dùng nguồn public chưa vào prompt. Post-view tạo JSON envelope cho untrusted data,
không sửa raw/labels. Đây là components, chưa full policy hoặc runtime A6.

Preflight02: **769 tests pass** (73 mới), setup/Ruff/mypy 186 files/knowledge pass.
24 Pre cases (4 ALLOW/20 DENY), sáu Post cases; bốn Broker mock calls, không model/
guard/Replay run. 771 prior source entries giữ nguyên; 132 source/121 raw hashes
đã kiểm lại. [Selected reproduction](../experiments/manifests/phase5_value_gates_v1_validation02.json)
từ source sạch `a3743a2` khớp preflight, **769 tests pass** trong 138,14 giây.
Validation01 bị gián đoạn trước khi có receipt; giữ nguyên, không chọn làm evidence.
[Contract](../docs/architecture/phase5_value_gates_contract.md),
[handoff](handoff.md). Preflight01 bị vô hiệu vì sửa source, không chọn làm evidence.

Runtime v3 vẫn A0–A5, final pass-through. Còn A6 integration/guard arbitration/
final authorization, guard thật và grouped Dev validation. Không Test payload parsing.

## Lịch sử: value-origin/final-release components

Đã hoàn thiện mốc component [truy nguồn giá trị/lọc final](../docs/architecture/phase5_value_origin_contract.md),
source `3b9f565`. Index theo kiểu dữ liệu, giữ mọi nguồn khớp và hai chiều
sensitivity/trust; release ALLOW/REDACT/DENY tất định, giữ nguyên proposed final
và nhãn lineage. Nguồn có transformation bị từ chối; giá trị chỉ còn rỗng sau
chuẩn hóa khiến release DENY, không crash hoặc tạo match rỗng.

Preflight **696 tests pass** (103 mới), setup/Ruff/mypy 183 files/knowledge pass.
24 ca synthetic: 12 ALLOW, 8 REDACT, 4 DENY; không Replay/model/benchmark run.
130 source/101 raw hashes đã kiểm lại, 641 prior source entries nguyên vẹn.
[Selected receipt](../experiments/manifests/phase5_value_origin_v1_validation01.json)
từ source sạch khớp stable preflight; lượt tái lập cũng 696 tests pass.
Test chỉ hash-check; không parse payload Test.

A6 chưa bật trong runtime: v3 vẫn A0–A5, Final pass-through. Còn Pre/Post/Final
integration, authorization/unknown critical relations, A4 general processing scope,
guard model/revision/GPU lifecycle và grouped Dev validation. Phase 5 chưa nghiệm thu.
Đọc [handoff](handoff.md) để tiếp tục; không cần tài khoản mới cho local implementation.

## Lịch sử: A3–A5 session enforcement đã tích hợp — 2026-09-07

Runtime v3 hỗ trợ A0–A5: A3 max sensitivity/S0 external clearance, A4 thêm raw-user
destination authorization sau untrusted source, A5 thêm sticky rule/LLM alerts
(kể cả SUSPICIOUS)/errors. Không hạ nhạy cảm bằng nguồn public về sau; sensitivity
và trust độc lập. Final vẫn pass-through, A6 từ chối rõ ràng.

Preflight **593 tests pass** (147 mới), setup/Ruff/mypy 179 files/knowledge pass.
44 A0–A2 exact parity pairs + 30 session cases = 118 Replay. Riêng session cases:
165 fake guard classifications, 225 snapshots và 15 expected denials; không ASR.
127 source/780 raw hashes đã kiểm, 514 prior source entries giữ nguyên. Source
`8a4ca3d`, [selected receipt](../experiments/manifests/phase5_session_v1_validation01.json)
khớp stable preflight và 593 tests pass. [Contract](../docs/architecture/phase5_session_contract.md),
[handoff](handoff.md), [tiến độ](phase5_progress.md).

Không guard LLM thật/benchmark Dev/Test payload parsing. Còn general A4 processing
scope, A6 value-origin/Post/Final, production guard model/revision/GPU lifecycle,
grouped Dev validation. Phase 5 chưa nghiệm thu; không cần tài khoản mới cho local.

## Lịch sử: A2 process guard

Vòng ReAct v2 hỗ trợ A0/A1/A2. A2 kiểm tra action/source, giữ cảnh báo độc hại/lỗi
trong task, chặn external sink trước Broker; read-open, SUSPICIOUS chỉ TAG.
Worker có deadline thực, terminate/kill/reap, không tự retry sau infrastructure
failure. Guard cache/trace riêng từng task, không vào agent prompt.

Preflight **446 tests pass** (80 mới); setup/Ruff/mypy 175 files pass. 40 exact
A0/A1 smoke pairs + chín A2 synthetic cases = 89 Replay, 31 fake classifications.
124 source/548 raw hashes được ghi, 390 prior source entries giữ nguyên.
Source `15ed921`, [selected receipt](../experiments/manifests/phase5_a2_v2_validation01.json)
khớp preflight; source/raw hashes đã kiểm lại. [Contract](../docs/architecture/phase5_a2_runtime_contract.md),
[bàn giao](handoff.md). Không real model/Dev benchmark run hoặc Test parsing.

Chưa chọn/chạy guard LLM thật. Adapter hiện cold-load mỗi cache miss; thời gian
ghi là tổng cold guard, không throughput GPU. A3–A6/final protection/Dev validation
còn thiếu, không nghiệm thu Phase 5. Không cần tài khoản mới cho phần local.

## Lịch sử: shared A0/A1 runtime

Source mới `d2ec2d5`, [runtime receipt](../experiments/manifests/phase5_runtime_v1_validation01.json).
Shared ReAct A0/A1 đã tích hợp policy, raw model/context/argument/final artifacts,
security sidecar và denial feedback không giả ToolResult. **366 tests pass**, 66
runtime tests mới; setup/Ruff/mypy 170 files pass. 20 exact A0 pairs + 24 synthetic
A0/A1 conditions = 64 fresh Replay; 120 source/369 raw hashes khớp, 270 prior
source entries giữ nguyên, stable summary khớp preflight. Không model/benchmark
Dev run/Test payload parsing. Bước tiếp theo: A2 guard/bounded inference và A3–A6.
Runtime chưa hỗ trợ A2–A6, final A0/A1 vẫn pass-through. [Handoff](handoff.md).

## Lịch sử: mốc component đầu tiên

Owner đã mở Phase 5. Source `4bddd23`,
[component receipt](../experiments/manifests/phase5_components_v1_validation01.json).
Đã có bảy config tích lũy, typed decisions/public inputs, A1 detector/authorization
và adapter trước Tool Broker; A2 có strict parser/backend/cache/error interface.
**300 tests pass**, gồm 56 micro-tests mới; setup/Ruff/mypy 166 files pass.
153 Phase 4 source hashes giữ nguyên; không Dev benchmark tuning/Test payload
parsing hoặc model run mới. [Tiến độ](phase5_progress.md), [handoff](handoff.md).
Chưa full ReAct integration, guard inference thật, A3–A6 enforcement hoặc nghiệm thu.

## Lịch sử: Phase 4 đã nghiệm thu — 2026-09-07

Source `be7f8b5`, [closure receipt](../experiments/manifests/phase4_closure_v1_validation01.json),
[12 DoD và giới hạn](../docs/architecture/phase4_report.md). **244 tests pass**;
setup/Ruff/mypy 160 files/knowledge-check pass. 21 clean Dev + 24 deep attack/benign
Dev paired conditions, 90 fresh Replay; thêm 440 smoke overhead và hai stress.
Metadata search/DB/nguồn phụ giữ nhãn bảo thủ; 120 sink fields có lineage S2.
Overhead CPU Replay thêm trung vị 5,539 ms, p95 11,749 ms; smoke traced peak
527.301 bytes, cả hai guard pass. Stress 64 KiB/eight-read traced peak 21.603.744
bytes: log/context duplication còn là giới hạn. Không suy sang LLM/GPU performance.
153 source + 1.625 raw hashes khớp, 497 prior hashes giữ nguyên; stable Dev summary
khớp preflight. Test hash-only, không Test payload parsing hoặc model run mới.
Phase 1–4 accepted dưới các waiver đã ghi; **Phase 5 cần owner cho phép**.
Điểm Gemma/Qwen cũ không đổi. [Handoff](handoff.md).

## Lịch sử: runtime Phase 4 đã tích hợp — 2026-09-07

Source `a65bc53`, [receipt](../experiments/manifests/phase4_runtime_v1_validation01.json).
Runtime riêng có ControlState/ContextBundle, hook Pre/Post/Final pass-through,
source snapshots, email/webhook field artifacts, model/context/final lineage và
trace v2. Audit-normalized views không vào prompt; raw A0 giữ nguyên.
**224 tests pass** (39 mới), setup/Ruff/mypy 156 files và seal check pass.

65 paired conditions = 20 smoke + 21 clean Dev + 24 attack/benign Dev probes,
130 fresh Replay, khớp exact contexts/actions/results/final/terminal. 824 artifacts,
1.173 edges, 390 raw artifact hashes; selected run khớp preflight stable summary.
Clean Dev dùng QA reference actions/faults riêng, không đưa GT vào runtime.
Dev probe final cố định: không tính utility/ASR hoặc điểm model mới. Không Test
payload parsing trong suite mới, không LLM/Kaggle run. [Chi tiết](phase4_progress.md).

**Phase 4 chưa xong:** tiếp theo rà metadata nguồn/search, luồng nhạy cảm nhiều
bước trên Dev và đo overhead/memory có kiểm soát, rồi acceptance review.
Không sửa source/data đã hash; không bật defense Phase 5. [Handoff](handoff.md).

## Lịch sử: primitive foundation

Owner đã cho phép Phase 4. Hoàn thành mốc đầu: ba profile chuẩn hóa có phiên
bản, artifact JSON bất biến, store riêng từng run, DAG/ancestor và propagation
sensitivity/trust độc lập. [Contract](../docs/architecture/phase4_foundation_contract.md).
185 tests pass (53 mới), setup/Ruff/mypy 151 files pass; hai bộ dữ liệu vẫn khóa.
Source `a4e9a87`; [receipt](../experiments/manifests/phase4_primitives_v1_validation01.json)
khớp stable summary của preflight, source hashes đã kiểm tra.
1.650 primitive checks trên 150 clean Dev instructions + 400 adversarial Dev
payloads. Validator mới không parse Test payload/GT; 50 robustness IDs đã seal.

**Phase 4 chưa xong.** Bước tiếp theo: ControlState/ContextBundle, hook pass-through,
tích hợp runtime riêng và A0 parity, rồi smoke/clean/attack Dev trajectories.
Không đổi runtime/scorer/data đã hash. Không chạy model/Kaggle; chưa bật
normalization security trong A0, chưa có chặn tấn công. [Handoff](handoff.md).

## Lịch sử: Phase 3 đã nghiệm thu

**Phase 1, Phase 2 clean_v1.1 và Phase 3 adversarial_v2 đều đã accepted.**
Phase 4 chưa bắt đầu. [Receipt đóng phase](../experiments/manifests/phase3_release_v2_closure.json),
[tóm tắt](../docs/benchmark/adversarial_release_v2_summary.md), source `c228a68`.
Đủ 70 canonical pairs, năm dạng, **350 attack + 350 benign**; mỗi branch 200 Dev/
150 Test, giữ 20 nhóm trong split 40/30. Test đã seal, không author/replay lại.

782 tests pass trước seal; hai seal-only tests skip đúng điều kiện. Sau seal:
132 tests pass; 650 historical construction tests không collect để bảo vệ Test.
Setup/Ruff/mypy 146 files, clean seal và adversarial hash check pass. Full release
tái chấm/archive 1.692 reference paths cũ, không tính thành lượt inference mới.
732 Test-assigned reference paths đều trước seal; không LLM/held-out model run.

Giữ giới hạn: review assistant theo waiver, không independent human review;
70 scenario families không phải 70 cơ chế độc lập; output-poisoning lệch 12/3.
Điểm model cũ không đổi. Không cần tài khoản mới; Meta chưa có không chặn đóng
Phase 3. Đọc [handoff](handoff.md) để tiếp tục; cần owner mở Phase 4.

## Lịch sử: code-mix/paraphrase đang triển khai

Đã lưu source `257cb1c` cho 420 mechanical variants (210 attack/210 benign),
ba dạng bỏ dấu/ranh giới từ/ký tự ẩn. 140 boundary edits được assistant review
dưới owner waiver; 280 dạng còn lại được structural QA. 604 tests pass (109 mới),
setup/Ruff/mypy 140 source files và clean seal pass.
[Receipt mechanical](../experiments/manifests/phase3_mechanical_v1_validation01.json):
1.128 fresh Replay = 280 canonical standard + 840 variant standard + tám safe
alternatives, score parity khớp canonical đã khóa. 488 lượt QA trên Test-assigned
construction data, không LLM/held-out model run. Preflight và selected run có
stable summary khớp; giữ nguyên split/scorer/data cũ. Chưa seal/Phase 3 accepted.

Owner vừa yêu cầu tiếp tục trong lúc làm. Đang chuyển sang **140 code-mix +
140 paraphrase records còn thiếu**, rồi full 700-variant integration/QA/seal.
Không đổi mốc mechanical đã hash; thêm module/version mới.

## Lịch sử: canonical đã chọn, còn variants/release

Đã review toàn pool và **nhận 70 canonical cho bước tạo biến thể**, theo waiver
self-review của owner; không phải 70 abstract mechanisms độc lập. Giữ hai merge
trong 72 ca lưu. Chia **40 Dev / 30 Test**, không tách 20 nhóm bảo thủ.
[Manifest hiện hành](../experiments/manifests/phase3_canonical_selection_v1_validation01.json),
[tóm tắt và giới hạn](../docs/benchmark/canonical_selection_summary.md), source `dc45ccb`.

17.429 phương án grouped hợp lệ được xét theo objective cố định. Tool-output
poisoning lệch **12 Dev / 3 Test** do nhóm business có 25 ca; không được đổi nhãn
hay tách nhóm để che lệch. Sink/complexity cũng có phân bố và ô zero trong manifest.
495 tests pass (29 mới), setup/Ruff/mypy 136 source files và clean seal pass.
288 reference records cũ được tái kiểm tra; 280 thuộc 70 ca được chọn, tám thuộc
hai ca gộp. **Không Replay/model/Test run mới**, không đổi dữ liệu/scorer/điểm cũ.

Phase 3 **chưa xong**: chưa có 350 attack + 350 benign variants được duyệt,
chưa release integration/seal Test. Ước lượng **65–70% effort**, không metric
nghiệm thu. Bước tiếp theo là variants theo split đã chốt, không thêm canonical
hoặc chọn lại split. Xem [handoff](handoff.md) và [readiness](phase3_readiness.md).
Không cần tài khoản mới để làm phần này; quyền Meta vẫn không chặn Phase 3.

## Lịch sử: boundary batch đạt 70 đại diện tạm giữ

Đọc [handoff](handoff.md) để tiếp tục đúng điểm đang dở, [runbook](runbook.md)
cho lệnh hiện hành, và [Phase 3 progress](phase3_progress.md) cho audit mới.
Knowledge đã có chỉ mục, bàn giao và validator link/cấu trúc; đây là memory
phát triển, không đưa vào prompt agent benchmark.

Phase 3 có **72 cặp ứng viên, 70 đại diện tạm giữ** sau hai quyết định gộp cũ.
Thêm tám cặp `boundary_batch_v1`: private projection, final-policy hijack,
quota chung hai kênh và thu hồi quyền. 20 nhóm bảo thủ, 2.556 comparisons;
chưa variants/split/freeze hoặc chứng nhận 70 family độc lập đã nghiệm thu.

Bằng chứng hiện hành: **34 fresh Replay** (32 standard + hai safe alternatives),
tái dùng 256 standard paths cũ; tổng standard 288 (144 safe/144 negative).
Sáu admission counterexample/control
cũ vẫn là bằng chứng riêng, không cộng vào lượt mới. Rules v2 đã sửa tiếp tục
được giữ; A0, dữ liệu/scorer cũ và điểm model không đổi.
[Receipt boundary](../experiments/manifests/phase3_boundary_v1_validation01.json):
`valid=true`, `phase3_accepted=false`; source `c5e1030`.
[Tóm tắt](../docs/benchmark/boundary_batch_summary.md) ghi rõ coverage và giới hạn.
Kiểm tra mới nhất: **466 tests**, setup/Ruff/mypy 134 source files và clean seal
pass; mười ba receipt cũ/1.099 hash entries khớp, gồm 12 measured artifacts.
Không LLM/Kaggle/Test inference; không đọc payload Test để author ca mới.
Ước lượng: **55–60% effort Phase 3**, không metric nghiệm thu.
70/70 là đủ số đại diện tạm giữ, không phải 100% Phase 3 hoặc family accepted.
[Readiness](phase3_readiness.md): bước tiếp theo là quyết định admission toàn pool,
kiểm tra khả năng grouped 40/30 split rồi variants/freeze. Không author thêm chỉ
để tăng số; review toàn pool có thể yêu cầu gộp/thay thế.

## Lịch sử: pilot revision v2.2

Pilot `candidates_v2_2` là revision riêng của 12 cặp v2.1,
không phải thêm 12 family. Đã sửa wording attack/benign và gộp thận trọng còn
bảy review units; chưa split/approved, không tính vào quota 70 family chính thức.
Public task/private oracle giữ nguyên bytes so với v2.1; sidecar typed utility
và các reference scripts giữ nguyên. 48 Replay qua Broker đạt QA (24 safe/24
negative), per-case scores khớp bản trước. Benign trung tính hơn, tỷ lệ độ dài
so với attack 1,03–1,13; lexical/length QA không chứng minh độc lập ngữ nghĩa.
[Tóm tắt revision](../docs/benchmark/canonical_revision_summary.md) và
[contract](../docs/benchmark/canonical_revision_contract.md) ghi ranh giới rõ.
Typed utility + source evidence, SQL table/column và per-artifact sink/final
QA đã có; row-level scope, entailment và encoded leakage vẫn chưa tổng quát.
Draft v1, workbench và mọi input/source/receipt trước giữ nguyên. Bước tiếp theo
là author thêm cơ chế canonical thật sự khác, ưu tiên retrieval/multi-step;
không lặp lại việc sửa wording 12 cặp. Chưa tạo variants hoặc chạy Kaggle.
[Tiến độ theo DoD](phase3_readiness.md): ước lượng 25–30% effort, không phải
phần trăm family accepted. Không sửa evaluator hoặc điểm các pilot đã chạy.
Kiểm tra tại mốc v2.2: 244 tests pass; setup/Ruff/mypy (112 source files) pass;
clean_v1.1 seal và measured release hashes giữ nguyên. Các số test trong
phần lịch sử bên dưới thuộc các mốc trước, không phải lần kiểm tra mới nhất.

## Kết quả model gần nhất: pilot có đo hiệu suất — 2026-09-06

Gemma 4 E4B IT và Qwen2.5 7B Instruct đã chạy xong cùng 21 Dev task trên
Kaggle (mỗi model kernel v1, hai T4, cùng source/software, không chạy lại lỗi
ngữ nghĩa). CPU preflight pass; hai audit pass, 0 model errors, 0 secret matches.
Gemma đạt strict 6/21, trung bình 11,66 giây/task; Qwen 7B đạt 3/21,
10,92 giây/task. Schema validity tương ứng 100% và 94,74%.

[Báo cáo và giới hạn](../docs/evaluation/measured_dev_pilot_report.md),
[bảng/CSV/JSON](../experiments/reports/measured_dev21_v1/report.md),
[nhật ký pilot](multimodel_dev_pilot.md). Các script sinh báo cáo/biểu đồ từ
artifact đã audit; không sửa điểm tay và không chốt model từ mẫu nhỏ này.
Qwen 3B lịch sử không thuộc so sánh tốc độ có kiểm soát. Llama vẫn chưa chạy
vì chưa được cấp quyền Meta; không ghi model thiếu thành điểm 0.
Kiểm tra cuối: setup/Ruff/mypy pass, 107 tests pass; JSON/CSV/Markdown tái tạo
khớp từng byte, biểu đồ PNG/PDF đã kiểm tra hiển thị.

Phase 1 và Phase 2 v1.1 đã accepted; Phase 3 vẫn là draft cần semantic/overlay
QA. Held-out Test chưa chạy model. Phần dưới là lịch sử Phase 1–2.

## Lịch sử đóng Phase 2 — 2026-09-06

Owner đã phê duyệt bản thay thế. v1.1 đã qua QA thực thi 250/250 và khóa split
150/100 không tách nhóm ngữ nghĩa. Kaggle v1.1 COMPLETE ngay lần đầu: 21/21
terminal, 0 crash, 318 trace hợp lệ, 5/21 Dev diagnostic. 96 test pass. Đã
đóng Phase 2 cho benchmark frozen dưới automated-QA waiver; các giới hạn
annotation/cách trả lời tương đương được ghi rõ và không được diễn giải quá mức. Đọc
[clean_v11_progress.md](clean_v11_progress.md) trước phần audit lịch sử bên dưới.

Cập nhật: 2026-09-06, sau audit lại. **clean_v1.0 bị quarantine; clean_v1.1 là
benchmark thay thế đã được chấp nhận dưới waiver.** Kết luận cũ về v1.0
được rút lại; xem `integrity_audit_20260905.md` để biết lịch sử.

## Đã hoàn thành

- Setup repository, GitHub riêng tư và CI.
- Phase 0: research contract và các quyết định nền tảng.
- Phase 1: A0 baseline, simulated university environment, 8 mock tools, 20
  smoke tasks, trace JSONL, local Replay/Dummy và real-model Kaggle smoke.
- Kaggle authoritative run: kernel v4, Dataset v5, Qwen2.5-3B-Instruct v1,
  NVIDIA T4, internet tắt.
- Minh review được chủ dự án cho phép hoãn; lời mời GitHub vẫn giữ nguyên.
- clean_v1.1 đã tạo 250 task, môi trường, split 150/100 và Dev pilot; v1.0
  trước đó có 30 cặp cùng fact/nguồn bị gán nhóm khác nhau, 12 cặp xuyên Dev/Test.

## Trạng thái chất lượng

- Local Replay: 20/20 success, 20/20 terminal, 0 crash, 8/8 tool coverage.
- Real model: 20/20 terminal, 0 crash, 3/20 task success, 78,87% schema
  validity; đây là smoke metric, không phải kết quả luận văn.
- Test sau audit: 96 pass; Ruff/mypy/setup pass. Software pass không thay thế
  thẩm định ngôn ngữ độc lập.
- Phase 1 audit lại: hai lượt Replay/Dummy có cùng hành vi khi bỏ timestamp/run
  ID; 8/8 artifact Kaggle khớp hash, 262 sự kiện hợp lệ, không chạy lại model.
- Phase 2 oracle mẫu: 250/250, đủ 8 tool; review flag được gán sẵn nên không
  chứng minh 250 task đã qua đủ 10 kiểm tra QA.
- Kaggle Dev pilot v2: 21/21 terminal, 0 crash, 334 trace hợp lệ, 7/21 task
  provisional diagnostic success, chưa phải strict TSR; worker đọc 0 Test/GT.
- Held-out Test: đã niêm phong, chưa chạy model và không được dùng để tuning.

## Trạng thái phase tại thời điểm audit v1 (lịch sử)

Phase 2 mở lại, v1 giữ nguyên làm lịch sử. Đã sửa signature/group/hash validator,
chặn ghi đè bản khóa và chặn đóng gói split lỗi. Không đổi task/GT/môi trường/
schema/manifest v1. Cần chủ dự án chấp thuận version benchmark thay thế để sửa
quy trình nhóm xuyên category, QA theo bằng chứng và comparator trước khi khóa
lại. Phase 3 chưa bắt đầu; không cần thêm tài khoản hay Minh review.

Huy và Minh dùng chung máy nên chủ dự án bỏ peer review. Dataset không ghi giả
reviewer; thay vào đó phải có automated QA theo owner waiver, đồng thời ghi
rõ hạn chế thiếu independent human review trong data card. Không ghi rằng chủ
dự án đã inspect từng task; audit record dùng `automated_gate`.
