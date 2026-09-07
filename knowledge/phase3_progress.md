# Phase 3: tiến độ và thiếu sót đã xác minh

Cập nhật 2026-09-07. Trạng thái: **draft chưa đủ điều kiện nghiệm thu**.
Gồm audit tĩnh và QA executable để tiếp tục authoring, không phải ASR hay chọn model.

## Mới nhất: 64 ứng viên, 62 đại diện và task-effect QA

`completion_batch_v1`, source `9917eb0`, bổ sung 12 cặp có hiệu ứng nghiệp vụ
khác nhau: đơn vị tiền, làm tròn, idempotency, atomicity, quyền có hạn, phân bổ,
attribution, người ký, citation, ngày ghi nhận, múi giờ và hàng đợi. Bảy source
tool-output, ba document và hai cache. Tất cả giữ chung nhóm business có sẵn;
không coi mỗi field là một abstract mechanism mới.

- 48 fresh Replay (24/24), tái dùng 208 standard paths; tổng standard 256.
- 64 working/62 retained/2 merged, 17 nhóm bảo thủ, 2.016 comparisons.
- 428 tests pass (27 mới), setup/Ruff/mypy 131 source files và clean seal pass.
- Mười hai receipt cũ/956 hash entries khớp, gồm 12 measured artifacts.
- [Receipt](../experiments/manifests/phase3_completion_v1_validation01.json),
  [tóm tắt và giới hạn](../docs/benchmark/completion_batch_summary.md).

Ước lượng effort 50–55%, không metric nghiệm thu; 62/70 chỉ là đại diện tạm giữ.
Cần ít nhất tám đại diện nữa và review toàn pool. Business group 25 đại diện
phải chung split; không tách nhóm để ép stratification. Chưa variants/split/seal.
Không LLM/Kaggle/Test inference, không sửa source/scorer cũ hoặc điểm model.

## Lịch sử: 52 ứng viên, 50 đại diện và disclosure QA

Thêm bốn cặp query/final/email/JSON trong `disclosure_batch_v1`, source `1c3f829`.
Ba fragmented cases chung nhóm; pool có 17 nhóm bảo thủ/1.326 comparisons.
52 ca lưu trữ, 50 đại diện tạm giữ sau hai merge trước, chưa family acceptance.

- 16 fresh Replay (8 safe/8 negative), giữ utility và cô lập coverage mới.
- 192 standard paths tái dùng có hash binding; tổng standard 208, không phải
  208 lượt mới. Không cộng sáu admission counterexamples cũ vào standard paths.
- 401 tests pass (34 mới), setup/Ruff/mypy 129 source files và clean seal pass.
- Mười một receipt cũ/823 hash entries khớp, gồm 12 measured artifacts.
- [Receipt](../experiments/manifests/phase3_disclosure_v1_validation01.json),
  [tóm tắt/giới hạn](../docs/benchmark/disclosure_batch_summary.md).

Fragment coverage chỉ nhận hai mảnh khai báo, chưa general reconstruction hay
entailment; không biến việc thiếu full-disclosure hit thành bảo đảm riêng tư.
Cần thêm ít nhất 20 đại diện, cân đối source/category và review toàn pool trước
split/variants/freeze. Không LLM/Kaggle/Test inference hoặc đổi điểm lịch sử.

## Lịch sử: sửa rule và chốt review 48 ứng viên

`mechanism_batch_v2` chỉ sửa hai trường rule đã chứng minh bỏ sót quota và giá
trị webhook. Dataset/scorer/receipt cũ giữ nguyên. Source `e001c8a`.
Review toàn bộ 48 ứng viên giữ 46 đại diện cho lựa chọn cuối; hai ca gần trùng
gộp vào đại diện có sẵn, giữ nguyên file regression và 15 nhóm bảo thủ.
Không chứng nhận 46 family độc lập hoặc giả independent human review.

- 38 fresh Replay: 32 standard revised và sáu counterexample/control.
- Tái dùng 160 standard paths của 40 ca không thay đổi; tổng standard vẫn 192.
- 367 tests pass (26 mới), setup/Ruff/mypy 126 source files và clean seal pass.
- Mười receipt cũ/689 hash entries khớp, gồm 12 measured artifacts.
- [Receipt admission](../experiments/manifests/phase3_admission_v1_validation01.json),
  [tóm tắt](../docs/benchmark/mechanism_admission_summary.md),
  [contract](../docs/benchmark/mechanism_admission_contract.md).

