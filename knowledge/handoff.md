# Bàn giao phiên làm việc

Cập nhật: 2026-09-16. Phase5 đang làm, chưa nghiệm thu (4/7≈57% nhóm acceptance).

## Đang làm

**Candidate constrained adapter + cache riêng đã triển khai CPU.**
[Contract](../docs/architecture/phase5_constrained_guard_v1_contract.md),
[report/QA](../docs/evaluation/phase5_constrained_guard_v1_cpu.md).
47tests mới dùng fake CPU đạt; giữ repetition1.1 → prefix, kiểm policy/identity/
completion/cache, restore hook khi lỗi/interrupt và retire backend không retry.
Chưa nối paired factory/observer auditor, chưa actualmodel.generate của adapter.

Nền trước: **Native tokenizer/logits CPU v1 COMPLETE và đã audit.**
[Report/receipts](../docs/evaluation/phase5_guard_language_native_v1_run.md),
[protocol](../docs/architecture/phase5_guard_language_native_v1_contract.md).
Actual `huylmhuhu/react-vn-guard-language-cpu-v1`, version1/ID134521565;
source2269fef, sau download vẫnCOMPLETE/private/sourcekhớp lúc18:36:08UTC.
Qwentokenizer đủ3069values; max36tokens gồmEOS,248actualTransformersmask checks.
Compilation0,839066s; mask/fault/input-recheck0,521304s; không phải model latency.
Không weights/model.generate/GPU/Test/privateGT; không còn jobpending ở lịch này.

Ca negative control xác nhận ForcedBOS chạy sau có thể ghi đè prefix mask.
Lỗi/interrupt được truyền ra, thread settings khôi phục, callback mới vẫn dùng được.
Không thay frozen guard/parser/runtime hay kết quả đã đo.

## Bước tiếp theo

Nối candidate bằng paired-factory/composition version riêng với request-policy,
efficient-request và observer/auditor; không sửa frozen baseline/factory.
Đóng protocol actual GenerationMixin CPU integration để kiểm hooks tương tác
đúng với thư viện pin, receipt và exception restoration; không tải weights.
Sau đó exactpackage/native protocol riêng trước GPU diagnostic mới. Giữ
prompt/model/parser/fallback/shutdown2s để tách hiệu ứng decoding; study shutdown riêng.

Chưa có paired-runtime integration/inference package sẵn sàng. Không submit GPU
chỉ từ47fake tests hoặc248mask checks cũ. Local .venv chưa có Torch/Transformers/
tokenizers; native compatibility trước chạy CPU Kaggle, không trên máy này.

## Bằng chứng

- Adapter source964c51b:340focused tests/15,57s (47mới); setup/Ruff/mypy426/
  knowledge đạt,175baseline+86nativeCPU sourcepins nguyên. Có kiểm live backend
  config trước cache hit. [QA/source/log hashes](../experiments/manifests/phase5_constrained_guard_cpu_qa02.json).
  Raw `results/phase5_constrained_guard_cpu_qa02`; QA01 source99fb189 giữ làm lịch sử.
- Config `configs/guard/constrained_v1_effective.json` chỉ là generation metadata;
  canonical SHA231f3e0b…2efc6, không response/GT. Không submission mới ở bước này.
- Các receipts và58tests dưới đây thuộc mốc native-library CPU trước:
- [Terminal](../experiments/manifests/phase5_guard_language_cpu_terminal01.json),
  [audit](../experiments/manifests/phase5_guard_language_cpu_audit01.json),
  [summary](../experiments/manifests/phase5_guard_language_cpu_summary01.json),
  [QA](../experiments/manifests/phase5_guard_language_cpu_release_qa01.json).
- 58tests/6,40s, setup/Ruff/mypy424/knowledge đạt;86package pins và175baseline pins nguyên.
- [Closure check](../experiments/manifests/phase5_guard_language_cpu_close01.json):
  214preflight raw files kiểm lại, scan37evidence/source files/0credentials.
- Raw/remote: `results/phase5_guard_language_monitor03`; post-download observation:
  `results/phase5_guard_language_terminal04`.
- Audits02/03 dùng cùng observation và byte-identical:
  `results/phase5_guard_language_audit02`, `..._audit03`.
- Local auditor không rerun native libraries; xác thực source/bootstrap/
  tokenizer và metrics được báo cáo trong scope CPU, không model quality.
- Preflight đúng: `build/kaggle/phase5_guard_language_cpu_package02`;
  [corrected receipt](../experiments/manifests/phase5_guard_language_cpu_preflight02_corrected.json).
  Package01 lỗi kiểm aggregate resume; selected02 invalid digest do locale warning;
  cả hai giữ làm lịch sử. Submission helper01 bị chặn local, helper02 mới gửi v1.
- [Kaggle directory](kaggle_resources.md), [DoD queue](phase5_remaining.md).
  [Bare-JSON kết quả âm](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md)
  và [finite-language CPU nền](../docs/evaluation/phase5_guard_token_language_v1_report.md) giữ nguyên.

## Giới hạn

Chưa native constrained model generation/guard quality/utility/graceful shutdown.
**Không submit bare-json-v2 cũ, không gửi lại CPU v1 hoặc retry semantic failures.**
Không fullpytest vì Test-assigned authoring fixtures. Không cần tài khoản mới;
live-check quota/private mounts khi GPU package mới sẵn sàng.
GitHubLamhuy0489 khác Kagglehuylmhuhu; quyềnGitHub không tự cấp quyềnKaggle.
Giữ private/credential ngoàiGit. Giữ chỉnh sửa riêng của user tại plan/phase6–9,
docs/BAO_CAO_TIEN_DO_DO_AN.* và docs/figures/. Không đưa memory vào model prompts.
