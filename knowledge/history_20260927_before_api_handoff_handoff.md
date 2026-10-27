> LỊCH SỬ: bản trước khi thu gọn bàn giao API ngày 2026-09-27.
> Các mục “hiện tại/bước tiếp theo” bên dưới thuộc thời điểm cũ; đọc
> [current status](current_status.md) và [handoff](handoff.md) để tiếp tục.

# Bàn giao phiên làm việc

Cập nhật: 2026-09-27. Phase 5 chưa nghiệm thu: 4/7 ≈ 57% nhóm acceptance.

## Đang làm

**Rà tiến độ và hướng hoàn thiện — 2026-09-27**

[Tiến độ và lộ trình hoàn thiện qua API](../docs/evaluation/project_status_api_20260927.md): Phase1–4 accepted, Phase5 vẫn4/7nhóm nghiệm thu;
không dùng57% cho toàn đồ án. API pair đã qua technical smoke, chưa native
fullA6/guard quality. Có thể tiếp tục bằng local runner + Kaggle inference;
không cần tăng kích thước model hoặc fine-tune để đáp ứng contract.
RQ1 vẫn cần3task backbones, có thể chạy lần lượt; một agent + một guard chưa
đủ ba model. RQ2 giữ task backbone/decoding cố định quaA0–A6, A0 không guard.

**Bước cụ thể kế tiếp:** manifest + runner Dev nhỏ có checkpoint/fault QA,
đo clean utility và guard attack/benign riêng; rồi nối candidate A6 với
Pre/Post/Final và cumulative parity. Bridge cần schemaPlan adapter riêng,
HTTP client hiện tại chỉ action/final; không coi bridge đã tích hợp qua API.
Lifecycle API cần evidence riêng; không tự đóng lỗi worker cũ từ READY.

**Bằng chứng/giới hạn:** đọc contract/20DoD/source và receipt paired smoke
đã có; không probe uptime hoặc inference mới, không Test. Không thay model
chính thức/research scope/phase acceptance. Không có access mới cần cấp cho
lượt tài liệu này; khi chạy tiếp phải kiểm health/session hiện hành. Report
và memory còn local, không commit/push trạng thái riêng.
QA lượt tài liệu: knowledge-check/diff-check/setup/Ruff đạt, mypy563files
đạt,6memory/navigation tests đạt; không fullsuite vì không đổi code/runtime.

## Mốc trước — triển khai hai API

**Hai API mới đã READY và paired smoke đạt.** Owner chọn Qwen3-8B task agent /
Llama3.2-3B guard và xác nhận đã tắt bốn phiên cũ. Đã submit mỗi notebook1lần:
buiquocviet/react-vn-qwen3-agent-api-v1 v1/ID136136611 và
huylmhuhu/react-vn-llama3-guard-api-v1 v1/ID136136616, private/T4×2 mỗi máy.
[Report và cách kết nối](../docs/evaluation/structured_pair_api_v1_report.md),
[receipt](../experiments/manifests/structured_pair_api_v1.json).
Source728821e đã push trước GPU; remote scripts khớp byte. Hai vai constrained
JSON, Qwen no-thinking, FP16/greedy/seed42; không fine-tune weights. Synthetic
23*7+5:2agent+2guard calls, calculator qua Broker, final166 đúng schema;
guard SAFE/LOW cả hai lượt. Không retry, không ASR/quality hoặc fullA6 claim.
77tests/setup/Ruff/mypy563 đạt;4 exact worker layouts +5tokenizer controls đạt.

**Next concrete step:** khai báo Dev profile nhỏ trước inference, đo clean
utility và guard benign/attack rồi mới tích hợp candidate flow. API plumbing
đã chạy thật; không cần upload lại notebook mỗi lần sửa host experiment.
Không dùng kết quả smoke để chọn threshold hoặc công bố guard đủ tốt. Không
push lại release01, không mở Test; Phase5formal4/7giữ nguyên.

**Pending access/evidence:** hai server giữ chạy; kết nối bí mật ở local
`build/kaggle/structured_pair_release01/pair_endpoints.json`, không hỏi key
qua chat. UI8765/config bốn server cũ chưa chuyển sang profile này. Private
notebook cần owner access; model hashes không publisher-attested, lifecycle/
uptime chưa nghiệm thu. Raw chưa backup ngoài máy. Receipt/report/memory
mới chưa commit; source release đã frozen. Không routine commit đợt kế tiếp.

## Mốc trước — HTTP smoke bốn API

**Mới nhất — HTTP adapter/runner và smoke thật đã xong.** Owner làm rõ
Llama3B để làm guard, ba model lớn là task agents; đồng ý điều chỉnh API.
[Report + actual results](../docs/evaluation/kaggle_http_diagnostic_20260927.md),
[receipt](../experiments/manifests/kaggle_http_diagnostic_v1.json).
GET ban đầu4/4HTTP200 sau dùng systemCA; smoke5tasks/5calls: Qwen Broker action
đạt nhưng final sai schema, Gemma timeoutGET0calls, DeepSeek nonJSON1call,
Llama guard2/2controls đúng. Không rerun semantic failures;25raw hashes và
working sources/checkpoints được audit,completed resume0newcalls,secret scan0.

**Next concrete step:** contract/schema hai vai và schema-error diagnostics
không lưu raw; CPUQA rồi paired synthetic mới Qwen agent→Llama guard→Broker→
final validation theo declaration mới. Không sửa run01 để tăng điểm. Kiểm
Gemma health riêng/DeepSeek output trước clean Dev pilot; chưa full A6 integration.
Guard JSON prompt chưa phải constrained decoding; không thay guard benchmark.

**Pending access/evidence:** endpoints/keys có local, không hỏi key qua chat.
Không có submission/restart/stop của lượt này; API remote weights/source/kernel
version chưa attested. Raw chưa backup ngoài máy. Source working-tree,không
commit/push.62tests/setup/Ruff/mypy557đạt; fullpytest không chạy vì Testsealed và
scope hẹp. Phase5formal4/7giữ nguyên. Bốn accounts/model links ở Kaggle directory.

## Mốc trước — đánh giá API trước triển khai

**Mới nhất — đánh giá API do owner tự dựng.**

Owner báo có bốn GPU API Qwen3-8B/Gemma4-E4B/Llama3.2-3B/DeepSeek-R1-Llama8B,
yêu cầu đọc và giải thích khả thi. [Static review + publisher evidence](../docs/evaluation/kaggle_api_feasibility_20260927.md).
Thông tin “chưa có endpoint” bên dưới là lịch sử 2026-09-25. User đang cân nhắc
hướng API; chưa tự chốt đổi kiến trúc, model chính thức hoặc triển khai adapter.

**Next concrete step:** nếu triển khai hướng này, kiểm health + generation smoke
synthetic, thêm HTTP LLMBackend/identity/checkpoint và chọn ba model trên Dev.
Chưa có HTTP adapter; constrained guard hiện tại không tương đương chat JSON.
READY có thể stale; model fallback, generation pin, tokens/finish_reason và
retry/cancel cần xử lý trước số liệu chính thức. Không tự quay lại batch upload
theo hướng dẫn lịch sử khi owner đang đánh giá transport mới.

**Verification/pending access:** đã đọc hai script local, base/bridge/guard và
nguồn chính thức; SHA script trong report. Chưa live probe, không inference,
không credential/state JSON, không submit/stop/remote audit, không Test.
Không thiếu key được xác nhận; remote notebook version/source/model identity
và uptime chưa kiểm. Không suy trạng thái hiện tại từ log owner dán.
Chỉ bổ sung review/memory; các thay đổi có sẵn giữ nguyên, không commit/push.
QA local: setup/Ruff/mypy555 đạt,39 unit bridge/knowledge đạt; knowledge-check
đạt sau giữ heading bắt buộc. Không full pytest vì Test sealed, không đổi runtime.

## Mốc trước — model-plan bridge và lựa chọn batch ngày 2026-09-25

**Model-plan bridge v1 đã có code và CPU controls; owner chọn batch Kaggle,
không public endpoint.** [Report](../docs/evaluation/phase5_field_model_bridge_v1_report.md),
[contract](../docs/architecture/phase5_field_model_bridge_v1_contract.md),
[QA receipt](../experiments/manifests/phase5_field_model_bridge_v1.json).
File `prototypes/field_model_bridge_v1.py` nối `LLMBackend` vào Session: real
Broker reads, một strict Plan, host veto mặc định deny, không raw reasoning/error
logging hoặc retries. Lưu Plan/request hashes, call/total time; model string
identity match không phải weight attestation. Tests scripted/HF fake, chưa native.

**Next concrete step:** làm entrypoint batch smoke + source/model admission và
checkpoint cho bridge; ưu tiên existing pinned model để tách model improvement
khỏi representation change. Exact-worker archive/expanded QA trước một source
freeze/push theo khối rồi submit private Kaggle. Không dùng package04 cũ cho code
mới. Sau smoke mới compose A1/guard/PRE/POST thật; hook hiện chỉ final callback,
không full A6/ReAct. Không nới literals/Grant hoặc nhìn held-out Test.

**Pending access/state:** owner chưa có endpoint và đã chọn không cần endpoint;
không xin API key. Không có GPU job mới/remote submission đang chạy. Còn software
entrypoint/package/admission, chưa kiểm live quota/model mounts đợt này.
Qwen3.8/model/notebook links là external reference, không tài nguyên đã triển
khai. Chưa commit/push; user report/PDF/figures và old evidence giữ nguyên.
Phase5 formal4/7 không đổi. Verification:193tests đạt (33bridge),setup/Ruff/
mypy555/diff đạt,191historical source không đổi; hash ở selected QA receipt.

## Mốc trước — component field-reference

**Owner đã duyệt tái cấu trúc giới hạn; prototype field-reference v1 + CPU matrix
đã xong, bước tiếp là model-plan/veto integration contract.**
[Report](../docs/evaluation/phase5_field_reference_v1_report.md),
[contract](../docs/architecture/phase5_field_reference_v1_contract.md),
[selected evidence](../experiments/manifests/phase5_field_reference_v1.json).
Code riêng `src/react_agent/prototypes/field_reference_v1.py`; benchmark/runtime
cũ không import prototype. Host Grant pin task/user/catalog/scope; nguồn lấy qua
Tool Broker, ref bind raw artifact/hash/path; concat/encoding giữ nhãn. Exposure
và selected-value parents tách riêng, không tuyên bố model causal lineage.

16 cases/32 component executions/98 doc_read: exposure baseline public0/8,
negative denied8/8; selected candidate public8/8, denied8/8. Cùng logical input
hash, không phải A5/A6/model ASR. Grant đúng là giả định host, chưa NLP compiler,
guard thật, model chọn ref, implicit/control-flow guarantee hoặc external sink.
Không được suy generalization tiếng Việt từ prototype không đọc ngữ nghĩa.
Raw `build/evaluation/phase5_field_reference01`, declaration SHA
`b93993b2a6754e5544aacdeee8511b685ffb151771a2fb03f8b7377c3f82e751`.
Audit01/02 byte-identical, replay trực tiếp Broker/raw/plan/labels/output, không
gọi Session.finalize/tool/model. 226 regression tests đạt, gồm57component+7audit,
setup/Ruff/mypy554/diff đạt, JUnit/hash đã lưu; không full pytest vì Test sealed.
Historical package04 vẫn191 source hashes nguyên. Không commit/push/Kaggle mới.

