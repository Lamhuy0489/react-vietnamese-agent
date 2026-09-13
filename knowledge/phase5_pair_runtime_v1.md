# ModelPair / runtime v7 — CPU integration

Cập nhật: 2026-09-13. CPU02 đạt bounded CPU QA; chưa có native GPU evidence mới.

Đính chính: external audit trace phát hiện `warm attempt identity
mismatch`: pair READY chiếm sequence 1, nhưng trace vẫn gắn schema warm cũ.
CPU01 là lượt phát triển, không chọn làm acceptance receipt dù full QA đạt
2.492 pass/1 skip trong 588,87 giây. Snapshot code `819af7a`; raw/receipt giữ nguyên.
Đã thêm schema pair, auditor nối runtime guard attempts với worker snapshot và
host proposal ledger. Lượt bị pair đóng từ chối trước dispatch không đếm thành
worker inference. Bốn corruption tests kiểm schema/request/readiness/host count.

`run_pair_task` ghép pair đã tồn tại với runtime v7 qua role adapters ở parent.
A0/A1 tạo một agent worker; A2–A6 dùng hai worker sibling. Guard không spawn
pair hoặc worker thứ ba. READY nằm trong receipt ngoài, không đếm như generation.
Error/timeout/invalid guard JSON retire pair, các đường thoát ghi cleanup receipt.

52 integration tests pass, gồm exact observable/context parity với
v7 ở 7 levels, actual DB entitlement, A4 scope và guard external veto. Bộ test
đầy đủ thêm 28 level/terminal cases, startup/timeout/cancel/invalid-output và
assert PID không còn active cùng các worker handle đã đóng.

Full QA: **2.496 pass/1 native-tqdm skip**, 477,43 giây; 52 focused pass/58,03s.
Setup/Ruff/mypy 317 files/knowledge đạt. 51 joined receipts hợp lệ, 441 source/
530 raw hashes khớp và 169 tracked data hashes không đổi qua audit độc lập.
80 GRACEFUL/11 TERMINATE CPU exits; không có unclosed worker handles.
Output `results/phase5_pair_runtime_v1_cpu02` và
[receipt](../experiments/manifests/phase5_pair_runtime_v1_cpu02.json), SHA-256
`1bc819d51f47e90f2fb35ad904087626cbb958ea8665b250a848ec335009312e`.
Working-tree QA anchored parent `819af7a`, không gọi clean-source release.
Job đã kết thúc; giữ nguyên output identity và source bytes được receipt chọn.

Giới hạn: native Kaggle package/runtime chưa chạy; single-agent deadline hiện
áp dụng cả startup/calls. Runtime elapsed có inner cleanup, outer cleanup
không được gọi là tổng cleanup. Guard production/grouped Dev, broader semantic
coverage và freeze chưa đóng.
Trước native acceptance cần bổ sung post-response sibling-failure audit và
explicit failed-startup timing; chi tiết trong [native follow-up](phase5_pair_runtime_kaggle_next.md).

[Contract](../docs/architecture/phase5_pair_runtime_contract.md) ·
[Handoff](handoff.md).
