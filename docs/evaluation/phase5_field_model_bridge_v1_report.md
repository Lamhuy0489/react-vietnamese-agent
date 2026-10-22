# Model-plan bridge và lựa chọn batch Kaggle

2026-09-25. Scope: Phase 5, prototype riêng được owner duyệt.

## Đã làm và chưa làm

[Bridge](../../src/react_agent/prototypes/field_model_bridge_v1.py) nhận bất kỳ
backend tuân `LLMBackend`: host đọc nguồn qua Broker, đưa raw observations và
references vào envelope, nhận đúng một Plan JSON rồi gọi host renderer. Model
không có trường tạo Grant, bỏ veto hoặc chèn literal final. Duplicate keys,
markdown, sai identity, vượt budget, lỗi backend/veto đều fail closed, không retry.
Lưu được Plan hợp schema/hash/request hash, số call, generation/total wall time;
không lưu free-form response lỗi hoặc reasoning. Hook veto mặc định deny.

[Contract](../architecture/phase5_field_model_bridge_v1_contract.md) đã ghi
trước implementation. **Đây là one-shot selection, chưa ReAct loop và chưa nối
A1/guard/PRE/POST thật.** HF callable adapter cũ đã được kiểm tra tương thích
bằng fake callable, không tải Transformers/model. Matching model/revision
strings không chứng minh bytes của model trên máy chạy. Grant đúng còn là giả
định host, implicit/control-flow leakage chưa giải quyết. Không thay runtime A6.

QA được lưu tại `build/evaluation/phase5_field_model_bridge_qa01.xml`, chi tiết
hash/count ở [selected receipt](../../experiments/manifests/phase5_field_model_bridge_v1.json).
**193 tests đạt**, gồm 33 bridge tests; setup/Ruff/mypy555/diff đạt. Full pytest
không chạy vì Test sealed; 191 historical worker source files không đổi.
Tests dùng fake backend, Broker thật, dữ liệu synthetic có sẵn; không đọc Test,
không gọi model/GPU. Kiểm envelope chứa instruction ở raw document không tạo
system message mới; KHÔNG chứng minh LLM chống injection. Có test public,
concat/Base64, private/encoded/mixed, forged hash/grant/path, quyền giả, không
có host permission, timeout, identity, config/request budget và JSON nghiêm ngặt.

Không có native result hoặc notebook mới trong đợt này. Không tăng Phase 5
4/7, không commit/push. Old component matrix và worker source không sửa.

## Đánh giá notebook người dùng gửi (đọc nguồn 2026-09-25)

| Nhận định | Bằng chứng và giới hạn |
|---|---|
| Qwen3.8-27B là model chính thức | [Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B) mô tả model 27B và context native 262,144; chưa tải/pin weights |
| Thinking mặc định bật | Model card hướng dẫn `chat_template_kwargs.enable_thinking=false`; dự án không yêu cầu/lưu hidden reasoning |
| 130 tok/s và throughput nhiều stream | Số tác giả [kaggle-tpu-lab](https://github.com/ARahim3/kaggle-tpu-lab) báo cáo, không phải đo tại tài khoản/đồ án này |
| Tunnel dùng phát triển | [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/) không bảo đảm SLA/uptime và ghi không hỗ trợ SSE; không mặc nhiên coi streaming từ laptop tương đương localhost |
| Rủi ro trong script được dán | READY/curl log chứa API key; `publish(ready)` gửi cả key qua ntfy nếu topic bật. Script có binary latest, patch base64 và weights fallback không pin revision/hash |

Đánh giá cuối là đọc script, không kết luận mã độc. Không chạy patch/binary,
không mở tunnel hoặc gửi thông tin tới ntfy. Không xác nhận quota TPU, quyền
Dataset, khả năng mount/cache hoặc losslessness của MTP trong tài khoản owner.
Con số 12/12 greedy của tác giả không đủ chứng nhận mọi request của đồ án.

## Quyết định và bước chạy tiếp

Owner trả lời **“Chưa có, dùng batch Kaggle”**. Chọn model và runner cùng ở
Kaggle, local chỉ phát hành source/payload và tải kết quả; không cần endpoint
công khai hay tài khoản cloud trả phí lúc này. Nếu dùng vLLM ở bước mở rộng,
batch gọi localhost, giữ key trong secret/env và loại key khỏi mọi output.
Không triển khai remote transport đang không cần thiết.

Trình tự hữu hạn, không đổi nhiều biến cùng lúc:

1. Batch smoke lựa chọn reference bằng model đã có immutable mount/pins của
   dự án trước; dùng cùng schema/source, chưa đổi sang Qwen3.8-27B mặc định.
   Chọn model mạnh hơn là run riêng sau khi có baseline, không trộn số đo.
2. Hoàn thiện entrypoint batch cho bridge với model identity/timeout/checkpoint,
   nhận đủ source/model/generation manifest trước inference. Exact-worker
   archive/expanded rehearsal + 8 tools/public Dummy, một source freeze/push
   theo khối sau QA rồi upload private; không dùng package04 cũ để chạy bridge.
3. Chạy một smoke synthetic mới, lưu mọi lỗi/invalid Plan, không semantic retry.
   Chỉ sau đó mới prospective có prior guard/veto thật và matched comparison.

**Hiện thiếu entrypoint/package/admission cho bridge mới**, không phải thiếu
API key hoặc owner approval. Không gọi code nhận `LLMBackend` là batch đã sẵn
sàng submit. Lượt GPU chưa khởi động; không có job để chờ. Theo skill
experiment-repro, không bỏ qua exact-worker QA/source freeze để khởi động sớm.

Khi đo native: tách load/compile/warmup, generation, tổng task, token counts,
invalid/timeout rates, model/tokenizer revision, precision, backend/dependencies,
seed, context/output budget và concurrency. Wall time CPU hiện tại không phải
decode tok/s/TTFT. Với thử nghiệm TPU tương lai, MTP off là đối chứng đầu tiên;
đổi MTP/precision/context cần run identity và kiểm chứng riêng, không sửa số cũ.
