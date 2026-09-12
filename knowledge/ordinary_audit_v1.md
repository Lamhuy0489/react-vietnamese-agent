# Kiểm tra độc lập ordinary A/B/A

Source `1f28978`; [contract](../docs/architecture/phase5_ordinary_audit_v1_contract.md).
Hai lớp kiểm tra: supervisor đọc chuỗi READY/3 requests mỗi role và snapshots;
joined native nối policy, attention, metrics, publisher và allocator records.
Hai CLI nhận expected commit tường minh, chỉ ghi receipt mới ngoài raw inputs.

64 test mới đạt trong 7,69 giây. Nhóm liên quan trước phép thử overflow cuối:
244 pass trong 42,24 giây; setup/Ruff/mypy 297/knowledge đạt. Full QA hoàn tất:
2.262 pass/1 optional skip trong 415,95 giây, không lỗi; JUnit
`results/phase5_ordinary_audit_v1_cpu01_pytest.xml`. Không còn test job đang chạy.
[Release QA](../experiments/manifests/phase5_ordinary_audit_cpu_v1_release_qa01.json)
bind source, JUnit, 4 supervisor audits/64 prior raw files và 167 fixture files.
Joined audit đọc 82 inputs: probe 32, policy 30, attention 18, publisher 2.
106 frozen overlay entries/128 prior raw files và hash-only Test seals không đổi.
Quét 249 source/docs/receipt/evidence files với 4 giá trị credential đã biết:
0 matches; không đưa credential files vào Git.

Hai raw CPU runs 03/04 từ runner `44cf902` được audit độc lập hai lần mỗi run,
hai outputs cùng run byte-identical. Không chạy lại inference/model. Bản sao
fixture riêng `results/phase5_ordinary_native_join_cpu_v1_synthetic01` kiểm joined
auditor hai lần; các HF-shaped records được tạo bằng test fixture, mọi timing/
memory/model responses giả lập. Fixture metadata chứa public snapshot hashes,
không weights hoặc benchmark payload. Không gộp với các GPU measurements cũ.

Kiểm worker PID/owner khác nhau, một load, exact attempt/role/request coverage,
prefix snapshots, timing containment, giới hạn allocator/residency/recovery,
publisher bytes và admitted model-file hashes. A mismatch được báo cáo, không
retry/chọn survivors. `native_validated`, source/tokenizer authentication và
Phase 5 acceptance vẫn false; phép kiểm các records không chứng minh native run.

## Bước tiếp theo

1. Xác thực tokenizer metadata để suy pad IDs (hiện vẫn là expected inputs).
2. Đóng gói exact source cho archive/expanded Kaggle layouts và thử imports,
   eight-tool/Dummy/resume; kiểm source/model/wheel identities và output routing.
3. Kiểm quota/private Dataset rồi chạy native A/B/A với model đã pin; audit
   outputs bằng các lớp mới và release-level source/remote checks.
4. A0/A1 task owner, runtime A0–A6/differential/lifecycle, A4/general final và
   grouped Dev vẫn còn mở. Phase 5 chưa nghiệm thu.

Pending access: không cần quyền/model account mới cho kiểm tra CPU; quota và
Dataset version kiểm trước GPU. Không Test payload/private GT/native tensor mới.