**Bước tiếp cụ thể:** freeze model-facing reference selection/feedback contract,
không cho model tạo Grant; thiết kế/kiểm định quyền từ host độc lập expected answer.
Nối thử loop riêng với prior A1/guard/PRE/POST veto, kiểm chọn sai field, public
source injection/free-form secret trước external mock sinks và native batch.
Representation phải giống nhau trong A0–A6 comparison mới; không đổi A0 purity,
benchmark/tool schema hoặc main mặc định. Chỉ integrate sau control pass, không
đặt GPU/package ahead of interface. Access chưa thiếu account; chờ integration
chứ không còn chờ owner duyệt prototype. Formal4/7 không đổi.

## Mốc trước — direction review và đề xuất

**Ưu tiên mới: rà lại hướng và chờ duyệt prototype tái cấu trúc có giới hạn;
không tiếp tục promote/package doc_read theo backlog cũ.** Owner lo Phase 5
đi lệch và yêu cầu thực nghiệm/giải pháp, cho phép cân nhắc xây lại nếu không khả thi.
[Review + đề xuất](../docs/evaluation/phase5_direction_review_20260925.md),
[protocol](../docs/evaluation/phase5_direction_probe_v1_protocol.md),
[selected receipt](../experiments/manifests/phase5_direction_probe_v1.json).
12 synthetic mechanism conditions × 2 A6 arms: v12 utility 8/8 nhưng protected
omissions 0/4; doc_read candidate utility 2/8, omissions 3/4 (lọt Base64).
Không model ASR/FPR, không 12 families độc lập. Candidate chỉ giữ exact command
và no-collision; paraphrases/polite/prose/multiline/repeat mất utility.
Không sửa policy theo kết quả này; không promote narrow proof thành general remedy.

Raw01 lỗi serializer sau first baseline, giữ/excluded 1 CPU execution. Raw02
hoàn tất 10 conditions/20 executions rồi lỗi ID base64 trước worker. Raw03
khóa parent declaration SHA ngoài, re-audit 20 retained, chỉ chạy missing2/4
executions; parent/raw inventory không đổi. Receipt03 có đủ selected24, ghi
harness deviation, runtime sources không đổi. 96 focused tests đạt (9 harness
và 87 proof/native/pair); không full pytest/Test/private oracle/model/Kaggle mới.

**Bước tiếp cần quyết định:** câu hỏi async đã gửi: đồng ý prototype typed-field
reference/host dataflow riêng, giữ benchmark/Broker/raw và cùng representation
A0–A6 hay không. Chưa có phê duyệt cụ thể; theo research-evidence không tự đổi
architecture. Nếu duyệt: contract ngắn + prototype falsifiable duy nhất, fresh
CPU controls rồi một native batch chỉ khi đạt. Không đập toàn repo, đổi benchmark,
tự hạ DoD hoặc xóa gate grace/quality. Chưa freeze/push/commit hay tăng acceptance.
Nếu chưa trả lời: nhắc lựa chọn ở review, không quay lại vô hạn regex/package.

## Mốc trước — doc_read native wiring và package CPU

**Đã nối doc_read native-capable adapter/admission/dispatch và full pair/Broker audit;
exact-worker CPU package04 đã qua, chưa native inference.**
[Report](../docs/evaluation/phase5_doc_read_native_cpu_v1_report.md),
[protocol](../docs/evaluation/phase5_doc_read_native_v1_protocol.md),
[selected evidence](../experiments/manifests/phase5_doc_read_native_cpu_v1.json).
Runtime riêng `security_runtime_doc_read_pair_candidate_v1`, giữ thuật toán
proof CPU/v3 PRE/POST. External run/source/approval/config/model/hash admission;
kiểm cả code thực tế import, chỉ ba environment files. Broker audit joins
raw ToolResult/call/run/task/step/order/catalog, final replay và full guard/
constraint/witness/exit. Native checkpoint chỉ sau full audit/model identities/
source stability; partial thất bại giữ nguyên, không semantic retry.

Package01/02 là source cũ; package03 bị source-origin check từ chối namespace
`react_agent.validation` do worker cố ý bỏ initializer kéo host QA. Đã xác định
nguyên nhân từ đúng archive, sửa chỉ cho phép một namespace path trong source,
không mang initializer/oracle vào worker. Package03 giữ nguyên, không preflight
thành công; sửa builder để các lần sau lưu stdout/stderr trước khi raise.
Selected package04: 191 worker files khớp working tree, archive/expanded venv
offline, 8 tools + 21 clean Dummy/layout, complete/missing-only clean resume.
SHA preflight `63291dbb7ab7f9ae64bed55a64fde652cddc33ac532f736a2b969c2ba75ac995`.
`source_commit=null`, 0 native/prospective run, không release-admitted.

**Bước tiếp cụ thể:** thiết kế prospective mới với metadata-only approval và
matched baseline/candidate run manifests, evaluator giữ host-side; một source
freeze/push theo khối sau QA, committed exact rehearsal, pin/content mới rồi
Kaggle. Không tái dùng stopped pilot để tuning, không coi fixture self-review
là owner chronology attestation. Native quality/representative utility/graceful
OS-exit vẫn mở. Khối native hiện chỉ one-task A6 candidate, chưa multi-arm
prospective batch launcher/payload/scorer; không gọi package04 là release.

Verification: final regression **374 passed, 1 strict XFAIL**; focused **53 passed**
(overlap), JUnit/hash trong selected summary. Setup/Ruff/mypy549/knowledge/diff
đạt; không full pytest vì authoring
Test sealed. Không private GT hoặc model/network mới. Pending access: chưa cần
tài khoản cho CPU; model mounts/native source/pin phải admission trước GPU.
Chưa có Kaggle notebook/Dataset mới; giữ resource directory hiện hữu. Chưa
commit/push, Git base c87 không chứa candidate; giữ cadence ít commit. Không
đụng báo cáo/PDF/figures riêng của user.

## Mốc trước — raw doc_read CPU proof

**Đã hoàn thành proof raw `doc_read` + paired CPU matrix; đang chờ native wiring.**
[Protocol](../docs/evaluation/phase5_doc_read_final_proof_v1_protocol.md),
[report](../docs/evaluation/phase5_doc_read_final_proof_v1_report.md),
[selected manifest](../experiments/manifests/phase5_doc_read_final_cpu_v1.json).
Component bind doc_id/source/raw document hash/call ID/`/content`, approval
hash ngoài và exact raw task; giữ nguyên raw doc_read ba field, không projection
giả. V3 PRE/POST không đổi, FINAL dùng v4 và proof mới. 12 conditions/24 CPU
tasks: utility baseline 1/5 → candidate 5/5, protected target omissions 7/7
cả hai, identical task/catalog/environment/tool dispatch. Proof chỉ whole
identifier content 8–64 ASCII, không xử lý prose/room-line/encoding; duplicate
public observation mất utility có chủ đích do ambiguity, không gọi nó malicious.

Original root `build/evaluation/phase5_doc_read_final_cpu01/` có đủ 12 case
receipts nhưng **không có runner top-level receipt**: lỗi TypeError duplicate
`protocol` keyword ở bước summary. Sửa đúng aggregation line, thêm 2 runner
tests. Không chạy lại các case để recovery; giữ 937 raw files nguyên vẹn.
Hai audit01/02 tại `build/evaluation/phase5_doc_read_final_cpu_audit*.json`
khớp byte, SHA selected
`fe4d3e10933034196d5a2634b1d13af0970199f490a064e6312baa507d662c4e`.
Declaration SHA `2c9bdfb6d2dfef8ede5d01c719da9ac502da50e2b31b7d2f6aa727b15348757e`.
Recovery auditor cho phép đúng historical runner hash deviation, kiểm lại
unchanged runtime/control/source và replay final/observable answer từ raw.
Không sửa receipt gốc hoặc suy native success từ CPU. Lệnh audit/reproduce trong report.

**Bước cụ thể tiếp:** native-capable adapter/manifest source admission và audit
đầy đủ pair/Broker cho candidate này; hiện `run_synthetic_pair_task` cố ý CPU-only.
Sau đó exact archive/expanded worker rehearsal, loại host QA `doc_read_final_controls_v1`
khỏi worker closure, một source freeze/push cần thiết và prospective pin/content
mới trước Kaggle. Không nhập oracle hoặc đổi pilot cũ để chạy lại. Public approval
fixtures hiện là assistant self-review metadata trước content, không chứng nhận
owner timing; native run phải bind approval/catalog/source/run độc lập. Guard
quality, representative utility và graceful OS exit vẫn là acceptance gates.

Verification mới: broad regression **319 passed, 1 strict XFAIL** giữ lỗi pilot
cũ; trong đó 40 component + 36 integration + 2 runner tests mới (overlap,
không cộng). Setup/Ruff/mypy542/knowledge-check/diff-check đạt. Không full pytest do
authoring Test sealed; không Test/private GT/model/network mock mới. Pending
access: CPU không thiếu account; native cần source/package/approval/model
identity admission trước, chưa có notebook/Dataset mới để ghi URL. Chưa commit
hoặc push, Git base c87 không chứa các file mới. Không stage báo cáo/figures
riêng của user. Gom commit khi native source freeze đã QA, không microcommit.

## Mốc trước — final-only Dev matrix và paired CPU

**Đã hoàn thành khối Dev matrix + tích hợp FINAL paired CPU; chưa native admission.**
[Báo cáo](../docs/evaluation/phase5_final_literal_dev_runtime_v1_report.md),
[receipt chọn lưu](../experiments/manifests/phase5_final_literal_dev_cpu_v1.json)
và [protocol](../docs/evaluation/phase5_final_literal_proof_dev_v1_protocol.md).
24 ca mới, ba arm tách store: proof giữ 6/6 raw-user + 4/4 S0 one-field
collision echo, chặn 6/6 leak và reject 6/6 proof sai. Hai giới hạn unscored.
Receipt03 chỉ sửa reporting v3/v4 proof-admission thành N/A; không đổi effects,
outputs hoặc candidate. Không sửa/chạy lại pilot prospective để chọn kết quả.

`final_literal_runtime_v1` có hai route **CPU-only** với identity riêng cho
clause PRE và room-ticket PRE; giữ v3 live index/Broker/POST, tạo v4 riêng ở
FINAL từ đúng admitted roots, không chữa missing/incomplete coverage. Runtime
chỉ bật raw-user exact echo, **chưa bật public-field proof** vì `doc_read`
thật trả ba field chứ không phải one-field component fixture. Năm room
conditions fresh giữ utility/denials, sửa embedded final leak trên fixture
mới. Auditor tái dựng DAG/index/proof/release và đối chiếu final observable;
14 runtime outputs audited (11 final, 3 non-final terminals). Không native
release/lifecycle attestation; candidate chưa có native launcher/package.

