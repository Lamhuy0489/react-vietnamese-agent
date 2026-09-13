# Worker shutdown v2 — tiến độ và giới hạn

2026-09-13. Standalone opt-in `ShutdownBackend`/`ShutdownConfig`; chưa thay
ModelPair hoặc runtime đang freeze. [Contract](../docs/architecture/phase5_worker_shutdown_v2_contract.md).

V1 dùng chung stop/terminate grace 0,5s và không có acknowledgement. Native
calculator pilot có 12 TERMINATE/-15, nhưng chưa biết nguyên nhân. V2 quan sát
stop_received, serve_returned, exitcode/reaped riêng; ngân sách graceful 2s độc
lập, identity-hashed. Timeout/backend failure vẫn cancellation budget cũ.

34 test mới đã đạt sơ bộ: real-spawn synthetic teardown/fallback và mutation
auditor. AST parity giữ transport generate v1 trừ entry quan sát/two timestamps.
Không model/GPU mới, không Test/privateGT. CPU này không chứng minh graceful GPU.

Đang chuẩn bị full QA qua `scripts/verify_phase5_worker_shutdown.py`, output mới
`results/phase5_worker_shutdown_v2_cpu01`; chỉ chọn receipt nếu source/raw/data
hash và setup/Ruff/mypy/pytest/knowledge đều đạt. Raw lỗi giữ nguyên, không ghi đè.

Bước sau: pair/agent-only versioned wiring cùng lifecycle auditor, CPU parity
trước exact Kaggle mounts và diagnostic GPU mới. Không sửa inference đã frozen,
không retry calculator semantic outcome. [Sổ link Kaggle](kaggle_resources.md).
