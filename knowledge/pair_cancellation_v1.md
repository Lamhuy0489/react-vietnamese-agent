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

25targeted tests pass trước thêm cleanup-interrupt case; final26/full QA pending.
Setup/Ruff/mypy231files pass. CLI `scripts/probe_phase5_pair_cancellation.py`
chỉ CPU, yêu cầu clean committed source; giữ146prior entries và11GPUoverlay,
Test hash-only, raw hashes/rehearsal receipt riêng. Chưa selected rehearsal.

Tiếp theo freeze source, hai fresh CPU rehearsals và full QA; chưa GPU wrapper/
HF entry point cho suite này, chưa submit hoặc có combined busy-VRAM evidence.
Context stress cần protocol riêng: exact tokenized input và forced-length nếu
muốn chứng minh4096+512, không suy ra từ early EOS. Không chọn guard/quality,
runtime integration hoặc Phase5 closure. Không pending account/model access mới.