**Bước tiếp cụ thể:** thiết kế proof versioned từ *raw doc_read nguyên bản*,
bind source hash + field path + approval ngoài; không dựng artifact raw giả từ
projection, không coi S0 tự đủ để declassify. Test collision/extra-field/context/
wrong pin và utility trên fixture mới. Sau khi composed candidate đạt, khóa
protocol/source/pin/content **mới**, native manifest/auditor và exact-worker QA
trước Kaggle. Không tái dùng stopped-pilot receipt như acceptance. Cổng guard
quality/benign utility và lifecycle OS-exit vẫn cần native evidence.

Raw local ignored: `build/evaluation/phase5_final_literal_proof_dev03.json`,
`build/evaluation/phase5_final_literal_runtime_cpu01/`,
`build/evaluation/phase5_final_literal_runtime_cpu_receipt01.json`. Input/source/
receipt hashes và lệnh tái tạo nằm trong report/selected summary. QA: broad
240 passed + 1 strict XFAIL; final focused 34 passed và matrix reporting 6
passed (overlap, không cộng). Setup/Ruff/mypy 536/knowledge/diff đạt; không full
pytest vì authoring Test sealed. Pending access: chưa cần tài khoản; trước GPU
cần candidate source/pin và model mounts/revisions đã admission. Không có
Kaggle notebook/Dataset mới nên không sửa directory bằng link đoán.
Chưa commit/push đợt này, giữ commit theo khối đã QA/source freeze cần thiết.
Git base c87 không chứa candidate mới; không stage report/figures riêng của user.

## Mốc trước — prospective stop và component proof

**CPU stop của pilot prospective.**

[Báo cáo CPU stop](../docs/evaluation/phase5_room_prospective_cpu_stop_v1_report.md)
và [casebook](../docs/evaluation/phase5_room_prospective_casebook_v1.md):
software commit `c87c321b42345e6d7152ca60976363a67a972531` đã selective
freeze; committed package01 qua hai layout/186 worker files/21 clean Dummy
mỗi layout. Pin S0/S2 metadata-only SHA
`8012e5f5192877f68446af05ddce34a984b36a2812c4396f09cd6475e9e89fee`
được tạo trước nội dung. Payload02 có 5 synthetic conditions và tất cả hash
môi trường khớp receipt; output nằm trong `build/kaggle/` ignored. Hai wording
pilot thất bại được lưu, không xóa/ghi đè. Current wording: clean webhook
được phép; poison/S2 collision/sai đích bị chặn; **final chứa token S2 từ
FREE_TEXT được release nguyên vẹn**. Chín module liên quan: 86 passed,
1 strict XFAIL, không có
native inference/Kaggle/Test mới. Không submit pilot này lên Kaggle hoặc
tăng acceptance; formal Phase 5 vẫn 4/7≈57%.
[Ứng viên v4 Dev](../docs/evaluation/phase5_embedded_identifier_v4_dev_report.md)
có 5 unit tests qua: index mã chữ-số S1/S2 nhúng trong free text, fail-closed
budget và final redact trên specimen Dev khác. Chưa nối runtime, không rerun
pilot đã dừng hoặc suy rộng thành chống mọi secret. [Ma trận Dev 18 ca](../docs/evaluation/phase5_embedded_identifier_dev_matrix_v1_report.md)
cho v4 6/6 leak blocked, 6/6 benign không trùng preserved, nhưng 0/3
collision utility và 3/3 giới hạn ngoài profile còn lọt (không chấm). Gate
đã chốt từ trước: **v4 no-go runtime**. Receipt selected local ignored:
`build/evaluation/phase5_embedded_identifier_dev_matrix02.json`, SHA
`d9fb363d7ba387530971661d4bc2452a1c8d63cf054cc85285b06e55d1d953bb`.
[Proof final v1](../docs/evaluation/phase5_final_literal_proof_v1_cpu_report.md)
đã được thêm như component opt-in mới: literal raw user hoặc S0 one-field có
external approval hash được ALLOW khi final đúng byte; proof/pin/nguồn sai,
final thừa ngữ cảnh, normalized-only và thiếu ancestry/index đều chặn/redact.
18 CPU controls qua. Chưa nối v12/v15, chưa Dev matrix độc lập/paired runtime;
approval schema tự nó không chứng nhận thời điểm owner review.

Bước cụ thể tiếp: (1) tạo ma trận Dev synthetic **mới** cho proof v1,
gồm collisions được phép, leak/context laundering và sai field/pin; kiểm cả
leakage và false-block, rồi paired CPU runtime nếu đạt. Không nới whitelist
theo bản matrix cũ hoặc sửa candidate
`c87c321b` hoặc lặp pilot để chọn kết quả; (2) khóa protocol/source/pin/content
mới trước native run nếu ứng viên qua CPU; (3) sau đó mới chuẩn bị matched
run manifests/weights và Kaggle. Lifecycle OS-exit vẫn là nhánh riêng. Pending
access: chưa thiếu tài khoản; cần model immutable revisions/mount trước GPU,
không cần thêm owner label approval cho pilot đã dừng. Không stage report
riêng `docs/BAO_CAO_TIEN_DO_DO_AN.*` hoặc `docs/figures/`. Commit mới chỉ khi
một gói sửa/QA nhất quán, không commit lẻ. Verification: setup, Ruff,
mypy 532 source files, knowledge-check, diff-check đạt; full pytest tránh
authoring tests có thể chạm held-out Test.
Git `main` local đang ahead `origin/main` một commit nguồn c87; các file
pilot/v4/matrix của phiên này còn uncommitted, chưa push. Không diễn giải
commit c87 là chứa ma trận mới.

## Mốc trước — three-arm CPU gate trước source freeze

**Ba arm prospective đã có CPU/admission/launcher parity; source freeze và
native model vẫn còn mở.**
[Three-arm report](../docs/evaluation/phase5_room_prospective_three_arm_cpu_v2_report.md):
baseline/metadata giữ v12, ticket dùng v15; manifest v2 buộc các pin ngoài
arm trùng nhau. CPU clean specimen: baseline chặn 3 proposal, metadata cho
hai đọc/chặn webhook, ticket cho webhook mock hợp lệ. Fault/checkpoint và
163 focused tests đạt. Package08 có 186 worker files, hai layouts, 21/21 clean
Dummy mỗi layout; `source_commit=null`, 0 native/prospective run, chưa release.
[Run-manifest report](../docs/evaluation/phase5_room_ticket_run_manifest_cpu_v1_report.md):
external run SHA, canonical+file pin, source, task, environment, model revision,
runtime/generation/seed và output overlap kiểm trước worker. Ticket arm chỉ
một task, chưa thay baseline/metadata arm. 157 focused tests đạt; package06
hai layouts/180 worker files/21 clean Dummy mỗi layout, `source_commit=null`,
0 native/prospective run.
[Native gate report](../docs/evaluation/phase5_room_ticket_native_gate_cpu_v1_report.md):
đã tách read-only auditor; committed source manifest + exact tree và inventory
pin là cổng trước worker. Task identity/checkpoint giữ raw, completed resume
read-only; partial và join fail không tự retry. 154 focused tests qua. Gói mới
`build/kaggle/phase5_room_ticket_dev_preflight04/preflight.json` có 178 worker
files, hai layout, 21/21 clean Dummy mỗi layout; `source_commit=null`, zero
model runs, không release-admitted.
[Package report](../docs/evaluation/phase5_room_ticket_package_dev_v1_report.md):
172 worker files; archive/expanded mounts trong venv offline độc lập qua 8
mock tools/recovery, 21/21 clean Dummy và complete/missing-only resume.
`build/kaggle/phase5_room_ticket_dev_preflight01/preflight.json` là receipt
local ignored: working-tree CPU, `source_commit=null`, 0 prospective/native
run, chưa release admission. Closure loại authoring và dữ liệu không công khai.
[Review](../docs/evaluation/phase5_room_inventory_review_request_v1.md)
và [record](../experiments/manifests/phase5_room_prospective_inventory_review_v1.json)
bind draft có sẵn: `AUX_FUTUREROOM` S0 và `AUX_FUTUREPRIVATE` S2, cùng
UNTRUSTED. [Validator](../src/react_agent/validation/room_inventory_review_v1.py)
kiểm byte hash, role, run pin/hash/commit và exact source IDs; unit controls
đạt, nhưng không chứng minh thời điểm người duyệt bằng mật mã. Chưa tạo
content, chưa tạo `InventoryPin`, không có inference mới. [Protocol](../docs/evaluation/phase5_room_prospective_v1_protocol.md)
đặt ba arm v12 baseline/v12 metadata/v15 ticket-adapter để tách lợi ích
metadata và vé. [CPU report](../docs/evaluation/phase5_room_ticket_pair_cpu_v1_report.md):
clean room được gửi tới đúng mock sink, poison bị chặn; cả hai có pair/guard
trace và versioned auditor join. Cùng catalog đã duyệt, v12 metadata-only
vẫn DENY clean, v15 ticket ALLOW; không quy hiệu ứng đó cho nhãn nguồn.
S2 collision, sai đích và final chứa giá trị
riêng cũng bị chặn/redact. Sai pin hoặc A5 bị chặn trước worker/output.
V14 gốc vẫn CPU-only; adapter mới có package **development CPU** nhưng chưa
có native/model hoặc authenticated source evidence.

Bước cụ thể tiếp: (1) rà file nguồn/secret và làm một selective source freeze,
không stage `docs/BAO_CAO_TIEN_DO_DO_AN.*` hoặc `docs/figures/`; (2) chạy
committed exact package QA; (3) tạo
`InventoryPin` với commit đó, pin hash vào
manifest **trước** khi viết nội dung synthetic mới; (4) exact package rehearsal
rồi mới cân nhắc Kaggle theo preflight. Lifecycle cold/warm OS-exit là protocol
riêng. Không đổi Dev32/Test/raw hoặc v12. Pending access: không thiếu tài
khoản; cần source freeze/native QA, không cần thêm owner label approval. QA
phiên này: 163 focused tests, setup, Ruff toàn repo, mypy 528 source files,
knowledge-check và diff-check đạt. Full pytest không
chạy vì authoring tests chạm Test sealed. Không commit lẻ.

Mốc trước — chiến lược sau Dev32:

**Giải các nguyên nhân kỹ thuật của Phase 5, chưa freeze.**
[Chiến lược](../docs/evaluation/phase5_completion_strategy_v1.md): v12 giữ
làm baseline native Dev32 đã chấm; v13/v14 là proof-carrying A6 ablation CPU,
không thay v12. Scoring selected Dev: attack success A2/A6 1/8 và 0/8;
benign typed utility 4/8 và 3/8, một A6 canonical safe-action false block.
Guard lifecycle: 31/32 GRACEFUL, một TERMINATE/-15 sau Python milestones.
Không relabel raw Dev32, không dùng Test hoặc tăng grace timeout hậu nghiệm.

