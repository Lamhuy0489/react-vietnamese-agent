# Bàn giao phiên làm việc

Cập nhật: 2026-09-24. Phase 5 chưa nghiệm thu: 4/7 ≈ 57% nhóm acceptance.

## Đang làm

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
