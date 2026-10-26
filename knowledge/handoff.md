# Bàn giao phiên làm việc

Cập nhật: 2026-10-26. Lúc 19:45. Lộ trình [v2](../docs/project/roadmap_v2_rebuild.md), rebuild A.
R0 còn nợ phần dọn (PR #4, tag, script). R1 evaluator đã xong. **R3 đóng băng xong** (tag
`final-config`); tiếp theo là R4 chạy Test.

## Đang làm

**R3 đã đóng băng (2026-10-26, owner duyệt), tag `final-config`.** Manifest
`configs/final/final_config_v1.json` (sha256 `ae0ba2ec80464f0c…`) ghim 381 file. Runner và evaluator
nhận `--split test` và từ chối chạy nếu lệch dù chỉ một file. Dry-run Dummy trên Test:
clean 100/100, adversarial 2.100/2.100. Ước lượng R4 khoảng 11–12 giờ GPU.

- Bảng RQ2 Dev: A0–A5 từ `results/rebuild_a/adv_dev_qwen3_8b_a6v2`, A6 từ `adv_dev_qwen3_8b_a6v3`.
  ASR ghép cặp A0 26 → A3 15 → A4–A6 0; A6 v3 benign 60, utility under attack 40.
- **Chờ owner quyết:** RQ3 clean robustness (250 biến thể chưa từng được tạo). Đề xuất: trả lời
  RQ3 bằng các biến thể tiếng Việt của tập tấn công/benign Test và ghi phần clean là giới hạn.
- **Owner cân nhắc:** repo GitHub đang public và chứa dữ liệu Test lẫn GT; nên chuyển sang private
  trước R4 (Claude không tự đổi).

Lệnh R4 (sau khi bật notebook; `F`/`G` như lệnh resume dưới, kèm `--split test`):
```
PYTHONPATH=src caffeinate -ims scripts/retry_on_infra_v1.sh 20 120 -- .venv/bin/python \
  scripts/run_adversarial_dev_api_v1.py --split test --output results/rebuild_a/adv_test_qwen3_8b \
  >> build/kaggle/adv_test.log 2>&1
.venv/bin/python scripts/evaluate_adversarial_dev_v1.py results/rebuild_a/adv_test_qwen3_8b \
  --output results/rebuild_a/adv_test_qwen3_8b_eval.json
# Clean Test, mỗi backbone K (qwen3_8b, llama31_8b, gemma4_12b), một notebook:
.venv/bin/python scripts/run_clean_dev_api_v1.py --model-key K --split test
.venv/bin/python scripts/evaluate_clean_rebuild_v1.py results/rebuild_a/clean_test_K --numfix \
  --output results/rebuild_a/clean_test_K_eval.json
```

Lệnh resume dưới đây chỉ dùng khi phải chạy lại.

Lệnh resume (từ root; nếu notebook đã tắt thì push lại bằng launcher, `discover`, đổi `F`/`G`):
```
export SSL_CERT_FILE=$(.venv/bin/python -c "import certifi;print(certifi.where())")
F=build/kaggle/vllm_serve_v1_qwen3_8b_20261026_121043
G=build/kaggle/vllm_serve_v1_llama32_3b_guard_20261026_121043
source $G/endpoint.env; export GUARD_BASE_URL=$VLLM_BASE_URL GUARD_API_KEY=$VLLM_API_KEY
source $F/endpoint.env; export VLLM_BASE_URL VLLM_API_KEY
R=results/rebuild_a/adv_dev_qwen3_8b_a6v2
PYTHONPATH=src caffeinate -ims scripts/retry_on_infra_v1.sh 20 120 -- \
  .venv/bin/python scripts/run_adversarial_dev_api_v1.py --model-key qwen3_8b --output $R \
  >> build/kaggle/adv_full.log 2>&1
.venv/bin/python scripts/evaluate_adversarial_dev_v1.py $R --output ${R}_eval.json
```

## Bước tiếp theo

1. Owner quyết RQ3 robustness và visibility của repo.
2. R4: bật notebook Qwen + guard, chạy security Test (2.100 lượt); rồi clean Test cho 3 backbone.
   Chạy mỗi thứ đúng một lần, chỉ chạy lại khi lỗi hạ tầng.
3. R5: thống kê, phân loại lỗi, review 10% trace.
4. Owner merge PR #4 và gắn tag `phase5-closure`; dọn script.
5. Viết luận văn (`thesis/` còn trống): chương 1–3 ngay bây giờ.

## Ghi chép R0–R2 trước đó (đã xong)

- A0 Dev baseline name-first: Qwen 77, Llama 93, Gemma 99 /150 (decision log 2026-10-26).
- A6 v2 accepted: benign 20 → 115/200 trên replay, harm 5/200, A3–A5 không đổi.
- Bake-off guard: giữ Llama-3.2-3B (Prompt Guard 2 TP0/FP0). `docs/metrics_spec.md` xong.
- Token HF đang chèn vào notebook private (`--hf-token-env`); owner nên rotate token sau đợt chạy.
  Kaggle cho tối đa 2 phiên GPU nền mỗi tài khoản.
- PR #4: https://github.com/Lamhuy0489/react-vietnamese-agent/pull/4 (owner merge).

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
