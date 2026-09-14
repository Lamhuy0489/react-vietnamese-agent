# Document diagnostic v1

2026-09-14 — đã submit native version1; Phase 5 chưa accepted.

Theo [preregistration](../docs/architecture/phase5_document_diagnostic_v1_contract.md),
chạy một task công khai tổng hợp đọc CDOC_034, một lần ở mỗi A0–A6, cùng model/
prompt/decoding/deadlines đã pin. Chỉ đo path/lifecycle/timing, không ASR/FPR hay
benchmark utility. Dữ liệu Test/private oracle không được mở.

CPU draft01 ở `results/phase5_document_devcheck01` phát hiện A4–A6 không hiểu
namespace CDOC, nên chặn đọc hợp lệ. Giữ output này, không chọn nghiệm thu.
Scope v3 bổ sung bounded CDOC, không alias sang DOC; runtime v8 chỉ thay scope.
V7 và toàn bộ receipt/source frozen giữ nguyên. CPU draft02 đạt 42 focused tests
trong 8,64s, có doc_read và guard Pre/Post qua đủ các level dự kiến; đây là stub.

Source inference đã commit `54aa3ec`. Exact archive/expanded preflight01 đạt:
102 overlay files, 110 source/430 raw hashes đã re-audit khớp; cả hai layout có
7 doc_read và 10 guard Pre/Post calls giả lập. [Preflight receipt](../experiments/manifests/phase5_document_probe_v1_preflight01.json)
SHA-256 `419c4b28f7d6f79120c3e8bccbec8345dfac7062818020a7208546058e926c0e`.
49 focused tests đạt 7,25s; full **2.813 pass/1 optional-tqdm skip**, 693,77s.
Setup/Ruff/mypy 357 files/knowledge đạt. [CPU01 receipt](../experiments/manifests/phase5_document_probe_v1_cpu01.json)
SHA-256 `159b2269d234b89530177094498085364af9a52d1bba3fb30f09b6eb431e9196`.
501 source/158 raw hashes khớp, 169 data unchanged; parent622 entries khớp.
Output `results/phase5_document_probe_v1_cpu01` đã xong, không chạy trùng/ghi thêm.
7 actual synthetic runtime receipts; không có mocked native-shaped records ở focused QA.

GitHub đã push evidence `8836e9c`, rồi submit private notebook
`huylmhuhu/react-vn-document-runtime-v1` **version1**, T4/7200s/offline.
[Submission receipt](../experiments/manifests/phase5_document_gpu_v1_submission01.json)
và [sổ link](kaggle_resources.md). Tiếp: theo dõi version1 và tải/audit khi terminal;
không gửi trùng. Dataset dùng lại private
`huylmhuhu/react-vn-guard15-probe-data-v1` v1. Live 2026-09-14 đã xác nhận private/
ready/v1 và quyền model version1; mine search tên mới trả Not found.
[Access snapshot](../experiments/manifests/phase5_document_access01.json) không phải reservation.

Owner đúng là huylmhuhu, credential1 được chọn mà không đổi config global.
Quota live trước bước này: GPU còn 29,43h ngày 2026-09-14; không reservation.
Không cần tài khoản mới; các tác vụ model nặng chỉ chạy Kaggle.

Sau submission/terminal thật, cập nhật [sổ Kaggle](kaggle_resources.md) với
version/source/receipt. Giữ mọi semantic failure, không chạy lại để tăng điểm.

Giới hạn phát hiện trước native: cue kế thừa `cho` khớp cụm hợp lệ `cho biết`,
nên instruction diagnostic hiện có `explicit_scope=false`. Trusted public first
read đi qua cơ chế no-scope-trigger; lượt này không chứng minh user-bound scope
authorization. Unit test `Đọc CDOC_034` có anchor chính xác. Giữ limitation cho
broader semantic validation; không đổi input/policy trong lúc full QA chạy.
[Report](../docs/evaluation/phase5_document_diagnostic_v1_report.md) tách rõ các loại bằng chứng.
