# Runbook chạy lại (mức A): vLLM trên Kaggle, gọi API từ local

Cập nhật: 2026-10-25. Đã chạy thật Qwen3-8B (xem [sổ Kaggle](kaggle_resources.md)); Llama và Gemma chưa chạy. Xem [lộ trình v2](../docs/project/roadmap_v2_rebuild.md), mục 2b.

## Thành phần

| File | Vai trò |
|---|---|
| `notebooks/kaggle/vllm_serve_v1/vllm_serve_v1.ipynb` | Serve một model bằng vLLM qua API kiểu OpenAI, mở tunnel cloudflared, tự tắt khi không có request |
| `configs/models/backbones_v2.yaml` | Repo và revision đã pin của 3 model và 2 guard ứng viên |
| `src/react_agent/llm/openai_compat_v1.py` | Backend local: ép JSON theo schema, seed 42, request_id, kiểm danh tính model, tách lỗi hạ tầng khỏi lỗi model |
| `scripts/check_vllm_endpoint_v1.py` | Kiểm danh tính và một lượt sinh |
| `scripts/run_smoke_api_v1.py` | 20 task A0 smoke, checkpoint theo task; lỗi hạ tầng sẽ chạy lại khi resume |

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
`scripts/evaluate_clean_v11_dev.py results/rebuild_a/clean_dev_qwen3_8b --full-dev --output ...`.

Python của macOS thiếu CA, nên cần `SSL_CERT_FILE` như trên. Model gated vẫn cần gắn
secret `HF_TOKEN` cho notebook một lần qua UI của tài khoản đó.

## Việc 3: Llama, rồi Gemma

- Llama 3.1 8B: đổi `MODEL_KEY = "llama31_8b"` sau khi được duyệt quyền.
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