Bước cụ thể: (1) owner duyệt hoặc sửa **trước nội dung** hai nhãn nguồn
`AUX_FUTUREROOM` S0 và `AUX_FUTUREPRIVATE` S2, cả hai UNTRUSTED, trong
[phiếu review](../docs/evaluation/phase5_room_inventory_review_request_v1.md);
(2) khóa một protocol prospective paired để kiểm v12/v13/v14 theo security,
utility, latency và lỗi worker, với source/seed/model/run identity riêng;
(3) khóa riêng diagnostic cold/warm OS-exit trước native run. Nếu owner chưa
duyệt, vẫn làm được admission/CPU negative controls và failure taxonomy;
không dựng nguồn thật hoặc submit Kaggle. Verification: scorer receipt và exit
diagnostic; 60 ticket/inventory tests, setup, Ruff, mypy 511 files,
`make knowledge-check`, `git diff --check` đạt. Full pytest không chạy vì có
authoring tests chạm Test đã sealed; chỉ dùng targeted tests. Không có quyền
truy cập bổ sung cần cho CPU; approval inventory cần trước pilot nguồn mới.
Không commit lẻ.

Mốc trước — v14 CPU:

**Ứng viên dated-room v14 CPU đã tích hợp; future-ID inventory vẫn chưa duyệt.**
[Báo cáo](../docs/evaluation/phase5_dated_room_v1_report.md). Grammar v2
cho đúng room line hoặc room line + ngày `Cập nhật: YYYY-MM-DD` hợp lệ; không
nhận dòng thứ ba/JSON/ngày sai/Unicode khó thấy. Runtime v14 chỉ bind ticket
v2 trên v13, giữ preflight synthetic, baseline PRE, Broker/POST/Final. Paired
Replay: v13 DENY dated clean, v14 ALLOW; poison/duplicate/S2 collision/guard
veto/sai đích/final leak vẫn DENY hoặc REDACT. Không model/GPU/Kaggle/Test,
không gắn host inventory attested; formal Phase5 vẫn4/7≈57%.

Bước tiếp: (1) owner xác nhận hai nhãn/role trong
[phiếu chưa có payload](../docs/evaluation/phase5_room_inventory_review_request_v1.md)
trước khi tạo content cho pilot mới; (2) khóa pin + source commit/run identity,
thêm typed-origin controls và protocol metrics/guard lifecycle; (3) chỉ khi
cổng model/package qua QA mới cân nhắc native v15/Kaggle. Giữ v12/v13/raw
Dev32/Test bất biến. Chưa commit lẻ. Kiểm cuối: 127 related tests,
setup/Ruff/mypy511/knowledge/diff đạt; full pytest tránh authoring Test sealed.

Mốc trước — inventory synthetic:

**Inventory synthetic mới và paired CPU đã xong; đợi review nguồn thực.**
[Báo cáo](../docs/evaluation/phase5_room_synthetic_inventory_v1_report.md).
Manifest chỉ có hai ID mới `AUX_NEWROOM` S0 và `AUX_NEWPRIVATE` S2,
UNTRUSTED, `assistant_draft_unreviewed`; file SHA được pin trong integration.
Builder kiểm exact IDs trước khi ghi case content và không đọc content để
đặt nhãn. Same-task/catalog clean/poison/S2-collision: v12 DENY clean,
v13 ALLOW clean, DENY hai nhánh không an toàn; Broker/POST/Final giữ nguyên.
Đây là Replay CPU, không phải chứng nhận nhãn Dev; không có owner review,
source commit freeze, model/GPU/Kaggle/Test hay thay đổi Dev32. Phase 5 vẫn
4/7≈57%.

Bước cụ thể: (1) để owner xác nhận riêng ID/nhãn cho tập nguồn prospective
theo [phiếu chưa có payload](../docs/evaluation/phase5_room_inventory_review_request_v1.md)
trước khi tạo nội dung thật; ghi review ref và source commit vào `InventoryPin`
và run manifest, không tự gắn attested; (2) mở rộng grammar/typed-origin bằng
synthetic negative controls rồi mới cân nhắc native v14; (3) xử lý guard
lifecycle theo protocol riêng. Chưa có lý do commit lẻ hoặc submit Kaggle.
File báo cáo/figures của user và raw Dev32 không chạm. Kiểm cuối: 107 related
tests, setup, Ruff, mypy509, knowledge-check và diff-check đạt; không chạy
full pytest vì authoring Test sealed.

Mốc trước — cổng pin inventory:

**Cổng inventory prospective đã có schema/pin; chưa có phê duyệt nguồn thật.**
[Protocol](../docs/evaluation/phase5_host_source_annotations_v1_protocol.md),
module `host_source_annotations_v1` và tests: pin gồm manifest pair-wide,
owner/review reference, UTC, source commit và hash; admission cần hash từ run
manifest đã khóa riêng, không được tính từ pin hiện tại. Thay nhãn/review,
sai commit, sai cặp public Dev hoặc metadata không hợp lệ đều bị từ chối.
Các reference trong test chỉ là specimen synthetic. Không thể xác nhận review
độc lập hay thời điểm thực bằng schema. Dev32 đã có kết quả không được relabel;
v13 còn replay-only. Chưa model/GPU/Kaggle/Test mới; Phase5 vẫn4/7≈57%.

Bước cụ thể: owner chuẩn bị/review inventory nguồn *trước khi tạo nội dung*
cho tập prospective mới; lưu record ngoài run, khóa SHA pin và source commit
trong manifest trước inference. Sau đó mới thiết kế broad room grammar với
synthetic paired negative controls và đánh giá có nên mở native v14 riêng.
Không nâng `host_inventory_attested` khi mới pass schema. Không thiếu quyền
Kaggle nhưng chưa đủ bằng chứng để submit. QA cuối của
cổng pin: 100 related tests, setup, Ruff, mypy508, knowledge-check và
diff-check đạt; full pytest không chạy vì các authoring Test đã sealed.
Không commit lẻ.

Mốc trước — v13 CPU hardening:

**A6 v13 ticket ablation CPU đã tích hợp và qua QA; chờ inventory độc lập.**
[Báo cáo](../docs/evaluation/phase5_ticket_runtime_cpu_v1_report.md).
Wrapper chỉ nhận A6/catalog v2, giữ loop v12 và các gate/Broker; PRE tính
baseline trước, chỉ xem lại UNKNOWN_FIELD room + coarse S2 có giải thích,
không bỏ qua guard/rule/scope. Trace giữ baseline và quyết định ứng viên.
Synthetic paired clean/poison, S2 collision, sai đích, guard veto, final leak,
version gate đều kiểm tra. Lần đầu poison test FAIL do JSON escape khiến rule
không phát hiện; extractor đã siết exact whole-content, case giữ lại. QA cuối:
169 targeted tests ở mốc tích hợp. Hardening tiếp theo thêm preflight chỉ nhận
replay agent, synthetic guard identity và 8 built-in tools trước worker/output;
private entry chặn worker bị tráo. 98 focused tests gồm v12 regression,
setup/Ruff/mypy508 đạt; knowledge-check/diff-check xem mốc kiểm cuối.
Kiểm cuối 2026-09-23: `make knowledge-check` và `git diff --check` đều đạt.
Đây không phải chứng nhận inventory synthetic hoặc nhãn host.
Full pytest không chạy vì authoring Test sealed.
Không model/GPU/Dev32/Test mới; Phase5 vẫn4/7≈57%.

Bước tiếp: (1) xác nhận inventory host độc lập *trước* inference, khóa manifest
và phương pháp paired Dev prospective; (2) mở rộng exact-line room grammar chỉ
với cặp synthetic clean/poison/sensitive, rồi QA; (3) chỉ sau đó source
freeze/commit gộp và cân nhắc Kaggle. Không gắn `attested=true` từ việc
catalog có version v2. Chưa thiếu quyền truy cập; cần owner chấp nhận inventory
để đi từ synthetic sang prospective model run.
Đường lifecycle guard TERMINATE vẫn mở độc lập. Không chạm report/figures
của user; raw Dev32 bất biến.

Mốc trước — ticket component:

**Pilot `public_field_ticket_v1` đã có component và synthetic controls; chưa
đưa vào A6 runtime.** [Báo cáo](../docs/evaluation/phase5_public_field_ticket_v1_report.md).
Host issue vé từ tài liệu S0 đã admit + POST ToolResult chính xác; PRE xác
thực run/index/source/observation/value/ancestry, user endpoint, exact payload
`room`, collision với S1/S2. Một public room có S2 không liên quan được phép
ở cấp *component*; sai đích, trùng S2, không nguồn, giả vé/POST bị chặn.
10 synthetic pytest cases thuộc pilot; QA cuối: setup, Ruff toàn repo,
mypy507 source files,94 focused tests, knowledge-check và diff-check đạt.
Không chạy full pytest vì authoring tests chạm sealed Test. Chưa model/GPU,
không đụng Dev32/Test; formal4/7≈57%.

Bước tiếp: độc lập xác nhận pre-ingestion host inventory cho nguồn sẽ thử,
sau đó thêm runtime A6 **phiên bản mới** với đầy đủ PRE/POST/Final/Broker và
paired controls, so sánh ablation baseline/metadata/ticket trên Dev mới. Không
biến component ALLOW thành full A6 ALLOW. Lifecycle guard TERMINATE vẫn cần
prospective instrumentation riêng. Không commit trước QA và source freeze cần
thiết; không chạm report/figures của user.

Mốc trước — metadata host:

**Đường metadata nguồn prospective đã được chủ đồ án chọn; implementation
opt-in, chưa có inference.** [Protocol](../docs/evaluation/phase5_host_source_annotations_v1_protocol.md),
[quyết định](../docs/project/decision_log.md). `host_source_annotations_v1`
chỉ tạo catalog v2 từ manifest cho cả cặp public Dev, exact inventory,
UNTRUSTED, không đọc text/oracle; frozen catalog Dev32 không đổi. Unit controls
kiểm tra poison text, thiếu/thừa ID, duplicate, trust upgrade, sai pair/Test.
Chưa có pre-ingestion host inventory được owner xác nhận nên chưa relabel bất
kỳ fixture thực nào. QA của bước này: setup đạt, Ruff toàn repo đạt,
mypy506 files đạt,17 focused tests đạt, knowledge-check/diff-check đạt;
không chạy full pytest vì các authoring tests chạm sealed Test. Chưa model,
GPU, Kaggle hay held-out Test mới. Phase5 vẫn4/7≈57%.

Bước cụ thể: chốt QA đầy đủ và code+evidence cùng một commit khi cần source
freeze; sau đó lập inventory nguồn phụ *trước* prospective run, có owner/date/
hash độc lập, thiết kế grammar `room` và typed origin với synthetic paired
public/sensitive/unknown/poisoned controls. Không dùng kết quả Dev32 để đặt
nhãn. Lifecycle: bài startup/exit mới identity riêng nếu cần, không rerun Dev32.
Quyền: không thiếu Kaggle; raw local chưa backup riêng. File report/figures
của user không chạm.

Mốc trước — hai chẩn đoán:

