# Nhật ký phiên chat

Mỗi phiên ghi một mục, mới nhất ở cuối. Mỗi mục gồm: mục tiêu, quyết định, việc đã
làm, việc còn dở. Chỉ ghi các dữ kiện đã xác minh. Không ghi credential, GT hay payload Test.
[Prompt cho phiên sau](next_session_prompt.md) · [Handoff](handoff.md).

## 2026-10-23 — Claude Code: đánh giá đồ án, dọn repo, lộ trình v2

- **Mục tiêu owner:** đánh giá tính khả thi, bỏ phần thừa, "đập đi xây lại" với lộ
  trình mới, lưu context để các phiên sau làm tiếp.
- **Đánh giá:** đề tài khả thi; benchmark và runtime A0–A6 là phần giá trị. Điểm yếu
  là quy trình bằng chứng quá nặng (287 script, 170 báo cáo, 348 manifest) và chưa
  có kết quả cho RQ1–RQ3.
- **Đã làm:**
  - Commit `a402772` (250 file còn dở, quét credential không thấy giá trị nào).
  - Dọn storage: xóa 3 file tar guard giống hệt nhau, trọng số Qwen2.5-1.5B, venv
    API và cache; nén `build/pytest_*` và `results/*preflight*` vào `archive_local/`.
  - Commit `8a2419e`: lộ trình v2.
  - Commit `6509ae0`: các quyết định R0.
- **Quyết định:** model RQ1 là Qwen3-8B, Gemma 4 12B, Llama 3.1 8B; RQ2 cố định
  Qwen3-8B; guard A2 chọn bằng bake-off trên Dev; ASR tính hành động thực thi,
  model_error tính thất bại.
- **Kiểm dữ liệu:** seal adversarial_v2 hợp lệ; clean v1.1 khớp 23 hash. Phát hiện:
  repo public chứa GT private, owner chưa quyết.
- **Còn dở:** merge vào main, tag, dọn script, metrics_spec; owner xin quyền HF Llama.
- **Bổ sung:** owner cho phép đập đi; chọn mức A, tức chạy lại pipeline từ Phase 1, giữ data và runtime. Không viết lại runtime, không làm lại data.

## 2026-10-23 (tiếp) — Claude Code: harness vLLM cho chạy lại mức A

- **Quyết định:** serve bằng vLLM trên Kaggle qua API (owner đồng ý); R4 dùng API hoặc
  batch tùy độ ổn định; guard Prompt Guard 2 chạy trên CPU local.
- **Đã làm:** notebook `vllm_serve_v1`, config `backbones_v2.yaml`, backend
  `openai_compat_v1` cùng 11 test, script kiểm endpoint, script smoke có checkpoint,
  [runbook](rebuild_a_runbook.md) kèm hướng dẫn xin quyền HF và Kaggle.
- **Còn dở:** owner chạy notebook ngày 24/10, pin revision, chạy smoke; Gemma 4 có rủi
  ro trên T4.

## 2026-10-25 — Claude Code: chạy thật Qwen3-8B trên Kaggle, A0 smoke

- **Đã làm:** kiểm 4 tài khoản Kaggle qua API (đều đăng nhập được, còn 20–25 h GPU,
  không notebook nào đang chạy). Thêm chế độ chạy nền cho `vllm_serve_v1`: tự sinh key,
  gửi URL đã mã hóa qua ntfy. Thêm `scripts/launch_vllm_serve_v1.py` cùng 2 test. Push lên
  lamhuy8904: v1 lỗi do torchaudio lệch CUDA; v2 READY. Pin Qwen3-8B `b968826d…`, vLLM 0.32.0.
- **Kết quả:** A0 smoke 20/20 completed, 0 lỗi parse/hạ tầng, 3/20 success (6/20 theo answer
  facts). Lỗi chủ yếu do model chọn sai nguồn và không gọi read/fetch.
- **Quyết định owner:** mỗi notebook một model; chạy song song dùng 2 notebook trên 2 tài khoản.
- **Prompt v2 (owner duyệt):** sửa system prompt chung và mô tả tool; `db_query` tự liệt kê
  schema. Bốn lần chạy smoke: 3 → 10 → 11 → 12/20, rồi đóng băng. Không đổi bộ chấm.
- **Seal:** seal adversarial pin byte các file prompt/tool, nên chuyển v2 sang module mới
  `a0_v2.py` và trả các file gốc về nguyên byte; check seal valid, 186 test liên quan đạt.
- **Clean Dev 150 × Qwen3-8B (A0, v2):** 71/150 (47,3%), 0 lỗi hạ tầng, khoảng 13 phút.
- **Còn dở:** prompt v3 cho ambiguous/db_document (owner quyết); Llama, Gemma; gắn secret
  `HF_TOKEN` qua UI cho notebook model gated; quyền Llama-3.2-3B còn 403.

## 2026-10-26 — Claude Code: prompt v3, numfix, per-tool schema, Llama

- **Prompt v3 (owner duyệt):** sửa luật 5 (lỗi retryable thì gọi lại, lỗi do lệnh sai thì sửa
  lệnh), thêm luật tra đủ nguồn và hỏi lại khi thiếu dữ kiện. Đổi tên module thành
  `prompts/a0_rebuild.py` (giữ cả v2). Chạy Dev 1 lần rồi đóng băng.
- **Bộ chấm:** regex số cũ bỏ sót số ở cuối câu ("bằng 876."). Sửa trong
  `validation/clean_rebuild_v1.py` (`--numfix`), chấm lại cả v2 và v3: 72 so với 79/150.
- **Harness:** Llama bị parse_failure 82/150 vì `arguments` là object tự do và key bị sắp
  xếp. Thêm `per_tool_schema` (mỗi tool một nhánh anyOf). Qwen giữ nguyên 79, Llama 30 → 59.
- **Llama-3.1-8B:** notebook riêng `react-vn-vllm-serve-v1-llama31-8b`, token chèn vào bản
  private. Smoke 8/20, Dev 59/150.
- **Còn dở:** Gemma, bake-off guard, A0–A6 Dev, phần dọn R0; owner nên rotate token HF.

## 2026-10-26 (tiếp) — Claude Code: Gemma 4, bake-off guard, R0

- **Gemma-4-12B:** không gated, vLLM 0.32.0 stable. bf16 và QAT đều hỏng ở kernel attention
  (head_dim 512 cần 96 KB shared memory, T4 có 64 KB; FlexAttention cũng vậy). Vá tile trong
  notebook. Smoke bf16 9/20, QAT 7/20. **Clean Dev bf16 99/150**, cao nhất (db_document 24/24).
- **Bake-off guard:** luật khai báo trước. Prompt Guard 2 86M (CPU, `build/venv_guard`) TP0
  FP0 trên 80 input Dev; giữ Llama-3.2-3B.
- **R0:** `docs/metrics_spec.md`. Sửa 3 test hỏng. Trả `evaluate_clean_v11_dev.py` về byte
  đã pin, chuyển phần mới sang `evaluate_clean_rebuild_v1.py`. Full pytest xanh. Mở PR #4.
- **Owner hỏi tối ưu Llama riêng:** không làm, vì RQ1 cần cùng prompt, tool, schema và bộ chấm.
- **Còn dở:** owner merge PR và gắn tag; dọn script cũ; R1 evaluator; A0–A6 Dev.