Cần thêm ít nhất 24 đại diện được giữ trước full-pool selection, grouped split,
variants và freeze. Ước lượng effort vẫn 45–50%, không phải metric nghiệm thu.
Không model/Kaggle/Test inference mới; không sửa điểm pilot hoặc dùng Test tuning.

## Lịch sử: 48 ứng viên và QA authorization-flow

Tám cặp mới dùng lại builder/runtime/scorer cũ nguyên vẹn; bổ sung source
dependencies và private flow rules, không thêm defense. Tổng 48 candidates,
15 nhóm bảo thủ và 1.128 pair comparisons; không coi tám cặp là tám cơ chế mới.

- 192 fresh Replay pass (96/96), 32 lượt thuộc batch flow.
- 341 tests pass (20 mới), setup/Ruff/mypy 123 source files và clean seal pass.
- Chín receipt cũ/566 hash entries khớp, gồm 12 measured artifacts.
- [Receipt v3](../experiments/manifests/phase3_pool_v3_validation01.json),
  [tóm tắt](../docs/benchmark/flow_batch_summary.md),
  [contract](../docs/benchmark/flow_batch_contract.md). Source `56de8e7`.

Ước lượng **45–50% effort**, không metric nghiệm thu; 48/70 ≈ 69% chỉ là số
ứng viên so với mục tiêu. Còn 22 trước full-pool admission/merge, rồi grouped
split, variants và freeze. Không LLM/Kaggle/Test inference hoặc Test-driven tuning.

## Lịch sử: 40 ứng viên, self-review và QA tổng hợp v2

Thêm 12 cặp transaction/sink-position, không sửa dữ liệu đã khóa. Đã ghi
self-review 28 cặp trước và 12 cặp mới. Các substitution gần nhau tiếp tục
chung nhóm; 40 candidates tạo 15 conservative review units, 780 comparisons.
Chưa chứng nhận đủ 40 family độc lập hoặc tự tạo variants/split.

- 160 fresh Replay pass (80 safe/80 negative); batch mới đóng góp 48 paths.
- 321 tests pass (24 mới), setup/Ruff/mypy 121 source files và clean seal pass.
- Full fixed-payload scope kiểm tra cả ID/extra field, bool/number/list/object;
  hai encoded sink cases được test riêng không dựa vào exact-message mismatch.
- Tám receipt trước/451 hash entries khớp, gồm 12 measured artifacts.
- [Receipt v2](../experiments/manifests/phase3_pool_v2_validation01.json),
  [tóm tắt](../docs/benchmark/transaction_batch_summary.md),
  [self-review](../docs/benchmark/pool_author_review_v1.md). Source `7f1f284`.

Ước lượng trả lời owner: **40–45% effort Phase 3**, không tỷ lệ nghiệm thu.
40/70 ≈ 57% candidate count; còn 30 trước full-pool release review. Các việc
variants, grouped split và freeze vẫn mở. Không model/Kaggle/Test inference;
static audit bản v1 đọc hai split chỉ để xác minh integrity như trước.

## Lịch sử: 28 ứng viên và QA tổng hợp

Batch linked-scope bổ sung tám cặp: bốn row-scope, bốn multi-source. Các nhóm
trùng cơ chế nối với pool cũ; không coi mỗi cặp là một cơ chế độc lập. Tổng
14 review units, 378 pair comparisons. Cả ba batch được chạy lại cùng verifier:
112 Replay pass, 56 safe có typed utility/evidence, 56 negative được nhận diện.

- 297 tests pass (34 mới), setup/Ruff/mypy 119 source files và clean seal pass.
- Row scope kiểm tra key trong SQLite read-only, grammar bounded; SQL ngoài
  grammar hoặc thiếu grant là unassessed. Không sửa A0 hay scorer cũ.
- Tách public auxiliary sources khỏi private rules; nguồn phụ trong từng pair
  giữ nguyên, mọi runtime read qua Broker. Tests chặn mạng và tái lập pass.
