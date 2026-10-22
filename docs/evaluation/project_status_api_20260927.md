# Tiến độ đồ án và lộ trình hoàn thiện qua API Kaggle

Cập nhật 2026-09-27 theo yêu cầu owner. Đây là rà soát tài liệu/source/receipt
đã có, không phải phiên probe uptime hoặc thực nghiệm model mới.

**Có thể tiếp tục hoàn thiện đồ án bằng cách chạy model trên Kaggle và điều
phối thí nghiệm ở local.** Bằng chứng hiện tại xác nhận luồng kỹ thuật chạy
được; chưa đủ kết luận chất lượng guard hoặc nghiệm thu kiến trúc an toàn.
API là phương thức triển khai inference, không thay đổi câu hỏi nghiên cứu.

## Đang ở đâu

| Phần việc | Trạng thái có bằng chứng |
|---|---|
| Phase 1: A0, môi trường và tám mock tools | Đã accepted |
| Phase 2: clean benchmark | clean_v1.1 đã accepted; giữ lịch sử lỗi v1 |
| Phase 3: attack và benign benchmark | adversarial_v2 đã accepted; Test khóa |
| Phase 4: normalization và provenance | Đã accepted |
| Phase 5: A1–A6 | Đang làm; chỉ số hiện có 4/7 nhóm acceptance, chưa đóng phase |
| Hạ tầng API Qwen3-8B agent + Llama3.2-3B guard | Hai notebook v1 đã triển khai; một paired smoke đạt |
| Prototype typed-field reference / model-plan bridge | Component/bridge đã có CPU controls; chưa full ReAct A6 với hai API |
| Phase 6–9: evaluator hoàn chỉnh, thực nghiệm chính thức, luận văn/bảo vệ | Các bước phía sau; chưa được nghiệm thu từ kết quả API |

4/7≈57% chỉ là số nhóm nghiệm thu **của Phase 5**, không phải 57% toàn đồ án,
thời gian hay công sức. Không có cơ sở quy đổi tiến độ hiện tại thành một tỷ lệ
phần trăm toàn bộ luận văn. Mốc accepted theo [phase status](../project/phase_status.md);
chi tiết20DoD theo [evidence map](phase5_dod_evidence_map.md).

[Paired API report](structured_pair_api_v1_report.md) và
[receipt](../../experiments/manifests/structured_pair_api_v1.json) ghi:
source728821e, Qwen và Llama mỗi model2calls, một calculator call qua Broker,
final166 đúng schema, guard SAFE/LOW cả hai lượt; không retry. 77 focused
tests đạt cùng setup/Ruff/mypy. Các checks này thuộc lượt triển khai trước,
không phải77 bài thực nghiệm chất lượng và không phải toàn bộ test suite.

## Phương thức API giúp gì

Local giữ task runner, state riêng từng task, tám tools, Broker, provenance,
Pre/Post/Final gates, traces và evaluator tách biệt. Kaggle giữ model weights
và nhận yêu cầu inference. Sửa runner/thí nghiệm ở local không cần đóng gói lại
notebook nếu hợp đồng inference không đổi. Đổi model, schema serving hoặc
dependencies vẫn cần phiên/version phù hợp và kiểm lại identity.

Có thể phát triển agent và guard độc lập, xem lỗi sớm, lưu checkpoint từng task
và chạy tuần tự các cấu hình. Không cần model lớn hơn8B để đáp ứng phạm vi hiện
tại: [research contract](../project/research_contract.md) không đặt sàn tham số,
không yêu cầu huấn luyện model mới. Việc model có đủ năng lực cho benchmark
phải đo trên Dev; không suy từ kích thước hoặc một phép tính thành công.

## Những phần API chưa giải quyết

1. **Guard đúng hay sai:** JSON hợp lệ không chứng minh phân loại đúng. Cần
   attack và benign ghép cặp, tỷ lệ bỏ lọt/chặn nhầm, có mẫu tiếng Việt và nguồn
   tool thực. Không có security-quality score mới cho Llama3B ở profile này.
2. **A6 giữ được công việc hợp lệ:** các phiên trước có false block và giới hạn
   phát hiện lộ dữ liệu. Phải kiểm dữ liệu công khai sau khi đã thấy bí mật,
   nội dung bị tiêm chỉ dẫn, nguồn không rõ và câu trả lời cuối; không chỉ
   kiểm một action calculator hoặc chặn mọi thứ.
3. **Tích hợp thật:** paired smoke dùng gate SAFE-only riêng, chưa chạy đầy đủ
   cumulative A0–A6. Bridge typed-reference hiện nhận JSON `Plan`, trong khi
   `StructuredHTTPBackend` đang kiểm `action/final_answer`. Server có cơ chế
   inline schema nhưng client/schema adapter cho Plan chưa nối; không thể
   coi thay base URL là bridge đã hoạt động. Grant vẫn là quyền do host xác
   lập, không được model tự tạo hoặc lấy từ evaluator ground truth.
