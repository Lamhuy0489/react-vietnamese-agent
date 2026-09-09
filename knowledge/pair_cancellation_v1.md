# Pair cancellation v1 — CPU implementation, 2026-09-09

[Contract](../docs/architecture/phase5_pair_cancellation_v1_contract.md).
Ba fresh pairs theo thứ tự agent_busy,guard_busy,guard_ignore_term. Wrapper
giữ backend resident, không gọi model.generate; host busy command chạy smallCUDA
chỉ khi explicit HF mode. CPU dùng backend/memory giả lập và real spawn.

Durable baseline/ready/busy/closed/recovery/trial/summary; stop-after-failure,
giữ error class, cleanup cả hai, không pass khi handle pending hoặc thiếu reap.
Timeout agent180/guard120 trong contract GPU, CPU rehearsal0,2s ghi riêng config.
Ca thường TERMINATE/-15, ignore-term KILL/-9; sibling method ghi đúng thực tế.
Không thay nguồn ModelPair/WarmGuard/HF v1/v2 hoặc kết quả pair GPU62files.

Source5d326bf đã chạy hai clean-source rehearsals validation01/02; cả ba ca đều
pass,12workers reaped, stable summaries identical.44raw files/run +receipt,
raw PID/timing bytes khác nhau.18synthetic recovery samples/run match baseline.
[Selected receipt](../experiments/manifests/phase5_pair_cancellation_v1_validation01.json),
[report](../docs/evaluation/phase5_pair_cancellation_v1_report.md).
Full final-source QA1.389tests/356,32s pass,26new tests gồm cleanup-interrupt.
Setup/Ruff/mypy231files/knowledge pass; không test/kernel job còn chạy.
[Release QA](../experiments/manifests/phase5_pair_cancellation_v1_release_qa01.json).
CLI `scripts/probe_phase5_pair_cancellation.py`
chỉ CPU;146prior entries và11GPUoverlay,62GPUraw hashes giữ nguyên; Test hash-only.

Tiếp theo exact GPU packaging; chưa GPU wrapper/
HF entry point cho suite này, chưa submit hoặc có combined busy-VRAM evidence.
Context stress cần protocol riêng: exact tokenized input và forced-length nếu
muốn chứng minh4096+512, không suy ra từ early EOS. Không chọn guard/quality,
runtime integration hoặc Phase5 closure. Không pending account/model access mới.
