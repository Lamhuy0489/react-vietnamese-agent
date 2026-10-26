# Bàn giao phiên làm việc

Cập nhật: 2026-10-26. Lúc 19:00. Lộ trình [v2](../docs/project/roadmap_v2_rebuild.md), rebuild A.
R0 còn nợ phần dọn (PR #4, tag, script). R1 evaluator đã xong. **R2 xong trên Dev:** ASR ghép
cặp, A6 v3 accepted; chờ owner duyệt đóng băng R3.

## Đang làm

**R2 Dev xong, chờ owner duyệt đóng băng R3.** Bảng RQ2 Dev ghép từ hai thư mục: A0–A5 lấy
từ `results/rebuild_a/adv_dev_qwen3_8b_a6v2`, A6 lấy từ `results/rebuild_a/adv_dev_qwen3_8b_a6v3`.
Mỗi thư mục có `_eval.json` và `.records.jsonl`. Chi tiết trong decision log, các mục ngày 2026-10-26.

- Chỉ số chính mới: **ASR ghép cặp** (attributable ASR, owner đã duyệt): A0 26, A1 20, A2 20,
  A3 15, A4 0, A5 0, A6 0 /200. ASR thô vẫn báo: 100, 93, 93, 85, 40, 40, A6 v3 20.
- **A6 v3 được chấp nhận:** benign 55 → 60, utility under attack 35 → 40, ASR thô 40 → 20,
  không có ca hại mới. v3 là mặc định của runner.
- Giới hạn còn lại của A6: QUANTITY (giá trị lấy từ tài liệu không tin cậy, chặn là đúng)
  và LEASE (guard phủ quyết câu lệnh người dùng; hợp đồng cấm gỡ phủ quyết của guard).
  Các bài khác A6 không làm được thì A0 cũng không làm được.
- Notebook Kaggle (Qwen v4 + guard v2) đã tắt keepalive; sẽ tự tắt sau 30 phút idle.

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

1. Owner duyệt đóng băng R3: model, prompt v3, guard, A6 v3, evaluator `adversarial_dev_v1`
   có ASR ghép cặp. Cập nhật `phase_status`/current_status.
2. R4: chạy Test một lần (A0–A6), chỉ sau khi đã đóng băng.
3. Owner merge PR #4, gắn tag `phase5-closure`; dọn script (298 → dưới 30).
4. Viết luận văn chương 1–3 (`thesis/` còn trống).
5. Sau R4 mới xét fine-tune LLM tiếng Việt (tùy chọn). JEPA/Jev làm guard: đã bỏ.

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
