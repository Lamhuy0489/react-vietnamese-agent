# Worker shutdown v2 — tiến độ và giới hạn

2026-09-14. Standalone opt-in `ShutdownBackend`/`ShutdownConfig`; chưa thay
ModelPair hoặc runtime đang freeze. [Contract](../docs/architecture/phase5_worker_shutdown_v2_contract.md).

V1 dùng chung stop/terminate grace 0,5s và không có acknowledgement. Native
calculator pilot có 12 TERMINATE/-15, nhưng chưa biết nguyên nhân. V2 quan sát
stop_received, serve_returned, exitcode/reaped riêng; ngân sách graceful 2s độc
lập, identity-hashed. Timeout/backend failure vẫn cancellation budget cũ.

34 test mới đạt: real-spawn synthetic teardown/fallback và mutation
auditor. AST parity giữ transport generate v1 trừ entry quan sát/two timestamps.
Không model/GPU mới, không Test/privateGT. CPU này không chứng minh graceful GPU.

Full QA đã đạt: **2.630 pass/1 optional-tqdm skip**, 581,50s; focused 80 pass,
55,31s. Setup/Ruff/mypy 331 files/knowledge đạt. Source `a45696b`;
462 source/677 raw hashes kiểm độc lập khớp, 169 data hashes không đổi.
Output `results/phase5_worker_shutdown_v2_cpu01`; [receipt](../experiments/manifests/phase5_worker_shutdown_v2_cpu01.json)
SHA-256 `0f2b43d7472b6c62959b2bf6aa94bb9fec070f7d7ba34cf6bf1053ec7ce383df`.
8 v2 events: 2 GRACEFUL, 2 EXITED, 3 TERMINATE, 1 KILL; một control v1 TERMINATE.
Tất cả reaped; ACK/serve return không bị nhầm thành exit. Không còn job chạy.
[Báo cáo và giới hạn](../docs/evaluation/phase5_worker_shutdown_v2_report.md).

Bước sau: pair/agent-only versioned wiring cùng lifecycle auditor, CPU parity
trước exact Kaggle mounts và diagnostic GPU mới. Không sửa inference đã frozen,
không retry calculator semantic outcome. [Sổ link Kaggle](kaggle_resources.md).
[Bản đồ điểm nối và gate cần kiểm](worker_shutdown_integration_next.md).
