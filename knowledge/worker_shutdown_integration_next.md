# Điểm nối tiếp sau standalone shutdown CPU

2026-09-14. Bản đồ ban đầu lập ngày 2026-09-13; ba điểm CPU đầu bảng đã có
[pair/runtime v3](pair_runtime_v3.md), 74 focused tests và full 2.704 pass/1 skip đạt.
Hai điểm native cuối bảng nay có [wiring v2 CPU](native_shutdown_wiring_v2.md);
exact package/release auditor và GPU chưa đạt. [Handoff](handoff.md) quyết định
mốc đã được chọn nghiệm thu; không dùng bảng lịch sử để chạy lại việc đã xong.

## Các điểm cần version cùng nhau

| Điểm nối hiện tại | Điều cần giữ / bổ sung |
|---|---|
| `llm/model_pair_v1.py`: `PairConfig.execution`, `ModelPair.__init__` | Cả hai role phải tạo ShutdownBackend, cold/warm config đều giữ cùng graceful budget. Không tạo v1 worker rồi thay ngầm; protocol/hash riêng. Giữ parent ownership, sibling workers, reserved READY command, fail-stop. |
| `security_v1/pair_runtime_v2.py`: agent-only branch | A0/A1 hiện tạo trực tiếp WarmGuardBackend; không chỉ đổi paired branch. Tách cold/start và warm/call deadline cho agent-only nếu muốn so timing công bằng, ghi identity/trace và test riêng. |
| `validation/pair_runtime_audit_v2.py` | Hiện kiểm closed/reaped, chưa xác nhận stop/serve-return observations. Version adapter phải join shutdown event với đúng PID/config/worker, không chỉ gọi event validator rời rạc. |
| Native factories và seven-level runner | ModelPair construction đang nằm trong ordinary native factory; tránh nhận worker mới trên CPU nhưng vô tình vẫn tạo worker cũ trên GPU. Không sửa frozen ordinary/pilot source. |
| Native joined/release auditors | Thêm versioned profile/config/attempt bindings, partial failure và graceful-vs-recovered tách biệt. Không làm dữ liệu cũ trở thành schema mới. |

## Kiểm trước inference

- Cùng synthetic responses/observable v7 actions ở bảy mức; A0/A1 không guard.
- READY vẫn không phải model generation; cold/warm deadline identities đúng.
- Slow teardown và no-ack/hung worker cho từng role; startup failure, post-response
  worker death, timeout, close idempotence, partial cleanup và reaped handles.
- Chỉ gọi GRACEFUL khi ACK + serve returned + process exit 0 + reaped; worker
  trả zero exit đột ngột không có serve return vẫn là EXITED.
- Standalone event validator chỉ kiểm consistency một event. Pair/runtime auditor
  v3 đã bổ sung PID/config/event joins trên CPU; native auditor vẫn cần version
  riêng. Không quảng cáo standalone validator như pair/native auditor.
- Exact archive/expanded worker mounts, offline import closure, 8 tools/recovery,
  public Dummy/resume, source hashes/identity pinned, rồi mới native diagnostic.

Hai giây normal-stop budget là lựa chọn diagnostic versioned, không kết luận đủ
cho GPU teardown hoặc cấu hình cuối luận văn. Không có Test/native failure nào
được dùng để tune ở mốc standalone CPU; dữ liệu cũ chỉ cho thấy thiếu quan sát.

Calculator pilot giữ nguyên 0 tool/guard calls. Diagnostic tiếp theo cần mục tiêu
tool/guard coverage được định trước và identity mới, không gọi là retry tăng điểm.
Không thay task/prompt âm thầm, không ghép kết quả của hai identity.

[Sổ notebook/Dataset](kaggle_resources.md) phải cập nhật mỗi lượt Kaggle mới.

## Bước triển khai native cụ thể sau CPU acceptance

Factory/runner/joined auditor ở các bước 1–3 đã đạt bounded CPU wiring v2;
không làm lại. Phần release auditor, exact package và diagnostic ở bước 3–5
vẫn là công việc kế tiếp. Checklist dưới đây giữ để đối chiếu thiết kế.

1. Tạo entry point native riêng trả về `ShutdownPair`, cấu hình
   `ShutdownPairConfig` với identity model/revision hiện hành. Không sửa
   `ordinary_pair_probe_v1.native_pair` hoặc `request_policy_pair_v1.policy_pair`:
   các hàm frozen này vẫn tạo `ModelPair` v1. Không tạo pair v1 rồi thay workers.
2. Giữ cùng stack lazy cho mỗi role: `ThreadProgressFactory` →
   `RequestPolicyFactory` → `EfficientRequestFactory` → native factory.
   Kiểm lại model input/evidence path isolation, pinned snapshot, no eager load.
   A0/A1 dùng agent stack tương đương nhưng `AgentWorkerConfig`/runtime v3,
   không khởi tạo guard. Các native factory bên dưới có thể tái sử dụng nguyên
   trạng; composition và run identity cần version mới.
3. Version runner và native/release auditor cùng profile runtime v3. Bind
   sidecar metrics, request/generation/config hashes, PID và shutdown observations;
   kiểm partial failure, forced exit và VRAM recovery riêng, không suy từ ACK.
4. Đóng gói exact archive/expanded mounts, subprocess import/worker tests, public
   Dummy/resume và bộ regression; source phải được push trước inference.
   Ghi trước task IDs, coverage mong đợi và điều kiện dừng của diagnostic mới.
5. Chỉ sau preflight mới kiểm lại quyền/quota Kaggle và submit identity mới;
   cập nhật directory với URL/version/source/receipt thực tế. Kết quả calculator
   v1 zero-tool/guard vẫn giữ nguyên, không phải missing task để retry.

Đây là checklist chuẩn bị, không phải bằng chứng code native hoặc GPU đã đạt.
