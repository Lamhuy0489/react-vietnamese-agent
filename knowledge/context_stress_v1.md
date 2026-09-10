# Context stress v1 — backend/runner CPU đã kiểm chứng

Cập nhật2026-09-10. [Contract](../docs/architecture/phase5_context_stress_v1_contract.md).
Ba file mới: native backend/factory, durable paired runner và CLI stub/HF entry.
Giữ nguyên nguồn/model/caps/deadline cũ; chưa wrapper/preflight/GPU submission.

Backend chỉ một call diagnostic, fixed4096input và512/128output; không decode
hoặc lưu generated text/IDs. Kiểm toàn bộ KV layers sau generation, rồi forward
riêng token cuối và kiểm full boundary. Ghi stage/PID, count/hash, cache metadata,
generation/final-forward time và process allocator peaks. Không gọi global free
endpoints là global peak; chưa đo prefill riêng. Lỗi lưu class-only và retire.

42 tests mới đã đạt (native fakes và real spawn synthetic transport). Source
`d07e914` đã tái lập hai CLI stub runs: summaries khớp, 4 PID khác nhau/reaped,
15 raw files mỗi lượt, không native calls. [Receipt](../experiments/manifests/phase5_context_stress_v1_validation01.json).
Chưa native model/cache execution; fake cache không chứng minh allocation GPU.

Full QA lần01 có 1 lỗi/1.593 pass/1skip trong349,88s: IPC test nhận5REGISTER
nhưng35UNREGISTER sau gc.collect;30unmatched do các object/finalizer từ test
trước còn giữ lại. Giữ XML `results/phase5_context_stress_v1_release01_pytest.xml`
và trace `build/pytest_context_stress_v1_release01/test_real_event_registration_a0/trace.jsonl`.
Thêm teardown cho **nhóm test mới**: undo monkeypatch rồi gc.collect, sau khi
runner đã reap workers. Không sửa tracer/frozen runtime hoặc manual unregister.
Nhóm new probe + IPC test chạy liền đạt46/46; full QA02 đã hoàn tất:
1.594 pass/1 optional native skip trong344,79s (JUnit344,696s).
Setup/Ruff/mypy250files/knowledge đạt. [Release QA](../experiments/manifests/phase5_context_stress_v1_release_qa01.json)
giữ hash cả lượt lỗi và lượt đạt; không giấu lỗi test isolation ban đầu.
146 frozen source entries, 296 raw GPU hashes và 17 current overlay hashes
không thay đổi. Không job local/Kaggle còn chạy; chưa native stress GPU.

Tiếp: independent stress artifact auditor + exact GPU wrapper/preflight/launch
contract, currentquota/mount, source/receipt push rồi một identity mới. Không
đổi benchmark decoding hay kéo weights về local. Các gate runtime/A4/final/
grouped Dev/freeze còn mở. Không jobGPU mới, không Test/privateGT payload.