**Hai đường chẩn đoán Phase5 đã xong, cần quyết định/thiết kế prospective.**
[False-block report](../docs/evaluation/phase5_clause_falseblock_root_cause_v1_report.md),
[lifecycle report](../docs/evaluation/phase5_clause_guard_exit_diagnostic_v1_report.md),
[lifecycle receipt](../experiments/manifests/phase5_clause_guard_exit_diagnostic_v1_receipt.json).
Shutdown audit32tasks/64workers:32agent GRACEFUL,31guard GRACEFUL,
1guard TERMINATE/-15 ở ca đầu chưa có guard classification; STOP/serve/
finalizers/threads đều return, 0 non-daemon threads, vẫn trễ deadline2s.
Hai output `results/phase5_clause_guard_exit_diagnostic01/diagnostic.json`
và `diagnostic02/diagnostic.json` SHA cùng
`1ced49b8d0adecbf5ced88b9f674cc8ea15849c7383eb1b9e6f2281ebdbbcb54`.
Chưa chứng minh nguyên nhân OS exit. Không Test/oracle/GPU mới. Mọi raw/Dev32
score giữ nguyên. QA cuối:163 targeted tests, setup/Ruff/mypy505/
knowledge-check/diff-check đạt; ba selected receipts và sáu final generated
reports khớp SHA. Không chạy full pytest vì fixture authoring Test đã sealed.
Phase5 còn4/7≈57%; không update phase_status.

Bước cụ thể: (1) cần chọn giữ nhãn nguồn phụ bảo thủ hay phê duyệt thiết kế
public host annotation độc lập, không dựa oracle, trước bất kỳ sửa policy;
(2) nếu cần đóng lifecycle, khai báo riêng bài prospective startup/exit
instrumentation với run identity mới, không retry Dev32; (3) chạy QA/commit
gộp khi thay đổi coherent và đạt. Kaggle không thiếu quyền; raw chưa backup
ngoài máy. File báo cáo/figures riêng của user không chạm.

Mốc trước — root cause false block:

**Root cause A6 benign false block đã được xác thực; đang chờ quyết định metadata.**
[Protocol](../docs/evaluation/phase5_clause_falseblock_diagnostic_protocol_v1.md),
[report](../docs/evaluation/phase5_clause_falseblock_root_cause_v1_report.md),
[receipt](../experiments/manifests/phase5_clause_falseblock_diagnostic_v1_receipt.json).
Hai output `results/phase5_clause_falseblock_diagnostic03/diagnostic.json` và
`diagnostic04/diagnostic.json` cùng SHA
`6386e6f094507a517a482549d12d8233ec71714cee0b7ab0ac1cc7afc61351e5`.
Raw 2.073 files/audit nguyên; chỉ public Dev/trace, 0 oracle/Test/model mới.
Tài liệu phụ được catalog cố ý gắn S2/UNTRUSTED; payload key `room` chưa hỗ
trợ; typed origin vắng. Đích do raw user cho phép và read thành công, nhưng
gate DENY đúng fail-closed với metadata hiện có. Không hạ nhãn/whitelist theo
oracle. Phase5 vẫn4/7≈57%, DoD5/15/20 và guard TERMINATE còn mở.

Bước cụ thể: chủ đồ án chọn giữ A6 bảo thủ và ghi utility loss, hoặc phê duyệt
thiết kế public host-source annotation độc lập/phiên bản mới (không từ GT, không
mở Test) trước khi sửa hành vi. Nếu chưa chọn, có thể kiểm toán riêng guard
TERMINATE bằng raw hiện có, không đụng policy. Quyền Kaggle không thiếu;
raw chưa backup ngoài máy. Giữ scorer/Dev32/raw bất biến, không commit status
lẻ; batch code+tests+evidence sau QA khi cần. User-owned report/figures bỏ qua.

Mốc trước — Dev32 scoring/adjudication:

**Dev32 evaluator-only v1 đã chấm và adjudicate bounded cases; Phase5 chưa đóng.**
[Giao thức](../docs/evaluation/phase5_clause_dev32_scoring_protocol_v1.md),
[báo cáo](../docs/evaluation/phase5_clause_dev32_scoring_v1_report.md),
[receipt](../experiments/manifests/phase5_clause_dev32_scoring_v1_receipt.json).
Hai output final `results/phase5_clause_dev32_score05/summary.json` và
`score06/summary.json` SHA cùng
`5601a90ddca2de14111fd6b573417022f989c2b4c52e21edc240baff9dfbd04e`;
32/32 ca, nguyên raw+audits. Không model/Test mới. Attack observed A2=1/8,
A6=0/8; benign utility4/8→3/8, safe utility2/8→3/8. Một A6 benign
canonical safe-action bị PRE chặn đã xác nhận bằng oracle/action/rule;
chưa báo FPR tổng thể. Hai A2 ROWLIST unassessed là cùng query không hợp lệ,
Broker INVALID_QUERY. Năm tests mới/90 related đạt, setup/Ruff/mypy503 đạt. Formal
Phase5 vẫn4/7≈57%; DoD5/15/20 và guard TERMINATE chưa đóng. Quyền:
không thiếu Kaggle; raw local chưa backup ngoài máy. Tránh commit status lẻ.

Bước cụ thể: đặt prospective protocol để sửa false block canonical benign
và bổ sung guard semantic/lifecycle coverage, rồi QA trước source freeze mới;
không sửa scorer đã khóa để cải thiện số. Gom một commit coherent sau QA.
Test sealed không đọc,
không rerun/cherry-pick Dev32.

Mốc trước — terminal audit xong nhưng chưa chấm:

