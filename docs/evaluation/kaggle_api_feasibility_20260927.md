# Đánh giá thực nghiệm qua API Kaggle

Ngày 2026-09-27. Owner báo đã tự dựng bốn GPU API và yêu cầu đọc/đánh giá,
chưa yêu cầu triển khai adapter hoặc chạy thực nghiệm. Đây là static review
local + tài liệu publisher, không phải live/terminal audit. Không gọi endpoint,
không đọc credential/state JSON, không submit/stop, không model inference/Test.
Phase 5 chưa accepted; không thay research contract hoặc chọn model chính thức.

## Kết luận và ranh giới

Khả thi và giảm rõ chi phí vòng lặp phát triển: runner, Broker, mock tools,
policy, checkpoint và evaluator ở local; Kaggle chỉ nhận inference request.
Sửa host code/prompt không cần upload lại notebook khi server contract giữ
nguyên. Đổi server/model/dependencies vẫn có thể cần restart hoặc phát hành
worker mới. API không làm model mạnh hơn hoặc tự giải provenance/false block.
Local cần giữ chạy và có mạng; phiên/tunnel gián đoạn phải được checkpoint.

`LLMBackend.generate` trong `src/react_agent/llm/base.py` là điểm nối sẵn có.
Chưa tìm thấy HTTP inference adapter trong `src/react_agent`/`scripts`.
Bridge `prototypes/field_model_bridge_v1.py` nhận backend này nhưng chỉ one-shot
Plan selection, mặc định veto deny, chưa full ReAct/A6. Native pair/lifecycle
runners đang gắn subprocess/HF; không chỉ đổi URL là giữ nguyên toàn bộ behavior.
Guard `llm/constrained_guard_v1.py` dùng prefix-constrained token decoding;
server chat hiện tại không có khả năng tương đương. JSON prompt không thay
thế được constrained decoding. Giữ guard cũ hoặc thêm server capability và
validation riêng; không âm thầm thay guard khi so A2–A6.

## Bằng chứng mã nguồn local

Hai file review nằm trong build, không coi Git HEAD là source freeze của chúng:

- `build/kaggle/launch_multi_model_gpu_apis.py`: SHA-256
  `ae6b50db002a983457373ac16ec51443701f1898c969233d4ea3ca0f8e3b73ae`.
- `build/kaggle/tpu_speed_test_ui.py`: SHA-256
  `6079424938606a0403922bfb4ae9d96a59b7a7a9a01ef3fb30e9d32b7b015075`.
- Git base `c87c321b42345e6d7152ca60976363a67a972531`; working tree có thay đổi
  từ trước, không sửa/commit/push các thay đổi đó.

Các điểm ảnh hưởng trực tiếp kết quả:

1. Worker đặt ready sau load/eval, chưa generation warmup. UI dòng 519–520
   có thể dùng ntfy ready cũ khi health probe lỗi và vẫn ghi READY (LIVE).
2. `find_model_dir` fallback về candidate đầu nếu không khớp preferred string;
   Qwen target mount cả Qwen3 và Qwen2.5. Alias không xác thực weight revision.
3. Handler chỉ đọc messages/max_tokens/temperature/stream; không kiểm request
   model, không thực thi seed, response_format/tools/stop hoặc grammar yêu cầu.
   top_p bị cố định 0.9 khi sampling; thư viện cài với pip -U, chưa pin.
4. Chat-template lỗi fallback sang role-text nối dòng: cần ghi lỗi, không
   âm thầm thay input giữa các model trong phép so sánh đã khóa.
5. Token usage tính bằng encode lại text/chunks; finish_reason luôn stop,
   kể cả chưa phân biệt hết token budget. Không dùng UI tok/s làm số liệu
   benchmark chính thức trước khi đo bằng token IDs và timing phù hợp.
6. Một GEN_LOCK mỗi server: requests cùng endpoint tuần tự. Bốn endpoint
   không đồng nghĩa một model xử lý bốn task song song.
7. Không có request-ID/idempotency/cancel contract; lỗi thread generate và
   client timeout chưa được nối thành kết quả có kiểm soát. Timeout không
   chứng minh GPU đã dừng. Retry phải tách infrastructure khỏi semantic failure.
