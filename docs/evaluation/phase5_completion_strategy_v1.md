# Phase 5 — giải pháp kỹ thuật để hoàn thiện đồ án

2026-09-23. Mục tiêu là làm cho agent **an toàn và còn làm được việc**, không
chỉ bổ sung giấy tờ nghiệm thu. Đây là lộ trình kỹ thuật, **không phải quyết
định freeze hoặc thay đổi DoD**. Chuẩn gốc là
[`plan/phase5.md` mục CXXVI](../../plan/phase5.md),
[`research_contract`](../project/research_contract.md) và
[`invariants`](../project/invariants.md). Trạng thái chính thức vẫn 4/7 nhóm
acceptance (~57%); không suy ra phần trăm công sức hay 20/20 DoD.

## 1. Tách ba nguyên nhân, tránh chữa nhầm bệnh

Đề xuất giữ **v12 cumulative** làm candidate chính của đợt đóng này: Dev32
native đã chạy một lần trên source `ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e`
và có [terminal audit](phase5_clause_dev_gpu_v2_terminal_report.md),
[scoring](phase5_clause_dev32_scoring_v1_report.md). Đây là lựa chọn triển khai
để tránh trộn danh tính run, **chưa phải phê duyệt freeze**. v13 và v14 chỉ là
ablation CPU opt-in với nguồn synthetic; không dùng kết quả đó để nhận v12
đã hết false block, hoặc âm thầm đổi policy của Dev32. Inventory hai ID mới
chưa được owner xác nhận; việc đó chỉ chặn ablation nguồn prospective, không
chặn kiểm toán v12 hay chuẩn bị Phase 5 freeze.
Mốc tiếp theo: owner đã duyệt nhãn trước nội dung và
[adapter pinned A6/ExitPair](phase5_room_ticket_pair_cpu_v1_report.md) đã qua
paired CPU, nhưng source pin/package/native model vẫn chưa có. Vì vậy đây
vẫn là ứng viên, chưa phải bằng chứng Dev32 false block được giải.

Đối chiếu read-only 32 dòng của generated `results/phase5_clause_dev32_score05/summary.json`
(hash trong [scoring receipt](../../experiments/manifests/phase5_clause_dev32_scoring_v1_receipt.json))
cho thấy lỗi không đồng nhất, nên **không có một prompt/threshold chung** giải
được tất cả:

| Nhóm ca trên subset đã khóa | Quan sát | Hướng xử lý đúng |
|---|---|---|
| `CAND_SOURCEBINDING` | A2 attack thành công một ca; A6 chặn attack nhưng benign A6 mất utility và có một canonical safe-action false block | Proof-carrying provenance cho đúng public field, không bỏ session sensitivity/guard veto |
| `CAND_ENCODED`, `CAND_LINKMAIL` | Mỗi family có bốn task A2/A6 × attack/benign không có security proposal, tổng tám task không gọi guard | Chẩn đoán agent planning/tool-use riêng; không tính là guard phân loại đúng hoặc sửa bằng nới PRE |
| `CAND_ROWLIST` | Hai nhánh A2 có SQL-shaped proposal ngoài khả năng canonical scorer; Broker báo `INVALID_QUERY` | Giữ trạng thái unassessed, mở rộng evaluator/typed query coverage theo protocol riêng, không gán pass |
| `CAND_LINKPAGE` | Benign typed utility vẫn đạt ở A2/A6; scorer-safe utility chỉ đạt A6 | Giữ case đối chứng để phát hiện remedy làm mất ích lợi đã có |

Đây là phân loại hành vi từ selected Dev, không phải nhãn oracle mới, tỷ lệ
toàn benchmark hay tuyên bố nguyên nhân model đã được chứng minh.

| Cổng còn mở | Bằng chứng đã có | Việc làm tiếp và điều kiện ra quyết định |
|---|---|---|
| ModelPair/guard native và lifecycle | 32/32 Dev tasks terminal; 64/64 workers reaped; guard 31/32 GRACEFUL, một TERMINATE/-15 sau Python milestones ([diagnostic](phase5_clause_guard_exit_diagnostic_v1_report.md)). | Trước run mới, khóa giao thức startup/exit riêng: thứ tự cold/warm, số lần cố định, cửa sổ thoát, log OS/process và cách tính cả lỗi. Dùng run identity mới, đối chứng cùng source; báo cả forced exits, không đổi thành “graceful” vì worker được reaped. Nếu không chứng minh được tính ổn định, giữ cổng mở và mô tả giới hạn; thay tiêu chí chỉ sau quyết định có ghi trong decision log. |
| Guard quality và benign differential | [Scoring Dev32](phase5_clause_dev32_scoring_v1_report.md): A2/A6 attack success 1/8 và 0/8; typed benign utility 4/8 và 3/8, scorer-safe 2/8 và 3/8. Có một A6 canonical safe-action false block đã xác nhận. 8/32 tasks không gọi guard; 65/65 returned responses đúng cú pháp. | Giữ nguyên raw/score Dev32. Lập bảng quyết định cho **mỗi** failed/unknown case theo cơ chế (model không đề xuất, guard, PRE, Broker, Final), không gộp “completed” thành đúng. Định nghĩa trước một phép kiểm prospective duy nhất nếu cần kiểm v13/v14 hoặc sửa false block; mẫu và controls chọn từ public Dev/synthetic trước inference, không sửa theo output. Phải báo security *và* utility, cả denied proposals trước Broker. Chưa có ngưỡng chất lượng định lượng được plan phê duyệt; không tự đặt ngưỡng hậu nghiệm. |
| Semantic coverage và freeze | [20-DoD map](phase5_dod_evidence_map.md) có bằng chứng CPU cho Broker/PRE/POST/Final, Test seal và mocks; v12 native chỉ là subset 8 Dev families. | Lập hồ sơ cuối cho từng DoD: source/run/receipt, validator, pass/fail/giới hạn. Chạy lại deterministic acceptance trên candidate được chọn; xác minh Test bằng hash/validator, **không đọc payload để tune**. Chỉ cập nhật [`phase_status`](../project/phase_status.md) và freeze rule/prompt/model/config A0–A6 khi toàn bộ điều kiện gốc đã đạt hoặc có quyết định đổi scope được owner chấp thuận và ghi log. |

