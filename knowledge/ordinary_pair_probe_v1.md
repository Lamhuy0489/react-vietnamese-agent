# Ordinary repeated-request pair — CPU

Source `44cf902`; [contract](../docs/architecture/phase5_ordinary_pair_probe_v1_contract.md).
Runner `scripts/run_phase5_ordinary_pair.py` có stub CPU mặc định và HF mode rõ
ràng cho worker GPU; builder giữ chain Ready → progress → policy → attention →
native từ source gốc. A/B/A chạy xen kẽ agent/guard, mỗi role 3 request; không
retry, không ép min length, không dùng benchmark/Test.

Hai lượt real-spawn CPU độc lập đều valid: 6/6 submitted-returned, một worker
mỗi role, recovery sáu mẫu và mọi handle reaped; 4 PID khác nhau/64 raw files.
Receipt và JUnit nằm trong [release QA](../experiments/manifests/phase5_ordinary_pair_cpu_v1_release_qa01.json).
40 test mới, focused 166 pass/33,14 giây; full QA 2.198 pass/1 optional skip/
406,24 giây; setup/Ruff/mypy 293/knowledge đạt. Không còn test job đang chạy.

Selected: `results/phase5_ordinary_pair_cpu_v1_run03` và `run04`. Commit lấy
trực tiếp bằng `git rev-parse HEAD`, truyền qua environment, đối chiếu manifest
và source bytes với `git show`. Runs 01/02 đã truyền sai full commit; giữ nguyên
64 raw files cũ, ghi rõ excluded trong receipt. Không sửa raw manifest để chữa
identity. Runner hiện kiểm cú pháp SHA; xác thực source vẫn thuộc release audit.
Đã kiểm lại 106 frozen overlay entries, 174 raw files của policy pair trước và
Test seals (hash-only), không đổi. Quét 139 source/docs/receipt/raw files với
4 giá trị credential đã biết: 0 matches; credentials không được đưa vào Git.

Đây là bằng chứng transport/residency/cleanup CPU với response và memory giả lập,
không phải native model quality, latency, GPU memory, graceful shutdown hay
Phase 5 acceptance. Bước tiếp: independent supervisor-bound native audit,
publisher/tokenizer/source/load/memory/placement authentication và exact Kaggle
package preflight; sau đó mới chạy HF mode trên Kaggle. A0/A1 vẫn cần task owner
agent-only và runtime A0–A6/differential/grouped Dev gates chưa đóng.
