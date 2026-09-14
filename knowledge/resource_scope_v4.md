# Host-bound resource scope v4 — hiện hành

2026-09-14. Nối tiếp [guard diagnostics](guard_diagnostics_v1.md).
[Contract](../docs/architecture/phase5_resource_scope_v4_contract.md).

## Đã triển khai và chốt CPU

- `ResourceBindings` lấy đúng AWB/AUX ID, tool, arguments và source type từ host
  catalog; reject ambiguous cross-type IDs, extras và vượt budget. Inventory
  không phải quyền đọc. Scope v4 chỉ cho extended ID khi có raw-user read anchor.
- Cho phép cụm `cho biết` trong affirmative read clause; không bỏ chặn `không`,
  `chớ`, điều kiện hoặc quoted text. Không dùng tool text làm authorization.
- Catalog Dev giữ overlay T0→TRUSTED, T1/T2→UNTRUSTED và sensitivity độc lập.
  Auxiliary docs/pages chỉ biết identity/type, mặc định S2/UNTRUSTED; không lấy
  nhãn từ nội dung, referring source hoặc oracle. Metadata giống matched pairs.
- Runtime v9 và pair adapter riêng ghép cùng task-local scope/index. V3/v8 và
  tất cả kết quả native/CPU cũ nguyên vẹn; A0–A3 không enforce scope v4.
- Chỉ đọc hai Dev files theo hash pin và public seal. Lịch chọn 8pairs/16cases
  không đổi; không dùng held-out payload/private oracle/GT hay model output.

Source `d9f11df`. Frozen-source 75 focused tests đạt 25,18s: 37 unit mới,
20 actual-spawn integration, 18 legacy scope regression; no-network controls.
Full **2.945pass/1 optional native-tqdm skip/865,40s**; setup/Ruff/mypy371/
knowledge đạt. 524source/295raw/169data hashes kiểm lại khớp. 20 completed runtime,
21 successful tool results, 37 synthetic guard sidecars; scope PRE 11ALLOW/3DENY.
Đây là CPU plumbing evidence, không phải model utility hay guard quality.
[Receipt](../experiments/manifests/phase5_resource_scope_v4_cpu01.json) SHA-256
`6735b6205bf6a094cc2fe79cadfd9c522f850870e7d6ada75ebe2a37aa2904d0`.
[Báo cáo](../docs/evaluation/phase5_resource_scope_v4_report.md).

## Bước tiếp theo và giới hạn

Full QA và receipt đã chốt, không còn QA chạy. Output
`results/phase5_resource_scope_v4_cpu01` đã đóng; không ghi thêm/chạy lại.
Tiếp theo bounded SQL row scope và runner/input identity/exact package; vẫn
`dispatch_allowed=false`. Scope parser đánh giá được 8/16 document/page trigger
đã chọn, 8 SQL trigger còn unassessed. Đây không phải utility hay success rate.

Auxiliary public facts giữ S2/UNTRUSTED nên legitimate final/sink utility có thể
bị chặn; cần đánh giá và host labeling evidence riêng, không tự hạ nhãn để pass.
Search/SQL row filters và broad Vietnamese semantics chưa được giải quyết ở mốc
này. Không có GPU/model nặng chạy local, chưa submit Kaggle mới, không cần account
mới. Gate Phase5 vẫn 4/7, chưa accepted và không mở Phase6/7/Test.
