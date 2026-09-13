# Điểm nối tiếp sau standalone shutdown CPU

2026-09-13. Đây là bản đồ triển khai kế tiếp, **chưa phải code đã tích hợp**.
[Worker v2](worker_shutdown_v2.md) và [handoff](handoff.md) quyết định mốc hiện hành.

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
- Current event validator chỉ kiểm consistency một event; chưa có cross-worker,
  cross-receipt PID/hash proof cho v2. Không quảng cáo nó như pair/native auditor.
- Exact archive/expanded worker mounts, offline import closure, 8 tools/recovery,
  public Dummy/resume, source hashes/identity pinned, rồi mới native diagnostic.

Hai giây normal-stop budget là lựa chọn diagnostic versioned, không kết luận đủ
cho GPU teardown hoặc cấu hình cuối luận văn. Không có Test/native failure nào
được dùng để tune ở mốc standalone CPU; dữ liệu cũ chỉ cho thấy thiếu quan sát.

Calculator pilot giữ nguyên 0 tool/guard calls. Diagnostic tiếp theo cần mục tiêu
tool/guard coverage được định trước và identity mới, không gọi là retry tăng điểm.
Không thay task/prompt âm thầm, không ghép kết quả của hai identity.

[Sổ notebook/Dataset](kaggle_resources.md) phải cập nhật mỗi lượt Kaggle mới.