8. `enable_thinking=False` không được coi là universal switch cho mọi tokenizer.
   Không yêu cầu/lưu reasoning; cần kiểm model-specific output contract.

## Publisher evidence đọc ngày 2026-09-27

| Nguồn chính thức | Thông tin dùng trong đánh giá | Giới hạn |
|---|---|---|
| [Qwen/Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) | 8.2B total; có hard switch non-thinking | Chưa xác thực weights ở endpoint |
| [Google Gemma 4 E4B IT](https://huggingface.co/google/gemma-4-E4B-it) | 4.5B effective, 8B including embeddings | Không gọi tương đương dense 8B compute |
| [Meta Llama 3.2 3B Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) | Model nhóm 3B | Không đáp ứng yêu cầu từ 8B |
| [DeepSeek R1 Distill Llama 8B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B) | Distill từ Llama3.1-8B; hướng dẫn nhiệt độ 0.5–0.7 và tránh system prompt | Không suy JSON/tool-agent quality từ reasoning benchmarks |
| [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/) | Không bảo đảm uptime/SLA; không hỗ trợ SSE | UI đang stream=True; đề xuất stream=False cho pilot, vẫn đo timeout |

Nếu owner muốn nhóm xấp xỉ/từ 8B total, Qwen/Gemma/DeepSeek là ba ứng viên
để kiểm Dev; Llama3B chỉ đối chứng nhỏ nếu được chọn. Nếu yêu cầu strictly >8B,
danh sách này không phải bốn model đạt ngưỡng. Không tự thay sang model nặng.
Qwen non-thinking là đề xuất cho integration đầu, chưa là kết quả chọn backbone.
DeepSeek cần kiểm output contract riêng; không áp đặt publisher reasoning prompt
trái invariant. Generation profiles phải predeclare và freeze, không gọi
cấu hình hiện tại là publisher-optimal cho mọi model.

## Bước tiếp đề xuất, chưa triển khai

1. Read-only health/model metadata, rồi smoke synthetic ngắn có ngân sách:
   messages nhiều vai, strict JSON, tiếng Việt, stop/length và context thực tế.
   Đo generation thành công, không chỉ GET models. Không lưu reasoning.
2. HTTP adapter nhỏ tuân LLMBackend, stream=False, session/model identity,
   timeouts/error classification, request hash và checkpoint. Giữ mock tools
   offline qua Broker, private oracle không vào request. Source host vẫn freeze
   cho phép đo chính thức; không cần đóng gói host sang Kaggle mỗi vòng Dev.
3. Cùng clean Dev pilot cho ba ứng viên sau khi xác nhận tiêu chí kích thước;
   đo success, valid actions/JSON, tokens, p50/p95, timeout và truncation.
   Ước lượng giờ chạy từ số model calls/task và latency đã đo; chưa có số tốc độ
   end-to-end đáng tin để cam kết thời gian hoặc mức tăng tốc.
4. Chọn/freeze một agent trên Dev; giữ agent và guard cố định khi so A0–A6.
   Không chạy ma trận bốn model × bảy mức mặc định. RQ1 vẫn ba backbones;
   RQ2 một backbone. Representation mới cần matched comparison riêng; A0
   không được thừa hưởng defense của prototype. Test tiếp tục sealed.

Mô hình server sống lâu có thể giảm bài toán nạp/dọn cặp GPU ở mỗi task, nhưng
không biến bằng chứng lifecycle cũ thành pass. Nếu đổi execution architecture
cho nghiên cứu chính, cần quyết định có rationale/impact và tiêu chí mới; chưa
được tự động chốt trong lượt tư vấn này.

## Kiểm tra local cho lượt review

Setup/Ruff/mypy (555 files) đạt. Knowledge validator phát hiện đổi tên heading
`Đang làm` trong handoff; đã giữ lại heading bắt buộc và knowledge-check đạt.
Unit bridge/knowledge chạy lại đạt 39/39. Không full pytest do Test sealed và lượt này
không thay runtime. Không dùng CPU tests để chứng minh remote API hoạt động.
