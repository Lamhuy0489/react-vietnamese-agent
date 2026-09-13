# Bàn giao phiên làm việc

Cập nhật: 2026-09-13. Chỉ dẫn hiện hành; các mốc v1/v6 là lịch sử, không thay thế mục này.

## Đang làm

Owner yêu cầu sửa lỗi audit và hoàn thiện phần thiếu Phase 5, lưu thực nghiệm/tri thức.
Đã thêm runtime v7 và components v2: clause-bound final grants, residual screening,
table/column scope pairs, tích hợp A4–A6 trước Broker, metadata đúng level và
origin extraction cho synthetic student IDs. Không sửa code/receipt v1/v5/v6.

Đã xác nhận 91 focused tests và full QA 2.444 pass/1 native-tqdm skip (460 giây).
Setup/Ruff/mypy 314 files/knowledge đạt. Validator hoàn tất, không job còn chạy.
Output/receipt:
`results/phase5_remediation_v2_cpu01` và
`experiments/manifests/phase5_remediation_v2_cpu01.json`.
Không gọi đây là clean-source release vì worktree chứa thay đổi chưa commit.

## Bước tiếp theo

1. Giữ nguyên identity đã hoàn tất; không chạy trùng hoặc ghi thêm vào output.
2. Tiếp [ModelPair/runtime integration](phase5_modelpair_runtime_next.md): tránh
   chuyển pair sang process con qua WarmGuardFactory; cần host-side role adapters.
3. Sau integration CPU, tiếp runtime GPU, guard
   quality trên grouped Dev, kiểm broader coverage và freeze. Chưa mở Phase 6/7.

Pending access: CPU không cần tài khoản mới. Trước job GPU phải đọc Kaggle
skill/preflight, xác minh quota owner và private Dataset; không cycling credential.
Tác vụ model nặng chỉ chạy Kaggle, không chạy local.

## Bằng chứng

- [Repair notes](phase5_remediation_v2.md).
- [Receipt mới](../experiments/manifests/phase5_remediation_v2_cpu01.json):
  436 source + 573 raw hashes khớp qua re-audit; 169 tracked data hashes không đổi.
- [Báo cáo QA](../docs/evaluation/phase5_remediation_v2_report.md): 69 runtime
  records, 28 exact parity pairs, 41 v7 Broker calls; không có inference LLM thật.
- [Runtime/component contract](../docs/architecture/phase5_remediation_v2_contract.md).
- [Native pair lịch sử](ordinary_pair_gpu_v1.md): chỉ transport/residency/timing,
  không phải quality/ASR; hai worker trước đó phải TERMINATE/-15.
- Entitlement v1 receipt có hash `pytest.log` sai; không sử dụng `valid=true`
  của nó làm điều kiện nghiệm thu. Giữ nguyên bytes và ghi audit độc lập.
- Runtime v6 raw 101/101 và scope v1 raw 19/19 khớp trong lượt audit; điều đó
  không sửa được lỗi hành vi. Các mốc lịch sử nằm trong từng knowledge note.

## Giới hạn

Phase 5 chưa accepted. CPU tests dùng synthetic/Replay/fake guard, không thay
cho kết quả thực nghiệm bảo mật với LLM. Held-out payload không được mở/tune;
validator chỉ hash tracked data. Không thay dataset hoặc mock network tools.

Giữ nguyên thay đổi ngoài phạm vi của người dùng: `plan/phase6.md`–`phase9.md`,
báo cáo tiến độ và `docs/figures/`. Không stage/xóa các mục này.
