# Bàn giao phiên làm việc

Cập nhật: 2026-09-16. Phase5 đang làm, chưa nghiệm thu (4/7≈57% nhóm acceptance).

## Đang làm

**Đã hoàn tất bộ ràng buộc token JSON trên CPU, chưa nối model thật.**
[Report/receipt](../docs/evaluation/phase5_guard_token_language_v1_report.md),
[contract và native gates](../docs/architecture/phase5_guard_token_language_v1_contract.md).
Source `2017e2468467cf3d13d4facbc60e977562e9fd8d`: immutable trie, callback
tách prompt/output, completion check; không repair/fallback sang unconstrained.
Toàn bộ3069tổ hợp schema,202846prefix checks,6138EOS checks; longest76tokens
chỉ là synthetic ASCII-pair, không phải Qwen. Không sửa guard/parser/runtime cũ.

## Bước tiếp theo

1. Xác thực tokenizer Qwen từ snapshot đã pin và EOS/vocabulary; compile đủ3069
   đường đi trong128tokens. Không pruning nhãn để vừa budget.
2. Chạy processor Transformers5.5 thực bằng CPU synthetic logits: masking,
   EOS/prompt slicing, conflicting processors, exception restoration.
3. Chỉ sau đó nối guard-only adapter với identity generation/cache/audit riêng,
   khóa native protocol/exact package preflight rồi GitHub và notebook mới.

Môi trường .venv hiện không có Torch/Transformers/tokenizers. Không cần tải
model lớn về máy; compatibility CPU có thể dùng môi trường worker đóng gói.
Chưa có native adapter, actual-tokenizer admission hay gói sẵn sàng submit.
Thí nghiệm thời gian shutdown làm riêng, không gộp đổi decoding/timeout.

## Bằng chứng

46focused tests (30new)/8,19s; setup/Ruff/mypy420 đạt.
Hai probe từ sourcecommit byte-identical, giữ175baseline pins và184prior
evidence/source files. Logs `results/phase5_guard_language_qa01`, frozen runs
`results/phase5_guard_language_cpu03.json` và `..._cpu04.json`.
[Receipt](../experiments/manifests/phase5_guard_token_language_cpu01.json).
Runs01/02 là working-tree history, không được đổi thành source-pinned evidence.

[Bare-JSON kết quả âm đã chốt](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md):
notebookv1/ID134511636 vẫn ERROR ở auditCLI;4inferences đã recovered-audit,
4model_error,2/6valid/4fenced,8reaped/4VRAMrecovered. Không chạy lại.
[Sổ Kaggle](kaggle_resources.md), [DoD còn thiếu](phase5_remaining.md).
[Bàn giao lịch sử](phase5_handoff_history_20260915.md) không phải lệnh submit mới.

## Giới hạn

Chưa chứng minh native JSON, guard quality/utility hay graceful shutdown.
Không mới model/GPU/Test/private-GT; không fullpytest có Test-assigned fixtures.
**Không submit bare-json-v2 cũ** hoặc retry semantic failures đã chốt.
Không có jobpending trong lịch đã audit; chưa cần tài khoản mới, phải live-check
quota/private access khi gói mới sẵn sàng. Owner Kaggle huylmhuhu khác GitHub
Lamhuy0489; không chia sẻ credential hay chuyển tài nguyên private sang public.
Giữ thay đổi riêng ở plan/phase6–9, docs/BAO_CAO_TIEN_DO_DO_AN.* và docs/figures/.
Development memory không đưa vào benchmark prompts.
