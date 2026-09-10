# Context geometry v1 — logic CPU, chưa stress GPU

Cập nhật 2026-09-10. Theo
[thiết kế context stress](../docs/architecture/phase5_context_stress_v1_design.md),
module `src/react_agent/llm/context_geometry_v1.py` chuẩn bị hình dạng token
cho diagnostic riêng; chưa gắn vào loader/runtime/Kaggle hoặc benchmark prompt.

- Fixed seed tiếng Việt tổng hợp, encode không special tokens; lặp rồi lấy
  prefix của seed để đủ đúng 4.096 input IDs. Không padding, không truncate
  yêu cầu user hoặc benchmark. Kiểm IDs nguyên, trong vocabulary và không
  mang special/pad/EOS token trong seed. Caller phải bind tokenizer identity
  vào snapshot pin; helper không tự xác thực model hay tokenizer artifact.
- Agent yêu cầu 512 new tokens, guard 128; kiểm prefix input không thay đổi.
  Receipt chỉ chứa count/hash, không decode hoặc lưu generated text.
- Cache sau generation có boundary input+output−1; chỉ cờ full-boundary khi
  có observation riêng sau final-token forward. Helper không thực hiện forward,
  không tự chứng minh KV resident bytes hoặc continuous peak memory.
- 35 test mới đạt trên synthetic tokenizer/IDs. Full QA hoàn tất: 1.552 đạt,
  1 optional native tqdm skip trong 343,38s; setup/Ruff/mypy 248 files/knowledge đạt.
  [QA receipt](../experiments/manifests/phase5_context_geometry_v1_qa01.json)
  bind source/test hashes và XML `results/phase5_context_geometry_v1_release01_pytest.xml`.

Tiếp nối: [stress backend/runner](context_stress_v1.md) đã có fresh forced-length
generation/cache, timing và peak counters, PID-bound stages/finally cleanup;
đang CPU QA, chưa native execution. Cần audit/exact GPU preflight riêng.
Chưa native tokenizer/model-generation test,
chưa gói hoặc lượt context-stress GPU. Không dùng helper làm bằng chứng đạt
maximum-context gate hoặc Phase 5 acceptance. Không sửa lượt pair-progress GPU
đang chạy hoặc 17 overlay files đã pin.
