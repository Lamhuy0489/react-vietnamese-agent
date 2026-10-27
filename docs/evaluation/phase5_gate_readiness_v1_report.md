# Phase 5 — báo cáo kiểm tra readiness 20 DoD

Cập nhật 2026-09-28. Báo cáo này được tạo bởi
[`audit_phase5_gate_readiness_v1.py`](../../scripts/audit_phase5_gate_readiness_v1.py)
và receipt cục bộ `build/evaluation/phase5_gate_readiness_v1.json`. Nó là một
kiểm tra admissibility/readiness có tính fail-closed; **không phải biên bản
nghiệm thu Phase 5**.

## Kết quả hiện tại

- Đủ 20 mục DoD trong bản đồ, nhưng cả 20 vẫn có `overall_status: open`.
- 16 mục có file evidence CPU/cơ học được lập chỉ mục (không phải 16 cổng đã pass): DoD 1, 2, 3, 4, 6, 7, 8, 10, 11,
  12, 13, 14, 16, 17, 18 và 19.
- 3 mục chỉ có bằng chứng chẩn đoán: DoD 5 (A2/guard), DoD 9 (A6
  provenance) và DoD 15 (benign utility).
- DoD 20 (formal freeze) chưa có bằng chứng CPU đủ điều kiện.
- Pilot API Dev `pilot01` có 37/37 checkpoint hoàn tất: 21 agent task và
  16 guard control; `failed=0`, `interrupted=0`, `missing=0`.
- Metadata của pilot ghi `test_tasks_loaded=0` và
  `private_ground_truth_loaded=0`. Validator chỉ đọc `manifest.json`,
  `summary.json` và evaluator metadata; không đọc task payload, Test hay
  private ground truth.

Readiness không tự nâng cổng lên `closed`: mọi mục vẫn bị chặn bởi điều kiện
native tương ứng trong `native_blocker`. Việc một task có checkpoint hoàn tất,
JSON có schema hợp lệ, hoặc một unit test pass không được coi là semantic
quality, A0–A6 integration, lifecycle reliability hay formal freeze.

## Blocker cần đóng bằng candidate native

1. `StructuredHTTPBackend` hiện chỉ nhận `ActionTurn | FinalTurn`; typed
   reference/model-plan bridge nay có adapter `StructuredPlanHTTPBackend` riêng
   và diagnostic theo [protocol](structured_plan_api_v1_protocol.md). Điều này
   chưa đủ tuyên bố A6 provenance đã tích hợp với runtime chính.
2. Chưa có run prospective gắn API agent/guard với `SecurityRuntime` v5 qua
   đủ A0–A6, giữ cùng task/data/tools/decoding và ghi Pre/Post/Final,
   cumulative parity, provenance và egress joins.
3. Pilot hiện tại là diagnostic: agent utility 3/21 (14,29%), guard bắt
   5/8 attack (62,5%) và flag 3/8 benign (37,5%). Các số này phải được giữ
   nguyên trong mẫu số; chưa đủ để đóng guard quality hoặc benign utility.
4. Checkpoint/resume của runner không thay thế bằng chứng cancellation,
   session isolation, request-delivery uncertainty và lifecycle của API
   profile.
5. Chưa có một receipt freeze buộc source, model revision, worker hash,
   settings, raw artifacts, lifecycle audit và mapping 20 DoD trong cùng
   một run identity. RQ1 cũng vẫn yêu cầu ba task backbones; cặp Qwen agent
   và Llama guard chỉ là một agent backbone cùng một guard.

## Quyết định chạy notebook

Ngày2026-09-28, sau pilot hai notebook v1 đã COMPLETE. Theo yêu cầu owner,
hai notebook đã restart lên v2 với source/model giữ nguyên, package release02a,
preflight4/4 và probe cả hai READY. Worker hiện hành đã nhận inline Plan schema;
chỉ cần adapter ở host cho diagnostic này. Xem [sổ Kaggle](../../knowledge/kaggle_resources.md).
READY không chứng minh quality, remote cancellation hoặc Phase5 acceptance.

## Phạm vi và bất biến

Audit này chỉ đọc evidence và hash file, không sửa dữ liệu frozen, không mở
held-out Test, không đưa ground truth vào prompt/policy/runtime, không ghi
credential/endpoint vào receipt, và luôn xuất `phase5_accepted: false`.
