# Phase 5 — sửa lỗi audit và runtime v7

Cập nhật: 2026-09-13. Repair CPU đã xác nhận; chưa nghiệm thu toàn bộ Phase 5.

## Đã triển khai

- Entitlement v2 giữ cặp nguồn/loại dữ liệu theo từng clause, phân biệt namespace
  tài liệu/cache/bảng; kiểm object host bằng canonical extraction, không chỉ hash.
- Quét residual sau khi che mọi raw span, kể cả span được cấp quyền, để chặn
  bản zero-width đi kèm bản nguyên văn.
- Scope v2 giữ cặp bảng/cột; runtime v7 ghép ở A4–A6 trước Broker, ghi trace
  riêng theo task. Metadata A0–A5 không còn tự nhận policy final A6.
- Thử SQL trên bản ghi database smoke thật phát hiện ID `SV_SYN_001` bị v1 bỏ
  qua. Origin v2 nhận dạng ID synthetic có giới hạn và fail closed khi typed
  field ngoài profile; không sửa dataset hay thay test để né lỗi.

## Bằng chứng và giới hạn

91 focused tests pass (27,06 giây); full QA 2.444 pass/1 native-tqdm skip
(460,00 giây). Setup/Ruff/mypy 314 files/knowledge đạt. Có 69 runtime records
(28 v5 comparison/41 v7), 28 exact Replay parity pairs, 41 v7 Broker calls.
436 source + 573 raw hashes được audit độc lập và khớp; 169 tracked data hashes
không đổi. [Receipt](../experiments/manifests/phase5_remediation_v2_cpu01.json)
SHA `a027c9f69c682d35b157e108e08a0dfa2ad1ec4d8a7245bac8e01028ba6b2332`.
Đây là working-tree CPU QA, không phải clean release/model benchmark.
Các lượt phát triển lỗi được dùng sửa code synthetic, không phải retry model
để cải thiện điểm. Không có model/Kaggle/benchmark Dev/Test run mới.

Receipt cũ `phase5_final_entitlements_v1_validation01.json` có `pytest.log`
không khớp: expected `b999c7cf671fbb629b790dbb95250a29c53f0186778740373d2d3a8ebee2f453`,
actual `c5e01aea3738dac7f8685dbfddf500a09113123b49db3e3af48ceb0547d40dfc`.
Giữ nguyên receipt/log, không đổi hash để hợp thức hóa. Hash đúng của runtime v6
không xóa được lỗi hành vi của nó. Không dùng v1/v6 làm bản mới cho thí nghiệm.

## Bước tiếp theo

Tiếp [ModelPair/runtime integration](phase5_modelpair_runtime_next.md), sau đó
guard quality/grouped Dev, broader coverage và freeze với bằng chứng riêng.
Raw output/log/JUnit được giữ tại `results/phase5_remediation_v2_cpu01/`;
không chạy lại hoặc ghi thêm vào identity đã hoàn tất.

[Contract](../docs/architecture/phase5_remediation_v2_contract.md) ·
[Báo cáo](../docs/evaluation/phase5_remediation_v2_report.md).
