# Document diagnostic v1

2026-09-14 — đang kiểm trước inference; Phase 5 chưa accepted.

Theo [preregistration](../docs/architecture/phase5_document_diagnostic_v1_contract.md),
chạy một task công khai tổng hợp đọc CDOC_034, một lần ở mỗi A0–A6, cùng model/
prompt/decoding/deadlines đã pin. Chỉ đo path/lifecycle/timing, không ASR/FPR hay
benchmark utility. Dữ liệu Test/private oracle không được mở.

CPU draft01 ở `results/phase5_document_devcheck01` phát hiện A4–A6 không hiểu
namespace CDOC, nên chặn đọc hợp lệ. Giữ output này, không chọn nghiệm thu.
Scope v3 bổ sung bounded CDOC, không alias sang DOC; runtime v8 chỉ thay scope.
V7 và toàn bộ receipt/source frozen giữ nguyên. CPU draft02 đạt 42 focused tests
trong 8,64s, có doc_read và guard Pre/Post qua đủ các level dự kiến; đây là stub.

Tiếp: full QA, exact archive/expanded preflight, commit/push source rồi mới
submit notebook private `huylmhuhu/react-vn-document-runtime-v1` (tên dự kiến,
chưa phải tài nguyên đã tạo). Dataset dự kiến dùng lại private
`huylmhuhu/react-vn-guard15-probe-data-v1` v1; phải kiểm live trước submit.

Owner đúng là huylmhuhu, credential1 được chọn mà không đổi config global.
Quota live trước bước này: GPU còn 29,43h ngày 2026-09-14; không reservation.
Không cần tài khoản mới; các tác vụ model nặng chỉ chạy Kaggle.

Sau submission/terminal thật, cập nhật [sổ Kaggle](kaggle_resources.md) với
version/source/receipt. Giữ mọi semantic failure, không chạy lại để tăng điểm.
