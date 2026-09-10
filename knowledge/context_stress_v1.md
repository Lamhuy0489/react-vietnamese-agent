# Context stress v1 — backend/runner CPU đang chốt

Cập nhật2026-09-10. [Contract](../docs/architecture/phase5_context_stress_v1_contract.md).
Ba file mới: native backend/factory, durable paired runner và CLI stub/HF entry.
Giữ nguyên nguồn/model/caps/deadline cũ; chưa wrapper/preflight/GPU submission.

Backend chỉ một call diagnostic, fixed4096input và512/128output; không decode
hoặc lưu generated text/IDs. Kiểm toàn bộ KV layers sau generation, rồi forward
riêng token cuối và kiểm full boundary. Ghi stage/PID, count/hash, cache metadata,
generation/final-forward time và process allocator peaks. Không gọi global free
endpoints là global peak; chưa đo prefill riêng. Lỗi lưu class-only và retire.

42 tests mới đã đạt (native fakes và real spawn synthetic transport). Cần full QA,
commit nguồn và hai CLI stub reproductions trước freeze receipt. Chưa native
model/cache execution; fake cache không chứng minh allocation GPU thực tế.

Tiếp: independent stress artifact auditor + exact GPU wrapper/preflight/launch
contract, currentquota/mount, source/receipt push rồi một identity mới. Không
đổi benchmark decoding hay kéo weights về local. Các gate runtime/A4/final/
grouped Dev/freeze còn mở. Không jobGPU mới, không Test/privateGT payload.
