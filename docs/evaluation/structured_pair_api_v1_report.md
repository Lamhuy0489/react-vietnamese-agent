# Qwen agent / Llama guard API — triển khai và smoke ngày 2026-09-27

Hai notebook mới đã READY và hoàn thành một bài synthetic ghép cặp trên GPU.
Qwen gọi calculator qua Tool Broker rồi trả final đúng schema; Llama kiểm tra
cả action và final. Đây là bằng chứng kết nối/định dạng, chưa phải chất lượng
guard, A0–A6 benchmark hoặc nghiệm thu Phase 5. Test vẫn khóa.

## Hai notebook đang dùng

| Vai trò | Notebook thực tế | Version / ID | Model mount |
|---|---|---|---|
| Task agent | [buiquocviet/react-vn-qwen3-agent-api-v1](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1) | 1 / 136136611 | qwen-lm/qwen-3/Transformers/8b/1 |
| Guard | [huylmhuhu/react-vn-llama3-guard-api-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1) | 1 / 136136616 | metaresearch/llama-3.2/Transformers/3b-instruct/1 |

Mỗi notebook private, FP16, 2×Tesla T4; không Dataset và không benchmark input
được upload. Owner xác nhận đã tắt bốn phiên cũ trước hai submission này.
Hai notebook mới mỗi cái chỉ push một lần, giữ chạy để owner thực nghiệm.
Quyền GitHub không tự cấp quyền xem notebook private. READY là trạng thái
đã kiểm tại phiên này, không cam kết uptime của tunnel hoặc phiên Kaggle.

Source freeze [728821e](https://github.com/Lamhuy0489/react-vietnamese-agent/commit/728821ea761b3994eb40ebba91ab8238e4667f82)
gồm serving/client/launcher/preflight/smoke/tests/contract, đã push trước GPU.
Remote source tải lại khớp byte với scripts đã nộp. Version1 có receipt push;
pull bằng suffix `/1` không trả source, lỗi giữ ở `remote_source_audit.json`.
Pull latest sau đó khớp trong `remote_source_audit02.json`; không coi lần pull
latest là xác thực version độc lập. Source, session và worker hash được đối
chiếu lại qua API trước inference.

## Đã tinh chỉnh những gì

Không fine-tune trọng số. [Contract](../architecture/structured_pair_api_v1.md)
quy định constrained decoding bằng JSON schema, kiểm JSON độc lập trước trả
về và kiểm tiếp ở host. Agent xuất `action` hoặc `final_answer.answer` kiểu
chuỗi; guard xuất `risk`, `labels`, `confidence`. Qwen tắt thinking, không lưu
reasoning. Greedy/temperature0, seed42; context tối đa4096, server cho agent
tối đa1024 output tokens, guard128. Smoke dùng agent512/guard128.

Model mount, dependency versions, source hash và file fingerprint được pin/ghi
lại; actual Torch2.10.0+cu128, Transformers4.57.6. Model hash xác định bytes
worker đã đọc, chưa có publisher attestation. GPU tensor check và warmup sinh
JSON có ràng buộc hoàn tất trước READY. Metadata đầy đủ và Docker digest nằm
trong [receipt chọn lưu](../../experiments/manifests/structured_pair_api_v1.json).

## Kết quả thực tế

Task synthetic mới: `Dùng calculator tính 23*7+5. Sau khi nhận kết quả, trả lời chỉ bằng số.`

| Lượt | Kết quả hợp lệ | Thời gian decode phía server |
|---|---|---|
| Agent1 | calculator, expression `23*7+5` | 2,220s |
| Guard1 | SAFE, labels rỗng, confidence LOW | 1,129s |
| Broker | calculator trả value166 | Local |
| Agent2 | `{"final_answer":{"answer":"166"}}` | 1,650s |
| Guard2 | SAFE, labels rỗng, confidence LOW | 1,084s |

`completed`, `diagnostic_pass=true`; 2 agent attempts + 2 guard attempts,
không retry. Tổng decode khoảng6,083s, không phải latency end-to-end hay
benchmark tốc độ. Ba Broker events đúng thứ tự proposed→executed→result;
file JSONL khớp result. Hai guard verdict LOW được giữ nguyên, không suy
thành bảo đảm an toàn. Gate SAFE-only ở smoke không phải policy A2/A6.

Raw mới: `build/evaluation/structured_pair_smoke01/` (declaration trước gọi
model, result, Broker JSONL). Declaration ghi319 host source hashes, task,
generation và metadata từng model; source hashes còn khớp sau chạy. Giữ
nguyên smoke HTTP cũ và các lỗi semantic trước đây, không thay kết quả cũ.

## Kiểm tra và giới hạn

- 77 focused tests pass: structured API/client, HTTP diagnostic, tám tools,
  runtime và memory; setup/Ruff pass, mypy563files pass. Không chạy toàn bộ
  pytest trong scope hẹp này để không mở rộng sang dữ liệu Test đã khóa.
- Exact generated worker qua4 layouts (agent/guard × archive/expanded), không
  import project từ host;5 token-level controls với Qwen tokenizer thật pass.
  CPU Mac Intel dùng Torch2.2.2, không giả lập tương đương GPU2.10.0; native
  warmup và paired smoke mới là bằng chứng stack GPU hoạt động.
- Giữ hai preflight lỗi cũ (tar API Python3.11 và resolve symlink venv) cùng
  lần pull version không có source; không resubmit GPU để sửa các lỗi đó.
- Audit session/model/schema/seed, worker/source byte hashes và Broker join
  đạt; connection files và RSA private key mode0600. Không đưa endpoint,
  API key, discovery topic hoặc private key vào receipt/memory.
- Tunnel tạm thời; sustained availability và graceful OS-exit chưa được audit.
  Timeout generation chỉ kiểm giữa các bước, không là hard CUDA cancellation.
  Raw vẫn local, chưa xác nhận backup ngoài máy.

## Cách dùng tiếp

Kết nối mới nằm ở `build/kaggle/structured_pair_release01/pair_endpoints.json`.
Đọc file này để lấy từng role, endpoint, alias và key; không dùng cấu hình bốn
server cũ. File có thông tin bí mật, không commit hoặc dán vào chat.
Host adapter `src/react_agent/llm/structured_http_v1.py` đã kiểm identity và
schema; notebook chỉ inference, mọi tool vẫn do host Broker thực thi.

Nếu cần refresh discovery trong chính phiên hiện tại:

```bash
build/structured_api_venv/bin/python scripts/launch_structured_pair_v1.py discover \
  --directory build/kaggle/structured_pair_release01
```

Không push lại release01. Khi muốn dừng, Cancel Run tại đúng hai notebook mới.
Launcher bốn server cũ không quản lý hai notebook này. Lần khởi động mới cần
session/package riêng và kiểm lại identity; không nối kết quả hai session
như cùng một run. UI8765 cũ chưa được chuyển sang profile hai server này.

Bước nghiên cứu tiếp: khai báo profile Dev nhỏ trước inference để đo riêng
clean utility và guard benign/attack, sau đó nối vào flow của candidate đã
chốt. Format constraint phải áp dụng đồng nhất cho agent ở các mức A0–A6;
không tính nó thành phòng vệ bổ sung của A0. Chưa thay baseline chính thức,
chưa chạy benchmark lớn và không tự kết luận guard3B đủ tốt từ bài tính này.
