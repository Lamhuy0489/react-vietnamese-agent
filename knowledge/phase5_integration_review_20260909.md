# Review nhánh phase5-integration — 2026-09-09

Owner yêu cầu xem tiến độ và nhánh bạn cùng tài khoản vừa push; review only,
không merge/checkout/push hoặc sửa implementation. Theo phase contract, không
dùng tên commit làm bằng chứng nghiệm thu. Phase 5 vẫn chưa accepted.

## Git và tiến độ

- Remote main: `505149b77f8097114b8d3c1345a952cb74358992`.
- Remote phase5-integration: `7f37634`, hai commit mới `c0815b3` và `7f37634`,
  base đúng remote main. Remote current-project-progress-7ab3c cùng tip.
- Local main: `dab6c64`, một commit cancellation/VRAM recovery chưa push.
  Không trùng đường dẫn thay đổi với nhánh integration, nhưng điều đó không
  chứng minh tương thích hành vi hoặc research integrity.
- Cancellation local đã pass 1.067 tests/301,86s, setup/Ruff/mypy211files và
  knowledge; exact archive/expanded PAX preflight pass cả hai layouts, gồm
  eight tools/fault, 21 Dummy/resume và ba cancellation CPU-stub trials.
  Receipt local: `build/kaggle/phase5_guard_cancellation_v1_preflight01/preflight_receipt.json`.
  Chưa chọn receipt vào Git, chưa push source hoặc submit cancellation GPU.

## Phát hiện cần xử lý trước merge

1. **P1 — guard generation bị hỏng.** `src/react_agent/llm/guard_hf_v1.py:215`
   đổi thành `self.transformers.self.transformers.GenerationConfig`.
   Module/fake module không có thuộc tính `self`; valid generation bị retire.
   Chạy đúng source nhánh trong bản sao tạm: adapter suite 48 pass/3 fail,
   có traceback AttributeError xác nhận nguyên nhân.
2. **P1 — mất bảo vệ credential.** `.gitignore` bỏ `credential kaggle/`,
   `kaggle.json`, `*.key`, `*.pem`, và bỏ ignore generated results/logs.
   `git check-ignore --no-index` với ignore của nhánh xác nhận các đường dẫn
   credential mẫu không được ignore. Không đọc nội dung credential. Không có
   file thuộc các credential paths trên trong tip nhánh đã kiểm tra; đây là
   rủi ro commit nhầm, không phải kết luận đã lộ secret.
3. **P1 — thay loader nhưng giữ danh tính Gemma 4.**
   `src/react_agent/llm/measured_hf.py:42` đổi loader thành
   `Gemma3ForConditionalGeneration` khi profile vẫn là `google/gemma-4`.
   `scripts/preflight_pilot_models.py:47` đổi tiny-model test sang Gemma3,
   trong khi profile và assertion cuối vẫn Gemma4. Static identity mismatch;
   chưa chạy weights/GPU trên nhánh, không khẳng định một lỗi loader cụ thể.
4. **P1 — sửa trực tiếp nguồn đã khóa.** Đối chiếu 134 source hashes trong
   `phase5_guard_hf_v1_validation01.json`: guard_hf_v1.py và measured_hf.py
   không khớp. Không được dùng receipts cũ để nghiệm thu code đã đổi;
   phục hồi frozen source hoặc thiết kế phiên bản mới cùng evidence riêng.

## Kiểm chứng và giới hạn

- Diff tổng: 756 files, trong đó 748 generated files ở
  `results/runtime_output_v2`, còn lại .gitignore và bảy Python files.
  Không có test mới hoặc receipt/report nghiệm thu mới được commit.
  A0/A1 verification script chỉ đổi cách gọi Ruff/mypy qua PATH; phần kiểm tra
  runtime đã có từ base. Kết quả mới không chứng minh A2–A6/GPU đã hoàn tất.
- Không thay data/configs/experiments manifests/docs/knowledge/tests/AGENTS/skills
  so với remote main (kiểm bằng Git diff). Không đọc Test payload/private GT.
- Bản sao tạm chỉ trích src/scripts/tests/pyproject/.gitignore từ Git,
  không checkout main, không đưa benchmark data vào bản sao.
- `pytest tests/unit/test_guard_hf_v1.py -q --tb=short -p no:cacheprovider`:
  **48 passed, 3 failed, 0,51s**. Không chạy full suite nhánh.
- Ruff src/scripts/tests: **7 lỗi I001**; Git diff check: trailing whitespace.
- mypy src/scripts: **12 lỗi/6 files**, checked207files, trong CPU dev env hiện
  tại thiếu optional torch/transformers/matplotlib và đã bị bỏ import ignores.
- Không inference, upload, merge, remote writes hoặc thay bằng chứng đã khóa.

## Tiếp theo

Ưu tiên bạn sửa nhánh integration theo bốn điểm trên, giữ credential guardrails,
loại generated outputs chưa được chọn khỏi thay đổi tích hợp, và chạy QA/receipt
đúng contract. Chỉ tích hợp khi có yêu cầu và checks pass. Sau đó tiếp tục
cancellation GPU probe đã preflight, agent coexistence, grouped Dev protocol.
Không cần tài khoản mới cho bước review. Nên phân chia task/branch để tránh sửa
chung frozen model adapters; việc dùng chung tài khoản không làm hai nhánh tự merge.
