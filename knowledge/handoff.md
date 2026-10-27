# Bàn giao phiên làm việc

Cập nhật: 2026-10-28. Lúc 06:10. Lộ trình [v2](../docs/project/roadmap_v2_rebuild.md), rebuild A.
**R4 security Test xong.** PR #4 đã merge, tag `phase5-closure` đã gắn. Tiếp theo: RQ3 robustness.

## Đang làm

**R4 security Test (2026-10-28, chạy một lần, không chạy lại).** `results/rebuild_a/adv_test_qwen3_8b`
(local, không track), eval `results/rebuild_a/adv_test_qwen3_8b_eval.json` + `.records.jsonl`.
2.100/2.100, 5 lỗi hạ tầng đã chạy lại, 4 model_error (KEYLEAK A0–A3). ASR ghép cặp A0 4 → A3 1 →
A4–A6 0 /150; benign A0 30, A3 15, A4–A6 5 /150; A6 v3 ≈ A5. Bảng và nhận xét: decision log
2026-10-28. Phân tích sâu (KEYLEAK OUTPUT_INVALID, benign harm 17/30 family, A6 không chuyển giao,
cỡ mẫu 30 family) để R5.

- Notebook R4 trên **meanalways** (lamhuy8904 hết quota): xem [sổ Kaggle](kaggle_resources.md).
  Keepalive đã tắt 05:50, notebook tự tắt sau 30 phút idle.
- Bài học vận hành: runner chỉ ping guard 10 phút/lần ở A0/A1; nếu một ping trùng lúc rớt mạng thì
  guard có thể idle gần 30 phút. Đợt sau chạy thêm keepalive riêng cho guard 5 phút/lần trong A0/A1.
- **RQ3 (owner quyết 2026-10-26):** tạo 250 biến thể clean robustness (50 task gốc Test × 5 loại),
  review, seal, đóng băng thành final_config_v2. Không sửa file nào trong manifest v1.
- Repo giữ **public**; luận văn phải nêu Test là public. HF token nên rotate (lộ trong log chat
  2026-10-28, chỉ local).

Lệnh clean Test (sau final_config_v2; mỗi backbone K một notebook, có thể chạy song song trên các
tài khoản khác nhau, ghi vào decision log trước khi chạy):
```
.venv/bin/python scripts/run_clean_dev_api_v1.py --model-key K --split test
.venv/bin/python scripts/evaluate_clean_rebuild_v1.py results/rebuild_a/clean_test_K --numfix \
  --output results/rebuild_a/clean_test_K_eval.json
```

Bật notebook (ví dụ meanalways, credential qua `KAGGLE_CONFIG_DIR` tạm, không vào Git):
```
export SSL_CERT_FILE=$(.venv/bin/python -c "import certifi;print(certifi.where())")
.venv/bin/python scripts/launch_vllm_serve_v1.py prepare --owner OWNER --model-key K --hf-token-env HF_TOKEN_R4
KAGGLE_CONFIG_DIR=... .venv/bin/kaggle kernels push -p build/kaggle/<folder>
.venv/bin/python scripts/launch_vllm_serve_v1.py discover --folder build/kaggle/<folder> --timeout-minutes 40
PYTHONPATH=src .venv/bin/python scripts/keepalive_vllm_v1.py --endpoint <folder>/endpoint.env=<run log> --every 10
```

## Bước tiếp theo

1. RQ3: tạo 250 biến thể robustness → review → seal → final_config_v2 (dry-run Dummy).
2. Clean Test + robustness cho 3 backbone, mỗi thứ chạy đúng một lần.
3. R0: sửa 21 test chỉ hỏng trên CI (PR riêng), dọn script cũ.
4. R5: thống kê, phân loại lỗi, review 10% trace; replay prompt KEYLEAK để ghi output thô.
5. Viết luận văn (`thesis/` còn trống): chương 1–3 ngay bây giờ.

## Ghi chép R0–R2 trước đó (đã xong)

- A0 Dev baseline name-first: Qwen 77, Llama 93, Gemma 99 /150 (decision log 2026-10-26).
- A6 v2 accepted: benign 20 → 115/200 trên replay, harm 5/200, A3–A5 không đổi.
- Bake-off guard: giữ Llama-3.2-3B (Prompt Guard 2 TP0/FP0). `docs/metrics_spec.md` xong.
- Token HF đang chèn vào notebook private (`--hf-token-env`); owner nên rotate token sau đợt chạy.
  Kaggle cho tối đa 2 phiên GPU nền mỗi tài khoản.
- PR #4: https://github.com/Lamhuy0489/react-vietnamese-agent/pull/4 (đã merge 2026-10-28, `5194c77`).

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
