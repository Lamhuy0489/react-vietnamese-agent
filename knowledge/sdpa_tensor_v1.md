# Phép thử attention không weights

2026-09-11: owner đã đồng ý tiếp tục phương án tối ưu attention sau OOM v2.
[Contract](../docs/architecture/phase5_sdpa_tensor_v1_contract.md).
Chỉ làm Phase5; không Test hoặc local model. Hai GPU runs v1/v2 cũ giữ nguyên.

Đang triển khai tensor runner/independent auditor,28-file wrapper và exact
preflight. Mỗi role có short prefill/decode parity, long4096 baseline/candidate
và boundary decode;10fresh native processes, cap2GiB dành riêng tensor.
Chưa có native kết quả, chưa thay model attention, chưa submit kernel mới.
Tiếp focused/full QA, commit source, exact preflight, push, kiểm quota/private
Dataset rồi một submission `huylmhuhu/react-vn-sdpa-tensor-v1`.

Thành công tensor không thay thế full4096+512/128 model stress hoặc Phase5
acceptance; cần runtime integration/A4/general final/grouped Dev/freeze sau đó.