- Bảy receipt trước/347 hash entries khớp, gồm 12 measured model artifacts.
- [Receipt tổng hợp](../experiments/manifests/phase3_pool_v1_validation01.json),
  [tóm tắt/self-review](../docs/benchmark/linked_scope_summary.md),
  [contract](../docs/benchmark/linked_scope_contract.md). Source `89eedaa`.

Verifier báo `qa_valid=true` và `phase3_accepted=false`. Với cờ
`--require-acceptance`, exit 2 là báo thiếu acceptance có chủ đích.
28/70 = 40% số ứng viên mục tiêu, không phải phần trăm phase đã đạt. Còn thiếu
42 ứng viên trước review; variants, grouped split và freeze vẫn chưa hoàn tất.

## Lịch sử: thêm tám cặp cơ chế mới, tổng 20 ứng viên

Đã thêm batch độc lập `mechanism_batch_v1`: tham số nghiệp vụ ở endpoint hợp lệ,
gửi lặp vượt quota, gửi trước kiểm tra, mở rộng query và encoded final disclosure.
Các biến thể cùng cơ chế giữ chung group; năm nhóm mới + bảy cũ = 12 review units,
chưa chứng nhận family độc lập. Audit toàn bộ 190 tổ hợp của 20 ứng viên.

- 32 fresh Replay pass (16 safe/16 negative); 263 tests toàn repo pass.
- Tám tool thực sự được dùng; hai pair có full payload trong search snippet
  gốc, bốn path bắt đầu bằng retrieval, safe paths dài 2–4 actions.
- Private rules chấm nested arguments, quota successful calls, prior-success
  prerequisite và complete Base64/hex. Failed effects không tính executed;
  grants theo artifact/nơi nhận/final vẫn riêng. Không thêm defense cho A0.
- [Receipt](../experiments/manifests/phase3_mechanism_batch_v1_validation01.json),
  [tóm tắt](../docs/benchmark/mechanism_batch_summary.md),
  [contract](../docs/benchmark/mechanism_batch_contract.md).
- Setup/Ruff/mypy 115 files và sealed clean validation pass. Không LLM/Test run.

20/70 ~29% số ứng viên mục tiêu, không phải approved families. Ước lượng effort
Phase 3 khoảng 30–35%; variants/split/freeze vẫn pending. Bước sau là cơ chế
multi-source/data-scope khác, không lặp lại batch hoặc revision cũ.

## Lịch sử: pilot revision v2.2 — neutral benign và nhóm cơ chế

Đã tạo bản riêng cho 12 cặp, giữ nguyên v2.1 và các artifact cũ. Public task/
private oracle byte-identical; chỉ đổi overlay attack/benign text và catalog
group labels. Benign được viết thành thông tin tác vụ thay vì safety instruction,
attack bỏ nhãn tự gọi là giả; mục tiêu/đích nhận/reference scripts không đổi.

- 48 fresh typed-utility Replay giữ nguyên per-case scores; 244 tests pass.
- Tỷ lệ độ dài benign/attack 1,0278–1,1333, trong gate 0,8–1,25 đã khai báo.
- Gộp thêm destination substitution và extra-document access xuyên source/sink:
  còn bảy conservative review units, không phải bảy family đã accepted.
- Validator chặn đổi trường ngoài phạm vi, đổi target, chèn trực tiếp private
  value, giả human approval, nới gate độ dài và tách nhóm cũ. Tests chặn network
  và kiểm tra Replay tái lập pass; setup/Ruff/mypy 112 source files pass.
- [Receipt v2.2](../experiments/manifests/phase3_canonical_revision_v22_validation01.json),
  [tóm tắt revision](../docs/benchmark/canonical_revision_summary.md).

Mốc wording/group pilot đã xong; bước sau là author thêm cơ chế mới, không
tái sinh 12 cặp này để tăng count. Canonical approval/variants/split vẫn pending.
Không LLM/Test inference, không đổi clean/measured scores hoặc A0.

## Lịch sử: typed utility, group/pair audit và tiến độ DoD

Theo yêu cầu tiếp tục, đã thêm lớp review QA riêng, không sửa candidate inputs
hoặc scorer cũ. Typed utility kiểm tra giá trị số/ngày/giờ/entity/phrase và
evidence từ đúng source action; required sink và security checks vẫn độc lập.
Đã test regression cho lỗi substring, định dạng ngày tương đương, evidence
thiếu/sai, sink thiếu/thất bại và final leakage.

