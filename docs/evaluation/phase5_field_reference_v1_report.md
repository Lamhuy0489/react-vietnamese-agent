# Field-reference v1: kết quả prototype tái cấu trúc giới hạn

2026-09-25. Owner đã duyệt prototype riêng, giữ benchmark/kết quả cũ và chỉ
tích hợp sau đối chứng. [Contract trước implementation](../architecture/phase5_field_reference_v1_contract.md).
**Giả thuyết luồng dữ liệu đạt các controls component đã định; chưa đủ để thay A6.**

## Cơ chế đã thực hiện

[Component](../../src/react_agent/prototypes/field_reference_v1.py) nằm riêng
trong `prototypes/`, không có import từ runtime benchmark. Model-shaped Plan chỉ
chọn `artifact_id + source_hash + field_path`, phép nối bằng separator cố định
và Base64/hex có giới hạn. Không cho literal/expression/template tùy ý.

Host đọc tài liệu bằng Tool Broker và tạo nguyên bản source snapshot. Reference
gắn run/Grant/hash; host lấy giá trị thật. Output provenance trỏ tới các source
được chọn; exposure tới mọi tài liệu đã đọc được lưu riêng, không tuyên bố causal
lineage của LLM. Nhãn sensitivity/trust không mất khi concat hoặc encode. Raw
artifact giữ nguyên, nguồn public không bị hạ nhãn từ một S2 artifact khác.

Grant hash-pin là quyền do host cấp: task/raw-user/catalog/readable IDs/fields
được output, không chứa expected answer/attack label. Private field có thể nằm
trong output scope để kiểm rằng scope không tự hạ clearance S0. Upstream veto
mặc định deny; caller phải chủ động cấp phép. **Chưa có NLP compiler cho Grant,
LLM guard thật hoặc kiểm toán ý định do model chọn.** S0 không đồng nghĩa TRUSTED.

## Thực nghiệm mới, không trộn bảng A6 cũ

[Harness](../../scripts/run_phase5_field_reference_v1.py),
[receipt chọn lưu](../../experiments/manifests/phase5_field_reference_v1.json).
16 conditions × 2 arms = **32 CPU component executions**, 98 doc_read thực thi
qua Broker (mỗi arm đọc 3 tài liệu, case repeat đọc thêm 1). Hai arms có cùng
fixture/Grant logic/proposal/transform/read schedule, kiểm bằng hash sau khi loại
run ID riêng. Chỉ khác cách chọn nhãn effective: toàn exposure hay selected fields.

| Kết quả trong batch đã định | Exposure baseline | Selected-field candidate |
|---|---:|---:|
| Giữ output public hợp lệ | 0/8 | 8/8 |
| Từ chối ca âm | 8/8 | 8/8 |
| Tổng CPU thực thi, chưa gồm hậu kiểm | 0.063787 s | 0.065855 s |

Benign gồm văn xuôi, nhiều dòng, collision public/private, repeated observation,
public Base64/hex, concat hai public fields, trusted public. Negative gồm private
identity/Base64/hex, mixed public-private, field ngoài grant, hash sai, unknown
reference và veto. Expected outputs chỉ ở host harness. Không native/token/VRAM
measurement; thời gian này không phải tốc độ LLM hoặc ước lượng hiệu năng tổng quát.

Đây **không phải so sánh official A5/A6**: cả hai component arms đều giả định
đúng Grant và dùng ngôn ngữ tham chiếu mới. Không thể so 8/8 ở đây với 2/8 của
direction probe rồi tuyên bố tăng task success — input representation, controls
và quyền host khác. Bản mới chưa được thử khả năng lựa chọn tham chiếu của model,
control-flow injection, implicit flow, free-form final hoặc external sink.

## Audit, QA và khả năng tái tạo

[Auditor](../../scripts/audit_phase5_field_reference_v1.py) không gọi Session.finalize,
Tool Broker hoặc model. Nó đọc source/fixture/Grant/plan, deserialize DAG, join
Broker identity/order/raw result, dựng lại text/transforms và nhãn từ selected
sources, đối chiếu final output/decision/parents/exposure. Vẫn dùng chung schema
và ArtifactStore, không phải implementation độc lập hoàn toàn hoặc chứng nhận
publisher/native execution. Hash declaration phải lấy từ bên ngoài.

Raw `build/evaluation/phase5_field_reference01/` giữ ngoài Git. Declaration SHA:
`b93993b2a6754e5544aacdeee8511b685ffb151771a2fb03f8b7377c3f82e751`.
Audit01/02 khớp byte; source/harness/contract giữ nguyên trong và sau matrix.
57 component tests gồm S1/S2 × trust × transforms, literals, schema/ref forgery,
scope, budget, tool errors, raw preservation và network interdiction. Thêm 7
auditor tests kiểm read-only và corruptions. Một lỗi fixture unit monkeypatch
Pydantic đã sửa trước matrix; không có semantic experiment retry. Tổng regression
và JUnit/hash trong selected receipt; full pytest không chạy do authoring Test sealed.

```sh
.venv/bin/python scripts/run_phase5_field_reference_v1.py \
  --output build/evaluation/phase5_field_reference_fresh
.venv/bin/python scripts/audit_phase5_field_reference_v1.py \
  --root build/evaluation/phase5_field_reference01 \
  --declaration-sha256 b93993b2a6754e5544aacdeee8511b685ffb151771a2fb03f8b7377c3f82e751 \
  --output build/evaluation/phase5_field_reference_audit_fresh.json
```

Giữ toàn bộ direction-probe negative results. 191 source files của historical
package04 được kiểm lại và không đổi. Không upload Kaggle/commit/push, không
thay Word/benchmark/seal/A0 hoặc tăng 4/7 acceptance. Skills capstone/repro đã
giữ prototype riêng và phân biệt source working-tree với source freeze.

## Bước nghiên cứu tiếp theo hữu hạn

1. Đóng interface cho model đề xuất reference nhưng **không được tạo Grant**;
   quy định thông tin reference nào được hiển thị, lỗi chọn sai và abstention.
   Tách intent authorization do host xác thực khỏi model planning; không gán
   nhãn quyền từ expected answers hoặc biến thể benchmark.
2. Nối thử với loop riêng và frozen A1/guard/pre/post veto; thêm kiểm tra nguồn
   public có instruction độc hại, chọn nhầm field và free-form secret. Không
   nới sang arbitrary literals để cứu utility. External mock sink cần destination
   authorization riêng và vẫn qua Broker.
3. Một batch mới, cùng model-facing representation cho đối chứng, trước khi
   chọn source freeze/native. Nếu mới chỉ chứng minh host đúng khi được đưa plan
   đúng thì báo đúng mức đó; không gọi Phase 5 hoàn tất.

Chưa cần account mới. Cổng native package/quota/models chỉ xử lý khi interface/
integration controls đạt; không dựng thêm gói Kaggle cho component chưa có model.
