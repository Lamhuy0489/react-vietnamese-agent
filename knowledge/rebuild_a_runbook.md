# Runbook chạy lại (mức A): vLLM trên Kaggle, gọi API từ local

Cập nhật: 2026-10-26. Đã chạy thật cả 3 model và guard (xem [sổ Kaggle](kaggle_resources.md)). Đây là runbook **hiện hành**; `api_experiment_runbook.md` chỉ là lịch sử Phase 5. Xem [lộ trình v2](../docs/project/roadmap_v2_rebuild.md), mục 2b.

## Bản đồ: chạy ở đâu, lưu ở đâu (đọc trước mỗi phiên)

Mục này là nguồn duy nhất. Nếu thêm runner hoặc đổi chỗ lưu, sửa mục này trước.

**Chạy:** luôn từ root repo, bằng `.venv/bin/python`, với
`export SSL_CERT_FILE=$(.venv/bin/python -c "import certifi;print(certifi.where())")`.
Model chạy trên Kaggle (mỗi notebook một model, tối đa 2 phiên GPU nền mỗi tài khoản);
runtime, tool và bộ chấm chạy ở local.

**Endpoint:** `build/kaggle/vllm_serve_v1_<model>_<stamp>/endpoint.env` (gitignored, 0600).
Bật notebook: `launch_vllm_serve_v1.py prepare` → `kaggle kernels push -p $F --accelerator NvidiaTeslaT4`
→ `launch_vllm_serve_v1.py discover --folder $F` (xem "Cách nhanh" bên dưới). Notebook tự tắt sau
30 phút không có request: **không bao giờ suy ra endpoint còn sống** từ file cũ; kiểm bằng
`.venv/bin/kaggle kernels status <owner>/<slug>`. Slug và version ghi ở [sổ Kaggle](kaggle_resources.md).

| Việc | Lệnh | Kết quả (local, không track) |
|---|---|---|
| Smoke 20 task | `scripts/run_smoke_api_v1.py --model-key K` | `results/rebuild_a/smoke_<K>*/` |
| Clean Dev 150 | `scripts/run_clean_dev_api_v1.py --model-key K --prompt v3` → `evaluate_clean_rebuild_v1.py --full-dev --numfix` | `results/rebuild_a/clean_dev_<K>*` |
| A0–A6 Dev 400 × 7 | `scripts/run_adversarial_dev_api_v1.py --model-key qwen3_8b --output R` (cần thêm `GUARD_BASE_URL/KEY`) → `evaluate_adversarial_dev_v1.py R --output R_eval.json` | `results/rebuild_a/adv_dev_qwen3_8b_a6v2{,_eval.json}` |
| Log lượt dài | chuyển hướng `>> build/kaggle/<tên>.log` | `build/kaggle/*.log` |

Lệnh resume đầy đủ của lượt đang dở luôn nằm trong [handoff](handoff.md), mục "Đang làm".

**Lượt dài (> vài phút):** bọc bằng `caffeinate -ims scripts/retry_on_infra_v1.sh 20 120 -- <lệnh>`.
Runner trả rc=2 khi endpoint không với tới hoặc còn lượt thiếu, nên wrapper tự chạy lại;
checkpoint theo lượt nên resume không mất kết quả. Chạy nền một lần và chờ thông báo, không
kiểm tra lặp lại qua nhiều lượt chat.

**Ghi kết quả ở đâu:**

| Nội dung | File |
|---|---|
| Số liệu, quyết định, luật chấp nhận khai báo trước | `docs/project/decision_log.md` |
| Trạng thái ngắn và mốc đã xác minh | `knowledge/current_status.md` |
| Đang làm, lệnh resume, bước tiếp theo | `knowledge/handoff.md` |
| Tóm tắt từng phiên | `knowledge/session_log.md` (thêm mục mới ở cuối) |
| Prompt mở phiên sau | `knowledge/next_session_prompt.md` (viết lại khối `text` mỗi cuối phiên) |
| Notebook Kaggle: slug, version, boot, revision | `knowledge/kaggle_resources.md` (mục "Mốc hiện hành") |
| Ghi nhớ riêng của Claude | `~/.claude/projects/.../memory/` (không trong Git) |

**Cuối phiên:** làm theo danh sách trong `CLAUDE.md`. Không ghi credential, URL tunnel, GT private
hay payload Test vào bất kỳ file nào.

## Thành phần

| File | Vai trò |
|---|---|
| `notebooks/kaggle/vllm_serve_v1/vllm_serve_v1.ipynb` | Serve một model bằng vLLM qua API kiểu OpenAI, mở tunnel cloudflared, tự tắt khi không có request |
| `configs/models/backbones_v2.yaml` | Repo và revision đã pin của 3 model và 2 guard ứng viên |
| `src/react_agent/llm/openai_compat_v1.py` | Backend local: ép JSON theo schema, seed 42, request_id, kiểm danh tính model, tách lỗi hạ tầng khỏi lỗi model |
| `scripts/check_vllm_endpoint_v1.py` | Kiểm danh tính và một lượt sinh |
| `scripts/run_smoke_api_v1.py` | 20 task A0 smoke, checkpoint theo task; lỗi hạ tầng sẽ chạy lại khi resume |
| `scripts/launch_vllm_serve_v1.py` | Chuẩn bị notebook và nhận endpoint đã mã hóa (`prepare`/`discover`) |
| `scripts/run_adversarial_dev_api_v1.py` | A0–A6 Dev; ping guard giữa các lượt không cần guard |
| `scripts/retry_on_infra_v1.sh` | Chạy lại runner khi nó trả rc=2 |

## Việc 1: xin quyền (làm một lần)

