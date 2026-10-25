# Bàn giao phiên làm việc

Cập nhật: 2026-10-26. Đang ở **R0 (Reset)** của
[lộ trình v2](../docs/project/roadmap_v2_rebuild.md). Đã chốt 3 quyết định R0;
phần dọn repo của R0 chưa làm.

## Đang làm

R0, tuần 24/10–30/10. Đã xong:

- Commit/push toàn bộ việc còn dở.
- Dọn local storage: khoảng 18 GB xuống 2,3 GB; xem [storage](storage_and_obsidian.md).
- Chốt model, guard và chỉ số.
- Kiểm tính toàn vẹn của dữ liệu.

## Bước tiếp theo

0. **Xong 2026-10-25:** Qwen3-8B chạy thật trên Kaggle (lamhuy8904, v2), pin revision
   `b968826d…` và vLLM 0.32.0. A0 smoke với prompt v1 đạt 3/20. Owner duyệt sửa prompt chung
   và mô tả tool, chỉ tinh chỉnh trên smoke. **Prompt v2 đã đóng băng: 12/20 strict, 14/20 theo
   answer facts** (decision log 2026-10-25). Kết quả tại `results/rebuild_a/smoke_qwen3_8b*`.
   Prompt v2 nằm ở `prompts/a0_v2.py` và được bật bằng `activate()`. Không sửa
   `react_a0.py`, `context.py` hay các file tool, vì seal adversarial pin byte của chúng.
   **Clean Dev 150 × Qwen3-8B: 71/150 = 47,3%.** db_document 0/24, ambiguous 0/15.
   Lệnh chạy: `scripts/run_clean_dev_api_v1.py`, chấm bằng `evaluate_clean_v11_dev.py --full-dev`.
   **2026-10-26:** prompt v3 (`prompts/a0_rebuild.py`, sửa luật lỗi tool và hỏi lại) được
   owner duyệt, chạy Dev 1 lần rồi **đóng băng**. Sửa bộ chấm số ở cuối câu
   (`validation/clean_rebuild_v1.py`, `--numfix`). Sửa harness: schema giải mã theo từng tool
   (`per_tool_v1`), vì Llama bị parse_failure khi `arguments` để tự do.
   **Kết quả (v3 + per_tool + numfix):** Qwen smoke 12/20, Dev 79/150; Llama smoke 8/20,
   Dev 59/150. Bảng theo nhóm nằm trong decision log 2026-10-26.
   Việc tiếp: Gemma-4-12B (rủi ro cao trên T4, xem runbook), rồi bake-off guard, rồi A0–A6 Dev.
1. Token HF của owner đã có quyền Llama-3.1-8B, Prompt-Guard-2-86M, Gemma-4-12B; Llama-3.2-3B
   còn 403. Gắn `HF_TOKEN` làm Kaggle Secret qua UI cho notebook của tài khoản chạy model gated.
   Mỗi notebook một model. Kaggle cho tối đa 2 phiên GPU chạy nền mỗi tài khoản.
   Llama đã chạy bằng cách chèn token vào notebook private (`--hf-token-env`); owner nên
   rotate token HF sau đợt chạy.
2. Merge branch hiện tại vào `main` (qua PR), gắn tag `phase5-closure` trên `6509ae0`.
3. Dọn trên `main`: gom các script cũ, chưa dùng (v1/v2, preflight, chẩn đoán) vào
   `scripts/legacy/` hoặc xóa, chỉ giữ dưới 30 script đang dùng. Chạy
   ruff/mypy/pytest sau khi dọn. Không đổi các đường dẫn mà manifest hash vẫn tham chiếu
   nếu receipt còn cần audit lại; lịch sử khôi phục qua tag.
4. Viết `docs/metrics_spec.md` theo các quyết định trong decision log ngày 2026-10-23.
5. Sang R1–R2 theo mức rebuild A: harness mới (1 worker API và 1 evaluator), rồi chạy lại
   A0 smoke → clean Dev × 3 model → bake-off guard → A0–A6 Dev. Xem mục 2b của lộ trình.

## Bằng chứng

- Smoke Qwen3-8B 2026-10-25: `results/rebuild_a/smoke_qwen3_8b/` (local, không track).
  Notebook: [sổ Kaggle](kaggle_resources.md). Launcher có 2 unit test.

- Quyết định: [decision log](../docs/project/decision_log.md), mục ngày 2026-10-23.
- Kiểm dữ liệu: `scripts/assemble_adversarial_release.py --action check`
  cho kết quả valid, test_sealed, 700 biến thể; 23 file clean v1.1 khớp hash.
- Harness mới: 11 unit test của `openai_compat_v1` đạt; chạy thử runtime với
  transport giả: completed, và lỗi TIMEOUT được tính là lỗi hạ tầng. Chưa chạy trên Kaggle thật.
- Phase 5: [completion receipt](../experiments/manifests/phase5_completion_20261002.json).

## Giới hạn

- **Repo GitHub đang PUBLIC** và chứa `data/clean/v1_1/private/*` (GT clean, gồm cả
  Test) cùng payload Test của adversarial. Owner cần quyết định có chuyển repo sang
  private trước Phase 7 hay không. Không tự đổi visibility.
- Không được sửa dữ liệu đã seal. Muốn tinh chỉnh dữ liệu phải tạo version mới
  và chỉ làm trên Dev.
- Guard recall 52,5%, 12/84 model_error, C6 bị chặn dư. Các điểm này để R2 xử lý trên Dev.
- 3 unit test cũ đang hỏng từ trước (không do harness mới): `test_deploy_structured_pair_v3`
  (KeyError 'cfg'), `test_document_package_v1` và `test_shutdown_package_v2` (pin hash
  nguồn cũ). Xử lý khi dọn script cũ ở R0. Còn lại 3.429 unit test đạt.
- Chưa có reviewer thứ hai; Minh chưa nhận lời mời GitHub.
- [Handoff trước lộ trình v2](history_20261023_before_roadmap_v2_handoff.md).