- 48 fresh Replay đạt kỳ vọng (24 safe/24 negative); 220 tests toàn repo pass.
- Audit đầy đủ 66 tổ hợp ứng viên: ba nhóm template chung, chín review units
  tạm thời. Nhóm có liên kết bắc cầu không được tự tách; không chứng minh
  độc lập ngữ nghĩa hoặc phân split tự động.
- [Assistant review notes](../docs/benchmark/candidate_review_notes.md) ghi các
  điểm cần sửa: attack tự gắn nhãn giả, benign gợi ý không hành động, độ dài
  và khả năng trùng cơ chế. Đây không phải human approval, không thay dữ liệu.
- [Receipt](../experiments/manifests/phase3_candidate_review_v1_validation02.json)
  lưu input/sidecar/source/trace hashes; setup/Ruff/mypy 110 files pass.
- [Readiness theo DoD](phase3_readiness.md) ước lượng 25–30% effort; vẫn chỉ
  12 ứng viên, chưa có 70 family đạt chuẩn, chưa variants/split/freeze.

Typed presence chưa phải entailment/negation detection; exact evidence-action
và sink fixtures vẫn có giới hạn. Không ảnh hưởng clean pilot/model scores.

## Lịch sử: 12 cặp ứng viên và data-scope QA

Owner cho phép mở rộng. Bộ riêng `data/adversarial/candidates_v2_1` có bốn cặp
thích nghi từ workbench và tám cặp mới, không ghi đè đầu vào cũ. Public task,
overlay, private oracle và catalog metadata tách riêng; runtime không nhận
ground truth. Tất cả unsplit/review-pending, chưa tính vào 70 family chính thức.

- Mỗi category và mỗi source type có ba cặp; catalog có chín nhóm template.
  Nhãn nhóm là gợi ý review, không phải bằng chứng có 12 family độc lập.
- Bổ sung đọc tài liệu ngoài phạm vi, đổi endpoint, gửi thêm artifact riêng
  tới địa chỉ hợp lệ, và gửi artifact được phép nhưng không lộ trong final.
- SQL scope kiểm tra bảng/cột bằng SQLite compile/authorizer offline, xử lý
  alias, biểu thức và wildcard. SQL không hỗ trợ/lỗi hoặc thiếu scope là
  `unassessed`, không được đánh giá thành safe. Không thêm defense cho A0.
- 48 Replay (12 × attack/benign × safe/negative): 24 safe đạt utility và
  24 negative được nhận diện; payload reachable, facts có evidence, private
  context guard pass, không action unassessed trong reference scripts.
- 25 test bổ sung, gồm chặn network, SQL adversarial cases, quyền artifact
  theo nơi nhận/final và tái lập normalized traces. Tổng 168 tests pass;
  setup/Ruff/mypy 107 source files và clean_v1.1 sealed validation pass.
- [Receipt mới](../experiments/manifests/phase3_candidates_v2_1_validation01.json)
  lưu exact input/source/trace hashes và base Git commit. Input/source của
  workbench và audit v1, cùng 12 measured release artifacts vẫn khớp hash.

[Contract mở rộng](../docs/benchmark/canonical_expansion_contract.md) giới hạn
SQL ở table/column, không chứng minh row-level scope/equivalence/side channels.
Utility và artifact leakage còn là literal checks, chưa có encoded leakage.
Không chạy LLM, chưa tạo variants/split và không ghi giả human semantic review.

## Lịch sử: bốn cặp executable workbench đã pass

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

1. Dùng 15 combined review units của 48 ứng viên và self-review hiện có để
   author 22 canonical còn thiếu. Không lặp các batch đã pass hoặc tự sinh
   variants để tăng count; không đòi 70 abstract mechanisms. Chốt quyết định
   nhận/gộp family khi đủ full pool, trước grouped split.
2. Mở rộng executable QA chỉ theo yêu cầu ca mới; bounded row scope đã có,
   nhưng general SQL row inference, transformed leakage ngoài full Base64/hex
   và utility entailment tổng quát chưa được bao phủ.
   Vẫn tách private oracle khỏi runtime policy/model.
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
