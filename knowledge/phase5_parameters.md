# Thông số Phase 5 đã khóa

Cập nhật: 2026-10-02. Trích trực tiếp từ các manifest đã kiểm hash; phục vụ tái lập
và bàn giao, không phải cấu hình kết nối đang hoạt động. Không chứa API key/endpoint.

| Thành phần | Thông số đã dùng |
|---|---|
| Runtime release | `419938b4c2bc9842a92b2d797126d69ae727c953` |
| Runtime family | `phase5_v14_closure_v1` |
| Task agent | Qwen3-8B; notebook lamhuy8904 version 1, worker source e4078d7 |
| Guard | Llama3.2-3B-Instruct; notebook meanalways version 3, worker source 77bc456 |
| Agent decoding | temperature 0; seed 42; max_new_tokens 512 |
| Guard decoding | temperature 0; seed 42; max_new_tokens 128 |
| Runtime bounds | max_steps 4; max_format_retries_per_step 0; tool timeout 5 s |
| API deadline | HTTP 150 s; local guard process 180 s |
| Diagnostic continuation | GET admission 12 s; POST 150 s; same pinned boot |
| Normalizer / FINAL | normalizer_v1 / final_encoded_full_value_v1 |
| Guard flags | SUSPICIOUS hoặc MALICIOUS; không đồng nhất với runtime DENY |
| Checkpoints đã đóng | closure 84; guard diagnostic 80; không chạy lại |

Model revision fingerprints, worker/session/boot IDs lịch sử, toàn bộ cấu hình
A0–A6, prompt/data/environment hashes và thông số đầy đủ ở
[bản JSON thông số](../experiments/manifests/phase5_frozen_parameters_20261002.json).
Các session/boot ID này không được tái sử dụng để giả làm phiên cũ sau khi restart.

Kết quả phải giữ: 20/20 DoD; 467 tests; native 72 completed + 12 model_error;
11 lỗi HTTP422 là OUTPUT_SCHEMA_FAILED. Guard: TP21/FN19/FP5/TN35 trên 40 cặp Dev
thuộc 8 nhóm. A6 vẫn chặn dư C6 và chỉ có provenance giới hạn.

[Completion receipt](../experiments/manifests/phase5_completion_20261002.json) ·
[Closure report](../docs/evaluation/phase5_completion_20261002.md) ·
[Guard report](../docs/evaluation/phase5_guard_quality_v1_report.md).

Gói bằng chứng local: `build/releases/phase5_completion_evidence_20261002.tar.gz`
(5,54 MiB, 5.928 file); checksum và inventory nằm trong completion receipt.
Giữ `build/`, `results/`, source snapshot, journal, manifest, dữ liệu và source
đã khóa. Gói local chưa phải bản sao ngoài máy hoặc bản đã đẩy lên GitHub.
