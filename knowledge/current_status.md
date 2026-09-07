# Trạng thái hiện tại

## Hiện hành: Phase 3 đã nghiệm thu — 2026-09-07

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