## 2. Giải pháp đề xuất

**A. False block A6 — provenance có chứng cứ thay vì nới whitelist.** Khi user
cho phép gửi đúng `room` tới mock endpoint, host gắn metadata độ nhạy cho từng
nguồn *trước khi có nội dung*; Tool Broker/POST tạo artifact có lineage. Một
vé dữ liệu công khai chỉ được cấp từ nguồn S0 đã admit, đúng dòng `room`, đúng
observation/giá trị/đích/user anchor; PRE kiểm lại vé và cấm nếu cùng giá trị
xuất hiện trong S1/S2 hoặc source/lineage không rõ. Guard, Broker, POST và
FinalGate vẫn có quyền veto. [v13/v14 CPU](phase5_dated_room_v1_report.md) đã
chứng minh đường này có thể giải ca synthetic sạch và chặn poison/collision;
**chưa giải ca Dev32** vì nguồn Dev cũ không có nhãn độc lập. Bước tiếp là
inventory prospective được owner duyệt trước nội dung, sau đó một so sánh
paired native có source/run identity riêng. Không relabel Dev32 hậu nghiệm.
CPU regression ngày 2026-09-23 đã mở rộng cặp clean/poison/S2-collision sang
ba mã phòng và cả ngày nhuận hợp lệ; payload khác giá trị nguồn vẫn bị chặn.
[14 integration cases](../../tests/integration/test_prospective_room_inventory_v1.py)
và 60 ticket/inventory cases liên quan đạt. Kết quả này chỉ xác nhận logic
synthetic, không suy thành model utility.

**B. Guard quality — tách “không gọi guard” khỏi “guard phân loại sai”.** Cần
ma trận cho từng action ở 32 trace: model có đề xuất không, PRE gọi guard
không, guard verdict, Broker thực thi hay chặn, POST và Final release. Trên
những ca guard thực sự được gọi, đánh giá coverage/structured-output và
đối chiếu quyền user, không dùng cú pháp JSON làm proxy cho an toàn. Nếu lỗi
đến từ model bỏ qua action thì thêm guard prompt không thể cứu utility; nếu
do PRE thiếu typed origin thì sửa provenance, không “huấn luyện” trên raw
Test. Giữ 8 ca không gọi guard trong denominator báo cáo đúng loại.

**C. Lifecycle — hoàn tất thoát tiến trình, không chỉ thu hồi process.**
Giữ timeout/fallback an toàn. Một diagnostic prospective được khóa trước sẽ
đo cold vs warm, thời điểm STOP, serve return, finalizer, OS exit, CUDA/IPC
release và RAM/VRAM; cả forced exit tính là failure lifecycle. Chỉ khi biết
độ trễ nằm ở đâu mới chọn sửa cleanup, owner join hoặc budget. Không tăng
2 giây grace theo đúng mẫu đã thấy để làm đẹp 31/32.

**D. Tích hợp và báo cáo khoa học.** Một candidate đã chọn được chạy cùng
frozen public Dev controls, cùng model revision/seed, ghi latency, token,
security, typed benign utility, denied proposals và lỗi worker. So sánh A2/A6
trên cặp cùng family; không gọi 8 family là ước lượng toàn benchmark. Các ca
âm được giữ; chỉ sau đó map 20 DoD, xác minh seal và freeze. Đây là bằng
chứng đồ án, không phải vòng lặp chọn kết quả đẹp.

## 3. Thứ tự thực hiện, với điểm dừng rõ ràng

1. **Ngay bây giờ, không cần GPU:** đồng bộ bản đồ DoD với scorer và exit
   diagnostic; khóa danh sách failed/unknown của Dev32, source và metric
   denominators. Kiểm CPU/integrity cho phần này. Không submit Kaggle để
   “sửa” số Dev32.
2. **Trước inference tiếp theo:** viết một protocol prospective ngắn cho
   lifecycle và/hoặc false-block remedy, định sẵn controls, source freeze,
   model revision, seed, run identity, retry/failure accounting và điều kiện
   dừng. Chỉ chạy khi package/admission và QA đạt. Một kết quả xấu vẫn là
   kết quả; không thêm v15/v16 theo từng lỗi phát sinh.
3. **Sau bằng chứng mới:** đối chiếu DoD-5/9/15/20 và các gate còn lại. Nếu
   chất lượng hoặc lifecycle vẫn không đạt, ghi báo cáo âm/giới hạn và yêu
   cầu quyết định scope; không gọi Phase 5 hoàn tất. Nếu đạt, thực hiện
   formal freeze và mới cập nhật tiến độ chính thức.

Điểm dừng của đường này là **một hệ thống có đặc tính đo được và một quyết định
nghiệm thu có kiểm toán được**:
pass theo DoD hiện hành, hoặc fail/block kèm nguyên nhân và đề xuất thay đổi
được tách khỏi bằng chứng. Không cần triển khai graph memory, thêm model lớn,
hay chạy held-out Test để đóng ba cổng trên.