**HuggingFace** (cần cho Llama 3.1, Prompt Guard 2 và Gemma 4):

1. Đăng nhập [huggingface.co](https://huggingface.co).
2. Mở từng trang, đọc license, điền form và bấm đồng ý:
   - [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
   - [meta-llama/Llama-Prompt-Guard-2-86M](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M)
   - [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it): nếu trang có nút "Acknowledge license" thì bấm.
   Form của Meta yêu cầu tên thật, ngày sinh, quốc gia, tổ chức (ghi tên trường) và
   thường được duyệt trong vài phút đến vài giờ. Trạng thái xem tại Settings → Gated
   repositories.
3. Settings → Access Tokens → Create new token, chọn loại **Read**. Copy token, không
   dán vào chat hay vào repo.
4. Kaggle → mở notebook → Add-ons → Secrets → thêm `HF_TOKEN` bằng token trên và bật
   cho notebook.

**Kaggle:**

1. Settings → Phone verification (bắt buộc để dùng GPU và Internet).
2. Xem hạn mức GPU còn lại mỗi tuần ở trang notebook (góc phải, mục "GPU quota"),
   rồi ghi lại vào [sổ Kaggle](kaggle_resources.md).
3. Thêm secret `VLLM_API_KEY`. Tạo giá trị ở local bằng `python3 -c "import secrets;print(secrets.token_urlsafe(40))"`.
   Lưu giá trị này ở local trong biến môi trường, không commit.

## Việc 2: chạy thử Qwen3-8B (không cần quyền gated)

1. Kaggle → Create → Import notebook → chọn file `vllm_serve_v1.ipynb`. Accelerator chọn
   **GPU T4 x2**, Internet **On**, gắn 2 secret ở trên.
2. Giữ `MODEL_KEY = "qwen3_8b"` rồi chọn Run All. Khởi động mất khoảng 10–20 phút, gồm
   cài vLLM và tải khoảng 16 GB.
3. Lần đầu notebook in ra SHA revision và version vLLM. Ghi SHA vào `REVISION` trong
   notebook và vào `configs/models/backbones_v2.yaml`, ghi version vào `VLLM_VERSION`,
   rồi commit.
4. Ở local:

```bash
export VLLM_BASE_URL=https://<xxx>.trycloudflare.com/v1
export VLLM_API_KEY=<key>
.venv/bin/python scripts/check_vllm_endpoint_v1.py --model-key qwen3_8b
.venv/bin/python scripts/run_smoke_api_v1.py --model-key qwen3_8b
```

5. Nếu mạng hoặc tunnel bị rớt: chạy lại đúng lệnh trên, script chỉ chạy các task còn
   thiếu. Nếu restart notebook thì URL đổi, phải export lại `VLLM_BASE_URL`.
6. Xong việc: bấm **Stop session** trên Kaggle. Notebook cũng tự tắt server sau 30 phút
   không có request, nhưng phiên GPU vẫn bị tính quota tới khi bạn Stop.

## Cách nhanh: push qua API (đã dùng 2026-10-25)

Không cần Secrets với model không gated. Notebook tự sinh API key, rồi gửi URL và key
đã mã hóa RSA qua ntfy. Khóa riêng nằm trong `build/kaggle/...` (Git ignored, 0600).

```bash
F=$(.venv/bin/python scripts/launch_vllm_serve_v1.py prepare --owner lamhuy8904 --model-key qwen3_8b)
KAGGLE_CONFIG_DIR=<thư mục chứa kaggle.json> .venv/bin/kaggle kernels push -p "$F" --accelerator NvidiaTeslaT4
.venv/bin/python scripts/launch_vllm_serve_v1.py discover --folder "$F"   # chờ READY, ghi $F/endpoint.env
source "$F/endpoint.env"; export SSL_CERT_FILE=$(.venv/bin/python -c "import certifi;print(certifi.where())")
```

Clean Dev: `.venv/bin/python scripts/run_clean_dev_api_v1.py --model-key qwen3_8b`, rồi
`scripts/evaluate_clean_rebuild_v1.py results/rebuild_a/clean_dev_qwen3_8b --full-dev --numfix --output ...`.

Python của macOS thiếu CA, nên cần `SSL_CERT_FILE` như trên. Model gated vẫn cần gắn
secret `HF_TOKEN` cho notebook một lần qua UI của tài khoản đó.

Mặc định của runner: prompt `v3` (`prompts/a0_rebuild.py`) và schema giải mã
`per_tool_v1`. Chấm clean Dev luôn thêm `--numfix` (evaluator `clean_v1_1_typed_v1+numfix1`).

## Việc 3: Llama, rồi Gemma

- Llama 3.1 8B: **xong 2026-10-26.** `launch_vllm_serve_v1.py prepare --owner <acc>
  --model-key llama31_8b --hf-token-env HF_TOKEN`, rồi `kaggle kernels push`, rồi `discover`.
- Gemma 4 12B là **rủi ro cao nhất**: vLLM chỉ hỗ trợ ở bản nightly, nhà phát hành khuyến
  nghị GPU 40 GB, Gemma có thể lỗi ở fp16 trên T4. Nếu không khởi động được: thử
  `ENFORCE_EAGER = True`, sau đó thử checkpoint QAT w4a16. Nếu vẫn không được thì ghi
  việc đổi backbone vào decision log trước khi chọn model khác.

## Giới hạn

- Chưa chạy thật: chưa biết vLLM trên T4 có chạy ổn với từng model hay không, và chưa
  biết tốc độ.
- URL trycloudflare là URL tạm. Ai có cả URL và key thì gọi được model, vì vậy giữ key
  bí mật.
- Kết quả smoke mới không trộn với số liệu Phase 1–5 cũ.
