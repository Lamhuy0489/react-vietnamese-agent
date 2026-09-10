# Context stress — kiểm tra artifact độc lập

Cập nhật 2026-09-10. Chỉ Phase 5; không đổi frozen backend, dataset, decoding,
nguồn hoặc raw GPU lịch sử. Đây là CPU audit milestone, chưa context-stress GPU.

## Phần đã triển khai

- `src/react_agent/validation/context_stress_audit_v1.py`: kiểm đúng 23 file cho
  một cặp HF hoàn tất; từ chối partial/error, file thừa/thiếu/symlink, duplicate
  JSON keys, nonfinite numbers và coercion boolean thành số.
- Kiểm nguồn khai báo/model/config, PID và toàn bộ snapshot/event/attempt từ
  ready → agent → guard → close; loader metrics, deadline, một lần load/role,
  ACK, cleanup method, sáu mẫu recovery. Không suy forced exit thành graceful.
- Tính lại 28 layers KV/role, shape/head/FP16-byte arithmetic, placement20/8,
  cache4607/4223 sau sinh và4608/4224 sau forward riêng. Kiểm token counts/hash
  continuity, từng allocator cap/order/peak và global endpoint.
- So sánh đủ69 serialized **submitted** GenerationConfig fields với fresh
  Transformers5.5.0:55 giá trị `null`,13 tham số explicit vàversion. Đây chưa
  phải effective policy sau thư viện resolve defaults; xem phát hiện bên dưới.
  Không lưu text/token arrays/hidden states.
- Kiểm thời gian containment tokenizer + generation + final forward ≤ backend
  ≤ worker generation ≤ worker elapsed ≤ host call. Throughput là output tokens
  chia aggregate generation gồm prefill, không phải decode-only throughput.
- CLI `scripts/audit_phase5_context_stress.py` chỉ viết kết quả mới ngoài raw;
  cùng đầu vào cho audit byte-identical, không tự gọi model hay sửa artifact.
- `scripts/check_phase5_context_stress_compatibility.py`: kiểm SHA wheel thật,
  AST constructor70 fields/serialized69, Qwen forward args và DynamicLayer.
  Không import/install Transformers/Torch hoặc tải/load weights.

## Bằng chứng và giới hạn

77 tests mới đạt (70 audit/CLI/mutation và7 static compatibility). Artifact trong
tests là **GPU-shaped synthetic receipts**, không phải kết quả GPU. Hai CLI
audit trong test cho bytes giống nhau và giữ nguyên23 raw hashes.
Static check wheel thật đã đạt, raw receipt:
`results/phase5_context_stress_static_compatibility01.json`.
Full suite đạt1.671pass/1optional native skip trong358,82s (JUnit358,688s),
XML `results/phase5_context_stress_audit_v1_release01_pytest.xml`.
Setup/Ruff/mypy253files/knowledge đạt. [Release receipt](../experiments/manifests/phase5_context_stress_audit_v1_release_qa01.json)
ghim source/evidence hashes;146 frozen entries/296oldGPUraw/17overlay và4context
source files nguyên vẹn. Hai static checks01/02 có bytes giống nhau. Không job
local hoặc context GPU đang chạy sau mốc này; chưa có submission ngữ cảnh dài.

Auditor kiểm tính nhất quán của ghi nhận; `source_authenticated=False` luôn được
giữ ở lớp này. Hash/count không đủ để tái tạo tokenizer hoặc độc lập chứng minh
GPU đã chạy. Release auditor ngoài cùng còn phải xác thực remote wrapper/source,
frozen bundle, exact preflight, snapshot tokenizer/model metadata và raw hashes.
`phase5_accepted=False`, `ipc_cleanup_verified=False`; không claim semantic
quality, prefill riêng, continuous global peak hay không thể rò IPC.

## Bước tiếp theo

Phát hiện mới trước submit: pinned `_prepare_generation_config` điền các trường
None từ `self.generation_config`, rồi global defaults. Guard publisher có
repetition_penalty1.1,temperature0.7,top_p0.8,top_k20. Explicit do_sample=False
vẫn giữ nên không suy các giá trị sampling thành việc thực sự lấy mẫu.
[Finding/hash nguồn](../experiments/manifests/phase5_context_stress_generation_defaults_finding01.json).
Backend v1 ghi **submitted** config trước generate, không ghi resolved policy;
không thể gọi đây là full policy provenance. Không sửa nguồn d07e914 hoặc giả
rằng auditor23files chứng minh đủ policy. Chưa có context GPU để phải rerun.

Trước GPU cần thêm versioned recording/verification cho publisher/resolved
generation policy, test precedence/None/defaults và auditor tương ứng. Sau đó
tạo **file mới** wrapper/builder/release auditor, compose 17 prior overlay files
và4 context files; giữ native progress-policy preflight riêng vì context CLI
stub không cấu hình tqdm. Exact archive/expanded/PAX 8tools/21Dummy/resume,
source/receipt push, kiểm quota/private inputs rồi một GPU identity mới.
Không đổi deadline/decoding để chọn kết quả đẹp; preserve failure trước mọi
deviation. Các gate runtime integration/A4/final/grouped Dev/freeze vẫn mở.