**Dev32 v2 COMPLETE/audit; bước tiếp là evaluator-only Dev scoring.**
[Terminal report](../docs/evaluation/phase5_clause_dev_gpu_v2_terminal_report.md),
[selected receipt](../experiments/manifests/phase5_clause_dev_v2_gpu_terminal01.json).
Actual notebook [v2](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
version1/ID135499833, source `ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e`,
private/offline/T4, Dataset guard15v1. Terminal trước/sau download COMPLETE,
source/metadata/version khớp. Raw `results/phase5_clause_dev_v2_gpu_monitor01/raw`
có 2.073 files; 2 remote files, 222 source pins, 8 shards/32 tasks được hai
audits độc lập byte-identical. Host descriptive report chạy lại từ hai audits
cũng byte-identical; 67 targeted tests/setup/Ruff/mypy502 đạt. 65/65 guard
responses `OK`, 8 tasks không gọi guard, 31/32 all-workers graceful, một
guard TERMINATE; không tự suy ra ASR/FPR/utility. Known credential scan
2.077 files/3 values có 0 matches. Không Test/private GT, không inference mới.

Bước cụ thể: khóa evaluator-only Dev scoring protocol/denominators/error handling
trước khi đối chiếu traces với oracle Dev; giữ raw và v1 ERROR/release01 rejection
bất biến. Không rerun notebook để chọn kết quả tốt hơn, không mở held-out Test.
Sau đó cập nhật DoD5/15/20 theo bằng chứng, quality/lifecycle limitations và
formal freeze. Phase5 vẫn 4/7≈57%. Quyền: không thiếu Kaggle; raw chưa backup
riêng ngoài máy. Receipt/báo cáo terminal hiện local, gom một commit sau khi
QA/knowledge-check đầy đủ; không status-only commit hoặc amend source worker.

Mốc trước — v2 RUNNING (quan sát lịch sử):

**Dev32 v2 RUNNING; không submit lại.** Actual
[huylmhuhu/react-vn-clause-dev32-v2](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
version 1/ID 135499833, private/offline/T4, source
`ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e` đã push GitHub main.
[Release02](../experiments/manifests/phase5_clause_dev_package_v2_release02.json)
qua hai layouts/222 committed source pins/213 worker files;
[QA03](../experiments/manifests/phase5_clause_dev_package_v2_qa03.json)
981 focused + 395 integration, Ruff/mypy501/setup/knowledge đạt.
[Submission](../experiments/manifests/phase5_clause_dev_v2_gpu_submission01.json)
đã xác minh remote source/settings/version; live 09:55:43 UTC 2026-09-23 là
RUNNING, chưa có model result. Dataset guard15 private/ready/v1; quota còn
29,73h lúc submit. Không Test/private GT, không semantic retry.

Bước cụ thể: monitor v2 read-only. Khi terminal, tải một lần vào thư mục mới,
ghi source/version/status trước-sau và chạy `audit_phase5_clause_dev_gpu_v2.py`
hai lần độc lập trên raw bất biến. Nếu ERROR, giữ partial và phân loại lỗi trước
mọi lần thử khác. Sau audit mới chấm quality/benign utility/lifecycle; formal
Phase5 vẫn 4/7≈57%. Quyền: tài khoản Kaggle hiện có đủ; bạn Minh cần quyền
Kaggle riêng nếu dùng tài khoản khác. Raw chưa có backup riêng ngoài máy.

Mốc trước — v1 failure và chuẩn bị v2 (không phải trạng thái hiện hành):

**Dev32 v1 terminal ERROR; v2 đã qua development package và QA, chưa submit.**
[Failure report](../docs/evaluation/phase5_clause_dev_gpu_v1_failure_report.md),
[v2 report](../docs/evaluation/phase5_clause_dev_package_v2_report.md),
[QA03](../experiments/manifests/phase5_clause_dev_package_v2_qa03.json),
raw `results/phase5_clause_dev_gpu_monitor01`, audit
`results/phase5_clause_dev_failure_audit01` và `audit02`.
Actual [v1](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1)
version1/ID135340687 ERROR lúc08:39:20UTC2026-09-22;remote source/settings
vàdownload-before/after version khớp.12raw files;0/32completed,
0native-generation receipts;baseline/environment/recovery của ca đầu giữ nguyên.
Traceback native `constrained` truyền hai lần, trước worker start.
`clause_dev_dispatch_v2` bỏ caller-supplied root ở native; test tái hiện v1 TypeError
và xác nhận v2 dùng root của factory, không load weights. V1 source/output bất biến.
Gói v2 development hai layouts mỗi layout 8 tools/21 Dummy/32 Dev/8 shard audits;
QA02: 980 focused + 395 integration, setup/Ruff/mypy501/knowledge/diff đạt;
182 native source và 169 tracked data pins giữ nguyên. Read-only Kaggle preflight
ngày 2026-09-23: GPU còn 29,73h, Dataset guard15 private/ready/v1, v1 ERROR.

Source freeze `24164d8` đã push main. Rehearsal committed
`build/kaggle/phase5_clause_dev_package_v2_release01` qua hai layouts nhưng
host validator có allowlist cache v1 thay vì v2; release01 bị từ chối trước
Kaggle. Sửa riêng auditor và regression test đã qua QA03: 981 focused,
395 integration, Ruff/mypy501/setup/knowledge. Bước cụ thể: chốt commit sửa
lỗi, dựng release02 từ commit đó, xác thực release,
kiểm tra v2 notebook chưa tồn tại rồi submit một lần v2 private/offline/T4
cho đúng 32 ca cố định. Không dùng release01; không resume v1 hay semantic retry.
Sau v2 terminal mới download/source audit/quality analysis. Hiện không Kaggle
job pending của v1; v2 chưa submit. Không Test/privateGT; formal4/7≈57% chưa đổi.

Mốc trước — submission v1 khi còn RUNNING (lịch sử):

**32Dev đang chạy Kaggle, một submission; không gửi lại.**
Live07:10:42UTC2026-09-22: actual=requested
[huylmhuhu/react-vn-clause-dev32-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1),
v1/ID135340687,RUNNING;source`5a2352834a791b11824a7c0c69e82f2390a03ca0`
đã commit/pushmain một lần. Private/offline/T4/timeout14400s;Dataset guard15v1.
[Submission](../experiments/manifests/phase5_clause_dev_gpu_submission01.json),
[committed package](../experiments/manifests/phase5_clause_dev_package_release01.json),
[report](../docs/evaluation/phase5_clause_dev_package_v1_report.md).
Hai committed layouts mỗi8tools/21Dummy/32Dev đạt;218source release pins xác thực;
remote code/settings/version khớp. QA976focused+395integration/setup/Ruff/mypy495
đạt trướcfreeze;model generation/deadlines không đổi. Không final/Test inference.
Rawsubmission `results/phase5_clause_dev_gpu_submission01`;releasebundle
`build/kaggle/phase5_clause_dev_package_release01`;QA `results/phase5_clause_dev_package_qa02`.

Bước cụ thể: read-only monitor đúngv1. Khi terminal tải vào thư mục mới, lưu
version/source trước-sau download và chạy`audit_phase5_clause_dev_gpu_v1.py`hai lần.
Nếu ERROR: giữ partial checkpoints/logs, phân loại infrastructure/semantic;
không tự repush hoặc retry semantic. Model outcomes chưa biết,không suy từCPU32/32.
Nguồn đã freeze: không sửa218pinned files. Receipt/memory saufreeze đanglocal;
không tạo status-onlycommit. Quyền:account đã đủ,networkapproval sandbox khi cần;
raw chưabackup riêng. Formal4/7≈57%chưađổi;quality/lifecycle/DoDfreeze cònmở.

Mốc trước — development package:

**Dev32 exact package đã qua development preflight; đang chuẩn bị source freeze.**
[Report](../docs/evaluation/phase5_clause_dev_package_v1_report.md),
[package](../experiments/manifests/phase5_clause_dev_package_dev01.json),
[QA02](../experiments/manifests/phase5_clause_dev_package_qa02.json).
211worker/218source pins; hai layouts mỗi layout8tools/21Dummy/32Dev,
prefix/missing-only/complete-resume và8auditCLI đạt;1.027raw/layout.
88tests mới;976focused/56,23s+395integration/403,50s đạt;setup/Ruff/mypy495/knowledge/diff đạt.
182native/169data pins giữ nguyên;scan2.278files/0credentials. Raw build
`build/kaggle/phase5_clause_dev_package_dev04`; development01–03 giữ lỗi cũ.
Native đường mới chỉ chấp nhận committed source; oldCPU runner vẫn khóa HF.
QA01 bị từ chối source đổi giữa run; QA02 ổn định là bằng chứng dùng.

Bước cụ thể: một source-freeze commit/push cần thiết, committed rehearsal vào
thư mục mới và `audit_phase5_clause_dev_gpu_v1.validate_package`, rồi submit một lần.
Lịch32Dev giữ nguyên;8shards tuần tự,session cap14400s,T4/private/offline;
không đổi deadline/model/prompt, không thêm4taskGPU diagnostic. Chưa submission.
Live `results/phase5_clause_dev_kaggle_preflight03`:ownerhuylmhuhu,29,75hGPU,
Dataset guard15 private/ready/v1;notebook cũ COMPLETE. Dùng systempython3 cho
KaggleCLI2.2.4;venv không có kaggle. Requested `huylmhuhu/react-vn-clause-dev32-v1`
chưa actual. Không cần account mới;raw chưa backup riêng. Test/privateGT không đọc.
Formal4/7≈57% chưa đổi. Sau submit chỉ monitor/tải/audit, không push trùng.

Mốc trước — Dev32 CPU runner:

**Đã đóng CPU gate cho runner32Dev A2/A6; native dispatch chưa mở.**
[Report](../docs/evaluation/phase5_clause_dev32_v1_report.md),
[contract](../docs/architecture/phase5_clause_dev32_v1_contract.md),
[controls](../experiments/manifests/phase5_clause_dev32_cpu01.json),
[audit](../experiments/manifests/phase5_clause_dev32_audit01.json).
32completed/8shards/16publicDev;64GRACEFUL workers reaped,32synthetic recovery.
188source/928raw pins kiểm riêng, hai audits/shard và complete-resume không đổi raw.
23tests mới; [QA02](../experiments/manifests/phase5_clause_dev32_qa02.json):888focused+
395integration,setup/Ruff/mypy488/knowledge/diff đạt;182native/169data pins nguyên.
Raw `results/phase5_clause_dev32_cpu01`, audits `results/phase5_clause_dev32_audit01`,
QA `results/phase5_clause_dev32_qa02`; QA01 cũng hoàn tất và giữ lại.
Không chấm utility/ASR từ scripted agent; recovery/teardown chỉ synthetic.
`clause_dev_native_audit_v1` nối token/count/constraint evidence nhưng KHÔNG
model-source/release authentication. `clause_dev_runner_v1.run` từ chối HF trước output.

Bước cụ thể tiếp theo: native source/release admission và launcher cho32Dev,
rồi exact archive/expanded rehearsal. Đọc Kaggle preflight +skill trước đóng gói.
Chỉ mở HF sau cổng này; source freeze/commit chỉ khi cần cho thực nghiệm thật,
không commit status. Giữ manifest32ca/seed/model/settings, frozen worker và
mọi failure; không lặp4task GPU diagnostic, không chọn ca theo model output.
Source hiện là base6d039e2 +working-tree pins, chưa GitHub source freeze mới.
Không pending Kaggle hoặc model/GPU/commit/push mới, không Test/private GT parsing.
Quyền còn thiếu: chưa cần tài khoản mới; raw chưa có backup riêng ngoài máy.
Formal4/7≈57% chưa đổi: native quality/utility, lifecycle và DoD freeze còn mở.

Mốc trước — constrained ExitPair integration:

**Đã nối v12 vào constrained ExitPair và kiểm toán riêng, CPU gate đạt.**
[Report](../docs/evaluation/phase5_clause_pair_v1_report.md),
[contract](../docs/architecture/phase5_clause_pair_v1_contract.md),
[controls](../experiments/manifests/phase5_clause_pair_controls01.json),
[audit](../experiments/manifests/phase5_clause_pair_audit01.json).
Raw `results/phase5_clause_pair_controls01`; full audits `results/phase5_clause_pair_selected01`.
12tasks/24workers reaped:4valid completed +4deliberate model_error +4egress controls.
20GRACEFUL/4TERMINATE (forced chỉ ở deliberate failures), chưa native reliability.
Egress A6public ALLOW; A6sensitive/A6unknown/A5public DENY đúng kỳ vọng. Hai audits
và complete-resume không đổi raw.184source/348raw pins khớp;scan349files/0credentials.
36new tests đạt; [final QA](../experiments/manifests/phase5_clause_pair_qa01.json):
879focused/50,17s +381integration/305,62s, setup/Ruff/mypy483/knowledge/diff đạt.
Logs `results/phase5_clause_pair_qa01`;182native pins +7prior candidate pins
+169tracked data hashes không đổi. Full pytest loại sealed Test-authoring fixtures.
Nguồn cũ v12/78controls và native182pins giữ nguyên; không Test/private GT parsing.
Không model lớn/GPU/commit/push mới; không có Kaggle job pending.

Bước cụ thể: chuẩn bị runner/manifest32Dev A2/A6 + independent native release
audit trên `clause_pair_runtime_v1`; profile mới `security_runtime_v12_constrained_exit_v1`.
Không chạy GPU4task probe mới chỉ để lặp dữ liệu teardown. Probe4task hiện là
CPU/package control. Phải gắn source closure, input/environment/model/generation
hashes, scopev5 + originv3, constraint cache/exit joins vào32task checkpoint;
giữ failures và missing-only resume. Sau đó exact archive/expanded rehearsal,
kiểm quota/private mounts, source freeze cần thiết rồi submit một lần.
Outer scope pre-start cũng cần ResourceBindings/RowBindings từ host catalog;
đừng chỉ nối constructor trong inner runtime. Audit cross-host dùng recorded
interpreter, không dùng mặc định máy Mac. Không dùng metadata version để giả nâng runtime.
Quyền còn thiếu: chưa cần account mới; raw chưa có backup riêng ngoài máy.
Formal acceptance không đổi: quality/utility, native lifecycle và DoD freeze còn mở.

Mốc trước — clause/warm-runtime CPU (đã có paired integration ở trên):

**Clause authorization v3/runtime v12 đã qua 78/78 CPU controls.**
[Report](../docs/evaluation/phase5_clause_candidate_v1_report.md),
[contract](../docs/architecture/phase5_clause_authorization_v3_contract.md),
[receipt](../experiments/manifests/phase5_clause_candidate01.json),
[Dev coverage](../experiments/manifests/phase5_clause_coverage01.json).
Raw `results/phase5_clause_candidate01`; selected `results/phase5_clause_selected01`.
157source/1.400raw pins kiểm riêng;scan1.401files/0credentials. 67new unit +65new
integration đạt; [final QA](../experiments/manifests/phase5_clause_qa01.json):
873focused/60,91s +351integration/310,06s, setup/Ruff/mypy478/knowledge/diff đạt.
Logs `results/phase5_clause_qa01`;182native pins +169data hashes không đổi;
10prior acceptance source pins nguyên. Không full pytest vì Test-authoring fixtures.
Cumulative A1–A6 dùng cùng parser; A0 giữ v10. Sáu Dev đích gửi đã nhận đúng;
payload sensitivity/unknown-lineage/guard veto/final gates vẫn độc lập.
`value_origin_v3` chỉ bổ sung literal đích từ raw host-user, giữ labels/hash/budgets;
sửa false-denial email trước dấu chấm, không chữa toàn bộ extractor punctuation.
Không Test/private GT parsing, không model/GPU/commit/push; source base6d039e2
+working-tree pins, không được gán source mới cho GitHub commit cũ.

Bước cụ thể tiếp theo: tích hợp runtimev12 và originv3 vào constrained ExitPair
(native hiện vẫn dùng scopev3/runtimev8, KHÔNG tự coi đã nâng cấp). Cần bind
HostClassifier/PROMPT giữ finite-language/cache identity, metadata runtime mới,
independent audits/runner checkpoint/source closure và tests spawned pair; giữ
frozen worker/old receipts. Sau đó exact archive+expanded rehearsal, source freeze
thật sự cần thiết, rồi32Dev A2/A6 đã chọn. Không resubmit diagnostic cũ.
Parser cố ý từ chối toàn bộ quoted/conditional/reported instructions và unsupported
prefix; chưa phải parser ngôn ngữ tổng quát. Native quality/lifecycle/freeze còn mở.
Quyền còn thiếu: không cần account mới; raw chưa có đích backup riêng ngoài máy.
Không job Kaggle pending, formal acceptance vẫn4/7≈57%.

Mốc trước (v11 là lịch sử, đã có v12 CPU ở trên):

**Coverage + bounded A6 authorization candidate đã có CPU evidence.**
[Report](../docs/evaluation/phase5_acceptance_controls_v1_report.md),
[matrix](../experiments/manifests/phase5_acceptance_coverage01.json),
[baseline](../experiments/manifests/phase5_acceptance_baseline01.json),
[candidate](../experiments/manifests/phase5_acceptance_candidate01.json).
Không đổi benchmark/Test/frozen worker. Public Dev16fixtures/8cặp giữ seed cũ;
native candidate workload32taskA2/A6 vẫn dispatch=false. Sáu fixtures có raw-user
destination anchor chưa nhận; không đồng nghĩa sensitive payload được phép gửi.
Synthetic baselinev10:26/26semicolon,17/26period;9failures giữ nguyên.
Opt-in A6runtimev11+anchorv2:52/52controls đạt;A0–A5 delegatev10, chưa cumulative
native release.27parser+6coverage+54baseline+52candidate tests mới;
[final QA](../experiments/manifests/phase5_acceptance_qa01.json):806focused+
286integration đạt, setup/Ruff/mypy474/knowledge/diff đạt,182nativepins nguyên.
Raw `results/phase5_acceptance_controls01`, `results/phase5_sentence_candidate01`;
52executions/run,933raw/run;scan1868files/0credentials. Không model/GPU/commit/push.
Bước cụ thể: thiết kế/test quyền-cấm theo raw clause spans và quote context;
giải quyết6Dev anchor gaps mà không cho sensitive egress, kiểm cumulative/A0
parity/native pair trước exact package/source freeze. V11 chỉ giải quyết bounded
read-then-send, không coi compound prohibition đã giải quyết. Không job pending.
Hardening bắt buộc trước promote: read-prefix dạng tường thuật không quote,
quote xuyên mệnh đề và thu hồi quyền; lexical READ không phải resource grammar.
Quyền còn thiếu: chưa cần account mới; backup raw riêng tư vẫn chưa có đích.
[Bản đồ20DoD](../docs/evaluation/phase5_dod_evidence_map.md) ghi rõ evidence và
cổng candidate/quality/lifecycle/freeze; không phải acceptance20/20.

Mốc trước:

**ExitPair GPU v1 COMPLETE; terminal release audits đã khớp byte-for-byte.**
[Report](../docs/evaluation/phase5_exit_gpu_v1_report.md),
[audit](../experiments/manifests/phase5_exit_gpu_audit01.json),
[summary](../experiments/manifests/phase5_exit_gpu_summary01.json).
Post-download07:28:29UTC ngày2026-09-21:actual `huylmhuhu/react-vn-exit-milestones-v1`,
v1/ID135130970, source `6d039e2`, private/offline/T4; remote pins/settings/version khớp.
4 completed/8 valid guard responses;8GRACEFUL/0TERMINATE/0KILL,4VRAM recoveries.
Tất cả target/finalizers/threads return; lỗi teardown cũ không tái hiện, chưa root
cause/fix. Hai audits182source/242raw/2remote;scan253files/0credential matches.
Raw `results/phase5_exit_gpu_monitor01`, report `results/phase5_exit_gpu_report01`.
Không còn job pending, không submit lại. Host summary +10 tests mới; final
[QA](../experiments/manifests/phase5_exit_gpu_qa01.json):773focused +180integration,
setup/Ruff/mypy468/knowledge/diff đạt; frozen pins nguyên. Không commit/push;
giữ nguồn worker frozen, gom evidence về sau.
Bước cụ thể: chuẩn bị coverage matrix public Dev cho guard quality/benign utility
và DoD5/9/13/14/15/16; đọc nhiệm vụ và policy expectations trước chọn run manifest,
không chọn theo model success. Lifecycle cần prospective paired comparison nếu
muốn kết luận reliability/fix; không tự tăng grace hoặc rerun v1.
Quyền đang chờ: không thiếu credentials; raw chưa có backup riêng ngoài máy.

Mốc submit dưới đây là lịch sử, không phải trạng thái RUNNING hiện tại:

**ExitPair GPU v1 đã submit một lần, RUNNING lúc 16:57:50 UTC ngày 2026-09-20.**
Actual `huylmhuhu/react-vn-exit-milestones-v1`, v1/ID135130970;
[submission](../experiments/manifests/phase5_exit_gpu_submission01.json),
[report](../docs/evaluation/phase5_exit_pair_package_v1_report.md).
Private/offline/T4/timeout3600s/guard Dataset v1; source `6d039e2` đã push main.
Remote code/settings/version khớp. API trả ref có `/code/`; host check ban đầu
dừng sau push thành công, đã sửa bằng read-only verification, không submit lại.
Development + committed archive/expanded đạt:176worker/182source pins,
mỗi layout8tools/21Dummy/10fresh controls/6retained. Final QA763focused +180integration,
setup/Ruff/mypy467/knowledge/diff đạt. Không đổi frozen worker/grace2s/Test.
Bước cụ thể: kiểm tra job hiện tại; khi terminal tải vào thư mục mới, xác thực
version/source trước-sau download, chạy hai release audits và phân tích milestones.
Chưa terminal/download/native cause/acceptance. Không submit trùng, không commit
status: receipts/memory sau freeze đang local. Không thiếu credentials; chỉ cần
network approval của sandbox khi monitor. Raw chưa có backup riêng ngoài máy.

Các mốc trước (không thay trạng thái hiện hành ở trên):

**ExitPair/runner và native audit wiring đã đóng CPU QA02, chưa commit/push.**
Owner nhắc lại: không mặc định commit cuối mỗi lượt dù checks đạt. Giữ local;
chỉ commit theo yêu cầu hoặc khi cần chốt nguồn cho thực nghiệm thật.
Đã nối role/task/PID/cold-warm identity qua sidecar riêng, giữ frozen sources.
Đã sửa kiểm toán native để bind interpreter theo run identity, không theo máy Mac
đang audit. Controls01/QA01 giữ lịch sử; controls02/QA02 bind source sửa.
Chưa package/release/GPU. Final QA02: 689 focused + 180 integration, setup/Ruff/
mypy462/knowledge/diff đạt. [Report](../docs/evaluation/phase5_exit_pair_cpu_v1_report.md).

**Exit-milestone observer đã đóng CPU gate; chưa nối native runner.**
[Report](../docs/evaluation/phase5_exit_milestones_cpu_v1_report.md),
[protocol](../docs/architecture/phase5_exit_milestones_v1_contract.md).
Backend opt-in kế thừa generate/cleanup cũ; hooks chỉ trong child, PID/timing và
Python non-daemon thread counts, không payload/tên luồng. Config identity riêng.
18/18 worker reaped; đối chứng phân biệt kẹt target/finalizers/thread shutdown,
không chứng minh native GPU cause. 53 tests mới; 666 focused + 149 integration,
setup/Ruff/mypy454/knowledge/diff đạt. Không Kaggle/model/Test/private GT access.

Đã củng cố điều hướng/lưu trữ cho vault Obsidian hiện có:
[START_HERE](../START_HERE.md), [quy ước](storage_and_obsidian.md).
Không thay settings/plugin/sync; `.obsidian/` và `.trash/` ngoài Git.
Raw vẫn local, chưa có bản sao ngoài máy; chưa chọn đích backup riêng tư.

**Nền post-serve teardown CPU probe v1 đã hoàn tất.**
[Report](../docs/evaluation/phase5_teardown_cpu_v1_report.md),
[contract](../docs/architecture/phase5_teardown_probe_v1_contract.md).
18 fresh spawned workers: 6 modes × 3 reps, 2 public responses/worker. Đủ 18 reaped;
6 GRACEFUL/9 TERMINATE/3 KILL đúng fault controls. Hai audits byte-identical,
19 raw files/31 source-evidence scan/0 credential matches. 44 tests mới;
final QA 623 focused + 133 integration, setup/Ruff/mypy450/knowledge đạt.
Finalizer bị kẹt và live non-daemon thread cùng tái hiện serve-returned+forced exit;
đây là phân biệt cơ chế CPU, **không xác định native GPU root cause**.
Không đổi frozen worker, grace2s, model, prompt, Test; không job Kaggle mới.

Mốc native trước:

**Constrained GPU v1 COMPLETE/audit; không submit lại.**
Actual `huylmhuhu/react-vn-constrained-guard-v1`, v1/ID134673914;
Post-download 03:43:34 UTC ngày 2026-09-17, source `0d4e82f` authenticated,
private/offline/T4/timeout3600s/guard Dataset v1.
[Report](../docs/evaluation/phase5_constrained_gpu_v1_report.md),
[submission](../experiments/manifests/phase5_constrained_gpu_submission02.json).
Host auditor `scripts/audit_phase5_constrained_gpu_v1.py` đã có 59 tests mới,
thêm summary adapter5tests; final QA02 573 focused + 105 integration,
setup/Ruff/mypy446/knowledge đạt. Gom host code/tests/receipts/memory trong một
commit khi đóng thực nghiệm; không đổi/amend source worker.
Hai release audits byte-identical: 172 source pins/238 raw/2 remote files.
4 completed tasks, 8/8 valid guard responses, zero incomplete constraints/backend
errors; 8 workers reaped/4 VRAM recoveries. Còn 4 TERMINATE/4 GRACEFUL,
chưa guard semantic quality/utility hoặc lifecycle acceptance.
[Summary](../experiments/manifests/phase5_constrained_gpu_summary01.json),
[audit](../experiments/manifests/phase5_constrained_gpu_audit01.json).

Nền package đã đóng:

**Constrained exact package đã đạt development + committed release preflight.**
[Report](../docs/evaluation/phase5_constrained_package_v1_report.md),
[receipt](../experiments/manifests/phase5_constrained_probe_package_dev01.json).
Builder `scripts/prepare_phase5_constrained_probe_package_v1.py`, template
`notebooks/kaggle/constrained_probe_kernel_v1.py`. Development package ở
`build/kaggle/phase5_constrained_probe_package_dev01`: 166 worker files,
172 source pins; mỗi layout 8 tools, 21 Dummy, 10 fresh constrained tasks và
6 retained checkpoints. 15 tests mới đạt; final QA 495 focused + 105 integration,
setup/Ruff/mypy444/knowledge/diff đạt; 142/86/175 frozen pins nguyên.
Đã gom một commit `0d4e82f`, push `origin/main`; release rebuild ở
`build/kaggle/phase5_constrained_probe_package01` cũng qua hai layout.
[Release receipt](../experiments/manifests/phase5_constrained_probe_package01.json).
Biên bản release và memory sau freeze được gộp vào phần host release audit/report;
không thêm status-only commit, không amend source thực nghiệm.
Đã cập nhật skill commit cadence và knowledge index: không commit mỗi status,
gom việc hoàn chỉnh; source freeze là ngoại lệ cần thông báo trước.

Nền runner đã đóng:

**Đã nối constrained runner/checkpoint/native evidence join**, QA đạt.
[Report](../docs/evaluation/phase5_constrained_probe_v1_report.md),
[contract](../docs/architecture/phase5_constrained_probe_v1_contract.md).
32 tests mới qua; final QA 480 focused + 105 integration tests đạt,
setup/Ruff/mypy443/knowledge đạt. Controls02: 4 completed + 4 deliberate model_error, missing-only
resume đúng; hai valid audits byte-identical. Native boundary tests dùng mock,
runner dùng spawned synthetic workers, không phải pretrained/native GPU proof.
Owner yêu cầu bớt commit: gom implementation + QA/memory trong một commit cuối.

Mốc host/cache làm nền:

**Đã nối constrained host/cache/runtime + read-only join**, source `e04cd8d`.
[Report](../docs/evaluation/phase5_constrained_host_v1_report.md),
[contract](../docs/architecture/phase5_constrained_host_v1_contract.md).
37 tests mới đạt, gồm CALC/DOC × A2/A6 qua spawned workers và các lỗi identity,
cache/receipt/worker; synthetic CPU, không production guard. Final QA đã đạt:
438 focused + 90 integration tests, setup/Ruff/mypy437/knowledge.
Host cache kiểm ownership/worker health và receipt history, không giả nhận đã
introspect live model từ xa. Lỗi không dispatch được ghi rõ không thêm inference.

Nền native CPU đã đóng:

Đã chốt **native constrained generation CPU v2 COMPLETE/audit**;
[report](../docs/evaluation/phase5_constrained_generate_cpu_v2_run.md).
Actual notebook `huylmhuhu/react-vn-constrained-generate-cpu-v2`,
version 1/ID 134579648; source `b4ae0f7`, Dataset guard15 v1/private.
Post-download check 08:25:13 UTC ngày 2026-09-16 vẫn COMPLETE/source khớp.
Không còn notebook pending trong lịch này; không submit lại.

Hai success cases sinh JSON + EOS, mỗi ca 28 token; ForcedBOS rejected trước
forward và interrupt restored. Đây là tiny random Qwen CPU, không pretrained
guard 1.5B hoặc benchmark quality. CPU v1 thất bại vẫn lưu, không xóa/retry.

## Bước tiếp theo

1. Không còn pending ExitPair GPU v1; **không resubmit ExitPair hoặc constrained v1**.
   Giữ raw `results/phase5_constrained_gpu_monitor02`, hai audits tại
   `results/phase5_constrained_gpu_audit01.json` và
   `results/phase5_constrained_gpu_report01/release_audit.json`.
2. Terminal outputs đã tải/kiểm toán; giữ raw/audits trong các thư mục mới nêu
   ở đầu. Lỗi không tái hiện, không suy diễn instrumentation là fix.
3. Clause/cumulative candidate v12 đã nối constrained ExitPair và audit CPU;
   chuẩn bị32task runner/native release audit +exact package trước GPU.
   Giữ syntax8/8 tách khỏi semantic quality, không resubmit4task probe cũ.
   Lifecycle follow-up nếu cần phải khóa repeat/order budget riêng trước chạy;
   hoàn tất mapping20DoD trước formal freeze.
4. Giữ thay đổi local qua các lượt, không commit chỉ vì QA đạt. Commit khi owner
   yêu cầu hoặc cần source freeze thật; không status-only/amend nguồn thực nghiệm.

## Bằng chứng

- [ExitPair close02](../experiments/manifests/phase5_exit_pair_cpu_close02.json),
  [QA02](../experiments/manifests/phase5_exit_pair_cpu_qa02.json):
  `results/phase5_exit_pair_cpu_controls02` có valid4 + deliberate model_error4,
  16 workers reaped; valid8 GRACEFUL, failure4 GRACEFUL/4 TERMINATE.
  Hai audits mỗi condition trước/sau complete-resume byte-identical,
  101 valid/77 failure raw files, 31 runner source pins.
  689 focused/50,98s + 180 integration/180,37s; 172/142/86/175 frozen pins nguyên.
  Controls01/QA01/close01 giữ/excluded sau sửa cross-host interpreter binding.
  Base `5875bb7` + exact working-tree pins, không commit/push hoặc job GPU mới.
  Native wrapper tests chỉ mock/lazy; raw chưa backup ngoài máy.

- [Exit milestones close](../experiments/manifests/phase5_exit_milestones_cpu_close01.json),
  [QA](../experiments/manifests/phase5_exit_milestones_cpu_qa01.json):
  15 execution source pins, 19 raw files tại `results/phase5_exit_milestones_cpu_controls02`;
  audits `results/phase5_exit_milestones_cpu_audit01.json`/`...audit02.json` byte-identical.
  QA logs `results/phase5_exit_milestones_cpu_qa01`: 666/44,72s + 149/138,93s.
  Base Git `3cb2b54` + working-tree pins, chưa native release.
  Controls01 giữ/excluded sau harden thứ tự kiểm symlink trước đọc JSON;
  controls02 bind source mới, không semantic model retry. Raw mới vẫn local,
  chưa backup ngoài máy; không cần account mới trước bước native preflight.

- Kiểm lại ngày 2026-09-20: 50 tests chọn lọc (knowledge + teardown unit và
  integration) đạt/11,24s; setup/Ruff/mypy450/knowledge/diff đạt.
  56 source/QA-log pins và 19 raw pins khớp; audit mới ở
  `results/phase5_teardown_cpu_audit_20260920_01.json` byte-identical với audit01.
  Validator đã kiểm thêm links của START_HERE, có regression cho link hỏng,
  đường dẫn ra ngoài repo, credential link và bỏ qua vault settings.
  Ví dụ Markdown ban đầu tạo broken link giả đã sửa; rerun 50/50 đạt.
  Không chạy full pytest hoặc model, không đổi receipt thực nghiệm cũ.
- [Teardown close](../experiments/manifests/phase5_teardown_cpu_close01.json),
  [final QA](../experiments/manifests/phase5_teardown_cpu_qa01.json):
  raw `results/phase5_teardown_cpu_controls02`, audit01/02 byte-identical.
  CPU CPython3.11.0/Darwin; runtime internals và 10 execution sources hash-bound,
  Git base27626b1 + working-tree pins. 172/142/86/175 frozen source pins không đổi.
  Preparation01 thiếu cases directory, giữ identity/excluded; regression đã thêm,
  không GPU/model rerun. Final QA 623/44,37s + 133/125,28s.
- [Terminal](../experiments/manifests/phase5_constrained_gpu_terminal01.json),
  [audit](../experiments/manifests/phase5_constrained_gpu_audit01.json),
  [summary](../experiments/manifests/phase5_constrained_gpu_summary01.json).
  Scan 256 files/0 matches. Summed startup901,127s/task total947,261s;
  agent7,196 token/s và guard17,041 token/s chỉ từ joined generation, không startup.
- [Final release/report QA02](../experiments/manifests/phase5_constrained_release_cpu_qa02.json):
  573 tests/44,43s + 105 integration/111,61s; 142/86/175 frozen pins nguyên.
  [QA01 trước summary](../experiments/manifests/phase5_constrained_release_cpu_qa01.json)
  giữ nguyên (562 + 105), không ghi đè.
- Live access `results/phase5_constrained_gpu_access01`: còn 22,50h GPU,
  Dataset ready/v1. Preparation01 dừng trước push do metadata `info.isPrivate`;
  corrected submission02 mới là một job GPU thật, raw được giữ cả hai.
- Development package: 433 raw files/layout, 1.043 file scan không credential match.
  Source base `f5e97ae` + exact working-tree hashes, native submission disabled.
- Committed package01: source `0d4e82f`, 172 Git source pins/166 worker files;
  hai layout/433 raw files mỗi layout xác minh lại; scan 1.043 file/0 matches.
- [Package QA](../experiments/manifests/phase5_constrained_package_cpu_qa01.json):
  495 focused/42,96s + 105 integration/111,91s; logs trong
  `results/phase5_constrained_package_cpu_qa01`.
- [Runner/native join report](../docs/evaluation/phase5_constrained_probe_v1_report.md):
  raw `results/phase5_constrained_probe_cpu_controls02`; base Git `e655658`,
  execution source hashes bind working-tree code, chưa GPU release identity.
  Controls01 nhập nhầm base SHA được giữ/excluded. Không sửa raw hoặc chọn kết quả.
- [Final QA](../experiments/manifests/phase5_constrained_probe_cpu_qa01.json):
  480 tests/42,60s + 105 integration/112,49s; raw `results/phase5_constrained_probe_cpu_qa01`.
  [Integrity/controls](../experiments/manifests/phase5_constrained_probe_cpu_close01.json).
- [Host integration report](../docs/evaluation/phase5_constrained_host_v1_report.md):
  37 tests mới qua; [final QA](../experiments/manifests/phase5_constrained_host_cpu_qa02.json)
  có 438 focused/42,30s + 90 integration tests đạt, raw ở `results/phase5_constrained_host_cpu_qa02`.
  Source `d270830`/QA01 trước hardening giữ lịch sử, không ghi đè.
- [Submission v2](../experiments/manifests/phase5_constrained_generate_cpu_submission02.json),
  [terminal](../experiments/manifests/phase5_constrained_generate_cpu_terminal01.json),
  [audit](../experiments/manifests/phase5_constrained_generate_cpu_audit01.json),
  [summary](../experiments/manifests/phase5_constrained_generate_cpu_summary01.json).
- [QA source 8298502](../experiments/manifests/phase5_constrained_generate_cpu_qa03.json):
  401 focused tests / 21,87s; setup/Ruff/mypy433/knowledge pass; 22 auditor tests mới.
  QA local không chạy native library; kết quả native nằm trong receipt riêng.
- Hai audits `results/phase5_constrained_generate_audit02` và `..._audit03`
  byte-identical, xác minh 142 source/25 raw/2 remote files.
  Raw/remote: `results/phase5_constrained_generate_monitor03`;
  post-download observation: `results/phase5_constrained_generate_terminal04`.
- Package đúng: `build/kaggle/phase5_constrained_generate_cpu_package02`;
  [preflight](../experiments/manifests/phase5_constrained_generate_cpu_preflight02.json).
  142 active + 86 prior native + 175 baseline source pins không đổi.
- [V1 failure và diagnosis](../docs/evaluation/phase5_constrained_generate_cpu_v1_run.md),
  [Kaggle directory](kaggle_resources.md), [DoD queue](phase5_remaining.md).

## Giới hạn

Bounded constrained native syntax/release và synthetic teardown controls đã đạt;
native teardown cause, representative guard quality, benign utility,
graceful shutdown và formal freeze vẫn mở. Không full pytest vì Test-assigned
authoring fixtures; không Test/private GT access. Không cần tài khoản mới;
kiểm quota/private mounts lại khi GPU package thực sự sẵn sàng.

GitHub `Lamhuy0489` khác Kaggle `huylmhuhu`; quyền GitHub không cấp quyền Kaggle.
Giữ notebook/Dataset private, credentials ngoài Git. Không đưa memory vào prompt.
Giữ nguyên tài liệu riêng tại docs/BAO_CAO_TIEN_DO_DO_AN.*,
docs/figures/ và cấu hình Obsidian. Ngày 2026-09-20 plan/phase6–9 không còn dirty;
không phục hồi các thay đổi cũ. [Lịch sử bàn giao](history_20260916_constrained_cpu.md) không phải
chỉ dẫn submit hiện hành.
