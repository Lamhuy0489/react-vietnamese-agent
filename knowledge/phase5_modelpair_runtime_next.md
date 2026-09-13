# Bước tiếp theo — ghép ModelPair với runtime

Đây là ghi chú triển khai từ code hiện hành, chưa phải phép thử đã chạy.

## Điểm nối đã xác định

- `src/react_agent/llm/model_pair_v1.py`: `ModelPair.generate(role, messages,
  config)` đã có timeout/identity/worker ownership và snapshot lifecycle.
- `src/react_agent/llm/ordinary_pair_probe_v1.py`: `native_pair(...)` dùng
  package/factories đã có evidence GPU, nhưng `run(...)` chỉ là probe sáu calls.
- `src/react_agent/security_v1/runtime_v7.py`: đã có Broker/scope/FinalGate,
  nhưng kế thừa cơ chế guard của v5, chưa sử dụng task-owned ModelPair.

## Cạm bẫy không được lặp

Không truyền một `ModelPair` đang sống vào `guard_factory` rồi để
`WarmGuardBackend` spawn thêm process. `ModelPair._enter()` ràng buộc owner PID;
cách đó sai ownership, có thể tạo worker thừa hoặc lỗi trước inference.
Giải pháp cần host-side role adapters gọi cùng một pair, không fork lại pair.
Giữ riêng startup READY, cold load, generation và cleanup; không tính READY như
model inference và không gộp forced cleanup thành graceful.

## Acceptance trước GPU

1. Một pair/task; agent/guard adapter cùng parent, không share task state.
2. A0 chỉ agent, không load hoặc gọi guard; A2–A6 giữ guard structured output,
   fallback và trace. So sánh A0 cùng backend/config, không đổi prompt/decoding.
3. Tool Broker/Pre/Post/Final coverage và scope/entitlement v2 giữ hiệu lực.
4. Completed/parse/model/timeout/cancel/max-step đều đóng cả worker; assert
   actual process exit/handles, không chỉ boolean hoặc thiếu warning.
5. Cold/warm counters và per-role requests khớp trace; ghi identity của nguồn,
   model revisions, generation, source catalog và seed.
6. Exact Kaggle package preflight cả archive/expanded layout trước upload.
   Đọc skill/preflight, kiểm quota/private Dataset và dùng run identity mới.

Chỉ sau đó chạy synthetic multi-step native matrix trên Kaggle. Grouped Dev
guard selection/quality là phép thử riêng; không tune từ sáu-call probe cũ,
không mở Test. Xem [handoff](handoff.md) để biết gate CPU đã được xác nhận chưa.