4. **Vận hành thí nghiệm dài:** cần task-state/cache isolation, timeout,
   interrupted-request accounting, resume không lặp semantic failures và xử
   lý thay session/tunnel. Server chạy lâu không tự giải quyết tiêu chí
   cancellation/graceful lifecycle của profile cũ; cần contract và bằng chứng
   tương ứng cho profile API, giữ nguyên các failure cũ.

## Đường đi tiếp, theo thứ tự

| Bước | Công việc | Bằng chứng cần có trước khi chuyển bước |
|---|---|---|
| 1 — Profile Dev qua API | Khóa danh sách task Dev/controls, model/hash, prompt/schema, budgets, seeds và tiêu chí dừng; runner có checkpoint và đo latency end-to-end riêng decode time | Manifest trước inference; CPU identity/resume/fault checks; không Test |
| 2 — Pilot năng lực và guard | Đo agent trên clean tasks; đo guard riêng trên attack/benign để phân biệt lỗi agent với lỗi guard | Trace đủ task/attempt, điểm evaluator riêng, giữ mọi lỗi/denial và mẫu số |
| 3 — Candidate A6 | Nối schema Plan nếu tiếp tục prototype đã duyệt, host quyền/nguồn và full Pre/Post/Final; kiểm cumulative parity và các ca công khai/bí mật/unknown | Integration controls + native Dev matched runs; không chỉ component pass |
| 4 — Đóng Phase 5 | Đối sánh A0–A6 cùng model/data/tools/decoding, audit lifecycle và20DoD; khóa candidate cuối | Receipt nối từng tiêu chí, giới hạn công bố rõ và formal freeze |
| 5 — Sau nghiệm thu Phase 5 | Hoàn thiện evaluator Phase 6; Phase 7 chạy thí nghiệm chính thức; Phase 8–9 tái lập, viết và bảo vệ | Đi theo acceptance từng phase; Test chỉ dùng sau freeze và đúng phạm vi |

Bước cụ thể kế tiếp là **manifest + runner Dev nhỏ có checkpoint**, chưa phải
bật toàn benchmark. Nếu pilot cho thấy guard kém hoặc agent thiếu năng lực,
ghi kết quả âm và điều chỉnh ứng viên trên Dev theo phiên bản mới; không sửa
task, loại mẫu khó hoặc lặp câu trả lời chỉ để tăng điểm. API làm vòng thử này
thuận tiện hơn nhưng không bảo đảm A6 sẽ thắng mọi baseline.

## Hai server hiện tại và yêu cầu ba backbone

RQ1 theo contract yêu cầu **ba backbone trả lời công việc**. Cặp hiện tại là
một task agent và một guard; không tự được tính là hoàn thành so sánh ba model.
Có thể dùng profile API để chạy lần lượt thêm hai task backbones được chọn
trên Dev, không cần ba agent và guard cùng chạy. Không tự chọn Gemma/DeepSeek
từ danh sách cũ khi chúng còn lỗi/giới hạn chưa xử lý. Llama guard chỉ được
tính như một task backbone nếu có một điều kiện agent riêng được khai báo.

RQ2 giữ một task backbone cố định qua A0–A6; guard cố định qua các mức dùng
guard, còn A0 không được thêm guard. Cùng agent schema/decoding trên mọi mức.
RQ3 giữ các split/variants đã chốt. Fine-tune trọng số không thuộc thực nghiệm
chính theo contract. Không gộp điểm lịch sử từ model/profile cũ vào cặp mới.

## Kết luận khả thi và phạm vi lượt cập nhật

Hướng API phù hợp để tiếp tục đồ án, với các gate chất lượng/tích hợp còn nêu
trên. Chưa đủ dữ liệu dự toán thời gian hoàn thành hoặc tổng GPU giờ từ một
smoke ngắn. Ưu tiên tiếp theo chuyển sang năng lực, guard và A6; chỉ sửa hạ tầng
khi có lỗi cụ thể cản các phép đo này. Lượt này cập nhật lộ trình/memory/evidence
index, không đổi research contract, không fine-tune, không model run mới, không
đánh dấu phase accepted và không commit/push chỉ để cập nhật trạng thái.

Kiểm tra lượt cập nhật tài liệu: `make knowledge-check`, `git diff --check`,
setup và Ruff đạt; mypy563files đạt;6tests memory/navigation đạt. Không chạy
lại toàn bộ pytest vì không đổi code/runtime; không đọc dữ liệu Test.
