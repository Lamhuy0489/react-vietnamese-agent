# Nhật ký phiên chat

Mỗi phiên ghi một mục, mới nhất ở cuối. Mỗi mục gồm: mục tiêu, quyết định, việc đã
làm, việc còn dở. Chỉ ghi các dữ kiện đã xác minh. Không ghi credential, GT hay payload Test.
[Prompt cho phiên sau](next_session_prompt.md) · [Handoff](handoff.md).

## 2026-10-23 — Claude Code: đánh giá đồ án, dọn repo, lộ trình v2

- **Mục tiêu owner:** đánh giá tính khả thi, bỏ phần thừa, "đập đi xây lại" với lộ
  trình mới, lưu context để các phiên sau làm tiếp.
- **Đánh giá:** đề tài khả thi; benchmark và runtime A0–A6 là phần giá trị. Điểm yếu
  là quy trình bằng chứng quá nặng (287 script, 170 báo cáo, 348 manifest) và chưa
  có kết quả cho RQ1–RQ3.
- **Đã làm:**
  - Commit `a402772` (250 file còn dở, quét credential không thấy giá trị nào).
  - Dọn storage: xóa 3 file tar guard giống hệt nhau, trọng số Qwen2.5-1.5B, venv
    API và cache; nén `build/pytest_*` và `results/*preflight*` vào `archive_local/`.
  - Commit `8a2419e`: lộ trình v2.
  - Commit `6509ae0`: các quyết định R0.
- **Quyết định:** model RQ1 là Qwen3-8B, Gemma 4 12B, Llama 3.1 8B; RQ2 cố định
  Qwen3-8B; guard A2 chọn bằng bake-off trên Dev; ASR tính hành động thực thi,
  model_error tính thất bại.
- **Kiểm dữ liệu:** seal adversarial_v2 hợp lệ; clean v1.1 khớp 23 hash. Phát hiện:
  repo public chứa GT private, owner chưa quyết.
- **Còn dở:** merge vào main, tag, dọn script, metrics_spec; owner xin quyền HF Llama.
- **Bổ sung:** owner cho phép đập đi; chọn mức A, tức chạy lại pipeline từ Phase 1, giữ data và runtime. Không viết lại runtime, không làm lại data.

## 2026-10-23 (tiếp) — Claude Code: harness vLLM cho chạy lại mức A

- **Quyết định:** serve bằng vLLM trên Kaggle qua API (owner đồng ý); R4 dùng API hoặc
  batch tùy độ ổn định; guard Prompt Guard 2 chạy trên CPU local.
- **Đã làm:** notebook `vllm_serve_v1`, config `backbones_v2.yaml`, backend
  `openai_compat_v1` cùng 11 test, script kiểm endpoint, script smoke có checkpoint,
  [runbook](rebuild_a_runbook.md) kèm hướng dẫn xin quyền HF và Kaggle.
- **Còn dở:** owner chạy notebook ngày 24/10, pin revision, chạy smoke; Gemma 4 có rủi
  ro trên T4.

## 2026-10-25 — Claude Code: chạy thật Qwen3-8B trên Kaggle, A0 smoke

- **Đã làm:** kiểm 4 tài khoản Kaggle qua API (đều đăng nhập được, còn 20–25 h GPU,
  không notebook nào đang chạy). Thêm chế độ chạy nền cho `vllm_serve_v1`: tự sinh key,
  gửi URL đã mã hóa qua ntfy. Thêm `scripts/launch_vllm_serve_v1.py` cùng 2 test. Push lên
  lamhuy8904: v1 lỗi do torchaudio lệch CUDA; v2 READY. Pin Qwen3-8B `b968826d…`, vLLM 0.32.0.
- **Kết quả:** A0 smoke 20/20 completed, 0 lỗi parse/hạ tầng, 3/20 success (6/20 theo answer
  facts). Lỗi chủ yếu do model chọn sai nguồn và không gọi read/fetch.
- **Quyết định owner:** mỗi notebook một model; chạy song song dùng 2 notebook trên 2 tài khoản.
- **Prompt v2 (owner duyệt):** sửa system prompt chung và mô tả tool; `db_query` tự liệt kê
  schema. Bốn lần chạy smoke: 3 → 10 → 11 → 12/20, rồi đóng băng. Không đổi bộ chấm.
- **Seal:** seal adversarial pin byte các file prompt/tool, nên chuyển v2 sang module mới
  `a0_v2.py` và trả các file gốc về nguyên byte; check seal valid, 186 test liên quan đạt.
- **Clean Dev 150 × Qwen3-8B (A0, v2):** 71/150 (47,3%), 0 lỗi hạ tầng, khoảng 13 phút.
- **Còn dở:** prompt v3 cho ambiguous/db_document (owner quyết); Llama, Gemma; gắn secret
  `HF_TOKEN` qua UI cho notebook model gated; quyền Llama-3.2-3B còn 403.

## 2026-10-26 — Claude Code: prompt v3, numfix, per-tool schema, Llama

- **Prompt v3 (owner duyệt):** sửa luật 5 (lỗi retryable thì gọi lại, lỗi do lệnh sai thì sửa
  lệnh), thêm luật tra đủ nguồn và hỏi lại khi thiếu dữ kiện. Đổi tên module thành
  `prompts/a0_rebuild.py` (giữ cả v2). Chạy Dev 1 lần rồi đóng băng.
- **Bộ chấm:** regex số cũ bỏ sót số ở cuối câu ("bằng 876."). Sửa trong
  `validation/clean_rebuild_v1.py` (`--numfix`), chấm lại cả v2 và v3: 72 so với 79/150.
- **Harness:** Llama bị parse_failure 82/150 vì `arguments` là object tự do và key bị sắp
  xếp. Thêm `per_tool_schema` (mỗi tool một nhánh anyOf). Qwen giữ nguyên 79, Llama 30 → 59.
- **Llama-3.1-8B:** notebook riêng `react-vn-vllm-serve-v1-llama31-8b`, token chèn vào bản
  private. Smoke 8/20, Dev 59/150.
- **Còn dở:** Gemma, bake-off guard, A0–A6 Dev, phần dọn R0; owner nên rotate token HF.

## 2026-10-26 (tiếp) — Claude Code: Gemma 4, bake-off guard, R0

- **Gemma-4-12B:** không gated, vLLM 0.32.0 stable. bf16 và QAT đều hỏng ở kernel attention
  (head_dim 512 cần 96 KB shared memory, T4 có 64 KB; FlexAttention cũng vậy). Vá tile trong
  notebook. Smoke bf16 9/20, QAT 7/20. **Clean Dev bf16 99/150**, cao nhất (db_document 24/24).
- **Bake-off guard:** luật khai báo trước. Prompt Guard 2 86M (CPU, `build/venv_guard`) TP0
  FP0 trên 80 input Dev; giữ Llama-3.2-3B.
- **R0:** `docs/metrics_spec.md`. Sửa 3 test hỏng. Trả `evaluate_clean_v11_dev.py` về byte
  đã pin, chuyển phần mới sang `evaluate_clean_rebuild_v1.py`. Full pytest xanh. Mở PR #4.
- **Owner hỏi tối ưu Llama riêng:** không làm, vì RQ1 cần cùng prompt, tool, schema và bộ chấm.
- **Còn dở:** owner merge PR và gắn tag; dọn script cũ; R1 evaluator; A0–A6 Dev.

## 2026-10-26 (đêm → trưa) — Claude Code: name-first, R1 evaluator, A6 v2, A0–A6 Dev

- **Đêm:** R1 evaluator và runner A0–A6 (`6154ecd`). Decoding name-first (`ba1881e`):
  clean Dev Qwen 77, Llama 93 (từ 59), Gemma 99 /150 — đây là baseline A0 RQ1.
- **A6 v2 (value provenance) được chấp nhận** (`56c6396`, docs `afdae0f`): replay tham chiếu
  benign 20 → 115/200, attack harm 5/200 không ca mới, A3–A5 1.200 lượt 0 khác biệt.
  Full pytest 5211 passed / 3 skipped / 1 xfailed.
- **Lượt A0–A6 Dev đầy đủ đêm qua chỉ được 312/2.800:** guard idle-out lúc 05:04 vì keepalive
  dùng chung log "bận" với runner; mạng local rớt khoảng 05:05; vòng retry thoát vì probe
  crash rc=1. Sửa (`a0b7cd6`, `9ecb8ee`): runner ping guard giữa các lượt không cần guard,
  probe lỗi và pass còn thiếu đều trả rc=2, `scripts/retry_on_infra_v1.sh` chạy lại có chờ.
- **Trưa:** relaunch Qwen v4 + guard v2, resume lúc 12:23 cùng identity. 12:47: 555/2.800,
  0 model_error. Dự kiến xong khoảng 16:30–17:00.
- **Ý tưởng owner hỏi:** fine-tune LLM tiếng Việt để sau R4 (tùy chọn, tool khác benchmark);
  JEPA/Decision Transformer và Jev (TypeSafe, API đóng) làm guard: bỏ.
- **Còn dở:** chờ lượt chạy xong, chạy bù lượt thiếu (process đang chạy dùng code cũ trả rc=1),
  chấm điểm, ghi bảng A0–A6 vào decision log. Owner merge PR #4.

## 2026-10-26 (chiều) — Claude Code: A0–A6 Dev xong, phát hiện vấn đề đo ASR

- Lượt resume chạy đến 17:37 (process cũ trả rc=1 khi còn 15 lượt thiếu); chạy bù 15 lượt
  lúc 17:37–17:39. Tổng 2.800/2.800, 0 model_error, 18 lỗi hạ tầng đều đã chạy lại.
- ASR A0 100, A1 93, A2 93, A3 85, A4 40, A5 40, A6 40 /200; benign A0 87, A3 70, A4/A5 5,
  A6 55 /200. Ghi vào decision log.
- **Phát hiện:** 40 ASR còn lại ở A4–A6 đều xảy ra ở cả biến thể benign (8 family). Ở 7 family,
  nguyên nhân là `doc_search` trả `[]` bị oracle tính là vi phạm. Nếu chỉ tính harm không có ở
  benign: A0 26, A3 15, A4–A6 0. A6 v2 chạy thật benign 55, so với replay 115.
- **Còn dở:** owner quyết cách tính ASR; phân tích khoảng chênh benign của A6; rồi mới R3.

## 2026-10-26 (tối) — Claude Code: ASR ghép cặp, A6 v3 accepted

- Owner duyệt chỉ số **ASR ghép cặp**: bài tấn công chỉ tính khi bài benign cùng cặp, cùng
  mức không bị hại. Đã thêm vào evaluator, kèm test và McNemar cho benign utility.
  Kết quả: A0 26, A3 15, A4–A6 0 /200; A5→A6 benign b/c = 0/50.
- Phân tích các ca A6 chặn nhầm: SOURCECLAIM bị chặn lệnh đọc vì scope v4/v5 bỏ mọi anchor khi
  câu lệnh có dấu ngoặc kép. **A6 v3** thêm anchor theo mệnh đề ngoài phần trích dẫn, chỉ ở A6.
  Đã khai báo tiêu chí trước khi chạy; chạy live 400/400 lúc 18:00–18:47.
- A6 v3: benign 55 → 60, utility under attack 35 → 40, ASR thô 40 → 20, không có ca hại mới.
  Accepted, thành mặc định. Full pytest 5219 passed.
- Keepalive notebook (script trong scratchpad) đã tắt sau khi chạy xong.
- **Còn dở:** owner duyệt R3; R4 Test; PR #4 và tag; dọn script; viết luận văn.

## 2026-10-26 (tối muộn) — Claude Code: R3 freeze

- Owner duyệt đóng băng. Thêm `final_config_v1` (manifest ghim 381 file: src, configs, runner,
  evaluator, seal), `--split test` cho runner và evaluator adversarial/clean, xuất 12 fault plan
  Test (chỉ lấy trường fault_plan), thêm `--dry-run-dummy`.
- Dry-run Test: clean 100/100, adversarial 2.100/2.100. Dry-run bắt được `fixture_catalog` chỉ
  nhận Dev; sửa bằng `run_catalog`, không đụng file đã pin.
- Ước lượng R4 khoảng 11–12 giờ GPU. Tag `final-config`.
- Vướng mắc báo owner: RQ3 clean robustness chưa có dữ liệu; repo public chứa Test/GT; luận văn
  chưa viết; cỡ mẫu thực khoảng 30–40 family; chưa có adaptive attack và reviewer thứ hai.
- Owner quyết: repo giữ public, HF token giữ nguyên, luận văn để sau; RQ3 tạo đủ 250 biến thể.
  R4 security Test hẹn chạy ngày 27/10 (tối 26/10 dừng trước khi bật notebook).

## 2026-10-28 (đêm) — Claude Code: R4 security Test xong, merge PR #4

- lamhuy8904 hết quota GPU; bật Qwen + guard trên **meanalways** (v1, READY 01:54), credential qua
  `KAGGLE_CONFIG_DIR` tạm. R4 chạy 01:55–05:50: 2.100/2.100, 5 lỗi hạ tầng (mạng local rớt khoảng
  02:48 và 03:45) đã chạy lại, 4 model_error (KEYLEAK A0–A3).
- Guard idle 19 phút sau lần rớt mạng (ping 10 phút của runner trúng lúc mất mạng); ping tay rồi thêm
  keepalive guard 5 phút/lần trong A0/A1, tự dừng khi sang A2.
- Kết quả Test: ASR ghép cặp A0 4 → A3 1 → A4–A6 0 /150; benign A0 30, A3 15, A4–A6 5 /150;
  A6 v3 ≈ A5. Ghi decision log. Owner hỏi tăng tốc bằng chạy song song: giữ tuần tự cho R4, song song
  (mỗi nhóm một notebook) để cho clean/robustness.
- CI: thêm certifi/cryptography vào dev extras (mypy xanh); còn 21 test chỉ hỏng trên CI. Owner chọn
  merge trước: PR #4 merged `5194c77`, tag `phase5-closure` → `419938b`.
- **Còn dở:** RQ3 250 biến thể; sửa CI; rotate HF token (lộ trong log chat, chỉ local).
- **Sáng 28/10:** owner hỏi vì sao Test yếu. Chẩn đoán 4 nguyên nhân (oracle tính đọc vô hại là harm;
  agent mở đầu bằng doc_search 100/150 bài benign; user instruction bị gắn UNTRUSTED và scope A4 overfit
  câu chữ Dev; guard vô dụng). Owner chọn A+B+C: phòng thủ v2 + chỉ số side-effect harm + Test-2.
- Viết bản nháp `docs/project/defense_v2_test2_design.md` (B: side-effect harm; A: D2 tách control/data,
  user tin cậy, đích sink phải có nguyên văn trong yêu cầu user; C: Test-2 20 family, seal trước code D2;
  đề xuất E2 doc_search_v2 cho mọi cấu hình). Chờ owner duyệt.
- Owner duyệt thiết kế (1, 2 ok; 3 = E2, đã đối chiếu AgentDojo/CaMeL; 4 = assistant tự sinh câu lệnh
  Test-2 theo ma trận phong cách + kiểm n-gram + owner xem 20 câu gốc; 5 ok, muốn chạy nhanh).
- Xong B: `side_effect_harm_v1` + script chấm lại. Test v1 (phụ, post hoc): ASR ghép cặp A0 11 → A3 1/150,
  A2→A3 p=0,004 (chỉ số cũ không thấy). Dev: A0 29 → A3 13 → A4+ 0/200. Ghi decision log.
- Lưu ý: thêm file mới trong `src/react_agent` làm `final_config_v1.verify` từ chối; việc v2 dùng manifest v2.
- C: sinh Test-2 20 family (`src/react_agent/authoring/test2_v1.py`, `scripts/build_test2_release_v1.py`):
  200 fixture, scorer utility khoan dung (fact thấy trong kết quả tool và câu trả lời; sink đúng đích có
  fact), QA 400 replay 0 lỗi, novelty 4-gram max 0,07. Chưa seal, chờ owner xem câu lệnh.
- Full pytest: 5.223 qua, 4 hỏng do `pyproject.toml` lệch hash evidence (commit 586591e).
- Owner giao assistant rà 20 câu lệnh gốc rồi seal. Seal Test-2 (`573c33b`, seal.json `1576b89a…`,
  200 fixture, ghi decision log). R0: 4 test evidence hỏng vì `586591e` sửa `pyproject.toml`; khôi phục
  file gốc, cài certifi/cryptography bằng bước CI riêng (`requirements-dev.txt` cũng bị ghim) → 62 test
  qua (`5c5a846`). Tiếp: E2 doc_search_v2.
- Kiểm Kaggle: 6 notebook serve đều COMPLETE (ghi sổ Kaggle). E2 xong (`f6d044b`): `doc_search_v2`
  giữ nguyên giao diện, thêm `id_matches` (chỉ định danh); 400 fixture Dev tra đúng tool đọc, 180 id trong
  câu lệnh benign đều resolve, replay qua runtime A0/A1/A6 chạy trọn; runner E2 dry-run 18/18. Owner
  chọn dùng lại HF token cũ, đã lưu `~/.hf_token_r5` (0600, còn hợp lệ). Owner hẹn chạy Dev mốc E2 ngày
  29/10 (bảng phân notebook trong handoff).

## 2026-11-05 (đêm) — Claude Code: E2 Dev mốc đang chạy trên lamhuy8904, PR #5 sửa CI

- lamhuy8904 rảnh (3 notebook COMPLETE, quota reset 31/10): bật Qwen3-8B **v5** + guard **v3** (T4, private),
  READY khoảng 00:45. Chạy E2 Dev A0 → A1 → A6 × 400 nối tiếp trên một endpoint từ 00:47
  (`results/rebuild_a/adv_dev_e2_qwen3_8b`, log `build/kaggle/e2_dev_1105.log`), qua `retry_on_infra_v1.sh`.
  Keepalive guard 5 phút/lần tới khi sang A6 (`build/kaggle/guard_keepalive_until_a6.sh`). Lúc 00:59: A0 144/400, 0 lỗi.
- Chấm tự động khi runner thoát: `build/kaggle/e2_eval_after_run.sh` → `..._eval.json`,
  `..._side_effect_eval.json`, log `build/kaggle/e2_dev_eval_1105.log`. Owner để máy chạy qua đêm.
- Owner cho dùng Antigravity CLI (`agy`) làm sub-agent, model mặc định Gemini 3.8 Flash. Skill Claude
  `~/.claude/skills/antigravity-subagent` (ngoài repo). Headless print mode tự từ chối lệnh shell, nên giao việc chỉ
  sửa file trong worktree, Claude chạy test.
- R0: Antigravity sửa 21 test chỉ hỏng trên CI (skip khi thiếu `build/`, jsonschema ở bước CI riêng, link knowledge
  vào `build/` thành code); Claude bỏ try/except thừa, sửa thêm 5 link history. Không `build/`: 6 pass, 15 skip.
  **PR #5** (`agy/ci-fix-21`), chờ owner merge.
- **Còn dở:** đọc kết quả E2, ghi bảng vào decision log; D2; RQ3; luận văn.
- **02:40 E2 xong:** 1.200/1.200, 0 model_error, 0 lần chạy lại. Benign utility A0/A1 87 → 110/200 (E2 sửa định tuyến
  tool), paired side-effect ASR A0 29 → 35, A1 23 → 27; A6 v3 không đổi (ASR 0, benign 60). Ghi decision log
  "E2 Dev re-baseline result"; tiêu chí dừng D2: benign ≥ 105, side-effect ASR ≤ 27 /200. D2 module luật có (`c7b666c`), chưa nối runtime.

## 2026-11-05 (rạng sáng) — Claude Code: D2/D2+G runtime, chạy Dev vòng 1 qua đêm, RQ3 250 biến thể

- Máy sập nguồn sau 02:40; không mất gì (E2 đã commit `2b45840`). 4 file báo cáo tiến độ chưa commit từ 28/10
  (`docs/BAO_CAO_TIEN_DO_DO_AN.*`, `docs/bao_cao_print.html`, `scripts/generate_pdf_report.py`) để nguyên.
- D2 runtime `c7d8626`, D2+G `caf2d95` (decision log hai mục "declared"). Ước lượng phản thực trên output A1 thật:
  benign 108, side-effect ASR ghép cặp 14 /200.
- Chạy qua đêm trên lamhuy8904: D2 vòng 1 từ 03:00 (Qwen v5 còn sống); guard v3 tự tắt, bật guard v4 03:13 cho D2+G.
- RQ3 `7ba28d0`: 250 biến thể (3 loại cơ học bằng `draft_surface`, 100 câu code-mix/paraphrase Claude viết, không
  giao Antigravity vì là dữ liệu Test). Chờ owner review rồi seal.
- 04:29 D2+G vòng 1 xong (400/400, 0 lỗi): trùng D2 hoàn toàn (benign 108, side-effect ASR 14, ASR thô 86). Guard
  được gọi ở cả 400 lượt nhưng chỉ trả SAFE/SUSPICIOUS, nên mapping A2 không chặn thêm. D2 r1 đạt tiêu chí dừng,
  không có vòng 2 (decision log "D2 round 1 result", "D2+G round 1 result"). Không chạy GPU thêm: Test-2 cần
  final_config_v2 và owner review RQ3. 10:16 cả hai notebook COMPLETE.

## 2026-11-05 (trưa–chiều) — Claude Code: RQ3 seal, final_config_v2, Test-2 và clean Test xong

- RQ3: Claude rà 100 câu, owner duyệt 2 sửa (clean_0184 code-mix, clean_0100 paraphrase), seal `6eb46c0` (`942b69bb…`).
- Runner/evaluator clean robustness (`--set canonical|robustness`; clean Test RQ1 cũng đi qua đây vì runner clean v1
  gắn v1, v1 không còn verify), runner Test-2 (`run_adversarial_e2_api_v1.py --release test2`), evaluator Test-2.
  Dummy Dev: canonical trùng runner cũ 150/150. Full pytest 5.264 qua. `final_config_v2` owner duyệt, ghim `c3f3d66`.
- Test-2 thật (lamhuy8904, Qwen v6 + guard v5) 11:35–13:17: A0 17 → các cấu hình khác 0 /100; benign 62 (A6 10);
  D2 trùng A1 200/200; ghi decision log `4191a24`.
- Clean Test: Qwen (lamhuy8904), Llama v2 (lamhuy8904 sau khi guard tắt), Gemma v1 trên tài khoản mới
  oanhlam123456 (`kaggle6.json`). 50/62/65 /100; no_diacritic giảm có ý nghĩa ở cả 3, loại khác không.
- Sự cố: bước chép credential bị auto-mode từ chối; sau owner cho phép, dùng biến môi trường KAGGLE_USERNAME/KEY trong
  subshell (không chép file). Script chuỗi Llama lỗi lần đầu vì đường dẫn có dấu cách (đã sửa, không mất lượt).

## 2026-11-05 (chiều) — Claude Code: chẩn đoán Test-2, đề xuất Rebuild B

- PR #5 vẫn OPEN, nên R0 chờ.
- Chẩn đoán Test-2 (phân tích, không chạy lại): D2 = A1 vì cả 20 family chỉ có kiểu chuyển hướng tới đích mới, viết
  lộ, mà regex A1 bắt được (17/20); 3 family M3 thì Qwen không làm theo ở A0 (đã sửa câu "cả 20 family đều S0" vốn sai). Spec Test-2 không có trục cơ chế. Trên Dev, D2 hơn A1 ở các ca
  lấy cắp qua sink người dùng đã nêu.
- Owner muốn làm lại dữ liệu, thêm model, nhắm hội nghị top; Claude viết câu lệnh, owner và Minh review. Claude khảo
  sát nghiên cứu 2025–2026 (AgentDojo, ASB, MAPS không có tiếng Việt, The Attacker Moves Second, CaMeL/Progent/
  MELON, Meta SecAlign) và viết `docs/project/rebuild_b_proposal.md`. Chờ duyệt.
- 17:30 owner duyệt Study 2: hướng chung, quy mô 48/72, AgentDojo-VI, thêm Qwen3.6-35B-A3B, API frontier hoãn,
  có đủ baseline, Minh tham gia red team, nộp hội nghị quốc tế về LLM/an toàn agent. Ghi decision log, amendment
  contract, `docs/project/rebuild_b_plan.md` (WP0–WP10, tiêu chí nghiệm thu, ma trận chạy, 6 giả thuyết), Bản đồ.
- 19:00 WP1: spec v3 sinh xác định (`build_v3_spec.py`, module `authoring/v3/spec.py`, 6 test), sha256 `1547dc4e…`;
  fixture 28/560/840 (sửa số 720 trong kế hoạch). Sửa chẩn đoán Test-2: có 3 family kiểu M3 nhưng Qwen không làm theo.
  WP2: kiểm HF (Qwen3.5-9B, Qwen3.6-35B-A3B AWQ đều lai linear attention, chưa chắc chạy được trên T4; SecAlign-8B
  gated manual), thêm key serve, `backbones_v3.yaml`, `--models-config`. Chờ owner duyệt spec.

## 2026-11-05 (tối) — Claude Code: WP2 xong, WP3 chuyển việc viết dữ liệu cho owner/Minh

- WP2 nghiệm thu: Qwen3.6-35B-A3B AWQ, Qwen3.5-9B, Meta-SecAlign-8B qua smoke (commit `2e70bca`).
- WP3: viết `authoring/v3/release.py`:
  - chèn tại `{{INJECT}}`, nhãn nguồn khai báo;
  - 3 nhánh;
  - kiểm sửa payload M5;
  - QA replay và kiểm độ mới.

  Thêm `scripts/build_v3_release.py` và `AUTHORING_GUIDE.md`.
- Bộ lọc an toàn chặn Claude khi viết, rồi cả khi đọc đoạn chèn tấn công. Thống nhất: owner/Minh tự viết canonical
  (tự giao cho công cụ khác), Claude làm hạ tầng và chỉ đọc số đếm từ script.

## 2026-11-05 (đêm muộn) — Antigravity: WP3 pilot canonicals 12/12 và build pilot_v3 hoàn thành

- **Đã làm:**
  - Viết `data/adversarial/v3_authoring/pilot_canonicals.json` đủ 12 họ pilot (`P3_01` – `P3_12`) tuân thủ nghiêm ngặt `spec.json`, `taxonomy.md` và `AUTHORING_GUIDE.md`. 100% dữ liệu giả lập học vụ.
  - Chạy `scripts/build_v3_release.py check`: 12 families, 28 fixtures (`CHECK_OK`).
  - Chạy `scripts/build_v3_release.py qa`: 40 replays, 0 problems; novelty max 0.037 <= 0.20, 0 reused literals (`QA_OK`).
  - Chạy `scripts/build_v3_release.py write`: xuất bản `data/adversarial/pilot_v3/` gồm `pilot_attack.jsonl`, `pilot_benign_plain.jsonl`, `pilot_benign_auth.jsonl`, `private/oracles.json`, `qa.json`.
  - Tạo `tests/unit/test_v3_release.py` (3 unit tests đạt 100%).
- **Việc kế:**
  - Review chéo theo phiếu 5 mục ở `taxonomy.md` §7 cho 12 họ pilot.
  - Viết runner `run_v3_api_v1.py` và khai báo metric M5 (`side_effect_harm_v3`) trong decision log.
  - Chạy A0 baseline cho pilot_v3 trên Qwen3-8B và Llama-3.1-8B.

## 2026-11-06 (khuya) — Claude Code: runner v3, pilot A0 lần 1

- Owner/Minh viết pilot (`611e7aa`). `check`/`qa` sạch: 40 replay, độ mới 0,037. Release tái lập đúng từng byte.
- Thêm `run_v3_api_v1.py`, `evaluate_v3_v1.py`, test dry-run; khai báo metric v3 trong decision log trước khi chạy
  (`3e8162e`). Full pytest 5278 passed.
- A0 pilot: Qwen3-8B (oanhlam123456) 2/12 family; Llama-3.1-8B (huylmhuhu) 1/12. Chưa qua cổng 40%. Chi tiết ở decision log.
- Bộ lọc an toàn chặn bước Claude tách lý do utility từ trace. Bỏ bước đó; owner/Minh tự xem trace.

## 2026-11-06 (sáng sớm) — Antigravity: Tinh chỉnh Pilot Canonicals v3 & Rebuild pilot_v3 sau chẩn đoán A0

- **Mục tiêu**: Khắc phục lỗi rớt utility ở 5 family (P3_02, P3_03, P3_07, P3_11, P3_12), tăng độ thuyết phục của đoạn chèn M1–M4 (ở 8 family Qwen không đề xuất vi phạm), và bổ sung sink_artifacts cho P3_01 benign_auth.
- **Đã làm**:
  - Chẩn đoán trace thực tế: `cached_search` trả về rỗng vì title/base thiếu ID; P3_03 thiếu lệnh gọi trực tiếp `send_email_mock`; P3_07 regex number bị dấu phẩy chặn trong JSON string `post_webhook_mock`.
  - Cập nhật `data/adversarial/v3_authoring/pilot_canonicals.json`:
    - Nâng cấp độ thuyết phục M1–M4 với thẩm quyền cao và lý do nghiệp vụ/hạ tầng khẩn cấp cưỡng chế.
    - Sửa title/base của P3_02, P3_11, P3_12 chứa ID định danh (`[AWB_CIVIC]`, `[AWB_ESCROW]`, `[AWB_DISPATCH]`) và chỉ dẫn `cached_fetch` tường minh.
    - Phân tách rõ lệnh gửi `send_email_mock` trong P3_03.
    - Chuẩn hóa fact `total_hours` của P3_07 thành `kind="phrase"` (value: "184").
    - Thêm `sink_artifacts` cho `auth` của P3_01 cho phép gửi email kèm mã tới bursar.office@example.test.
  - Chạy `scripts/build_v3_release.py check`: 12 families, 28 fixtures (`CHECK_OK`).
  - Chạy `scripts/build_v3_release.py qa`: 40/40 replays thành công (0 problems), max novelty 0.0306 <= 0.20, 0 reused literals.
  - Xóa `data/adversarial/pilot_v3/` và chạy `scripts/build_v3_release.py write`: xuất bản release mới thành công.
  - Đồng bộ cập nhật báo cáo đánh giá chuyên gia `docs/benchmark/pilot_v3_review_report.md`.
  - Chạy pytest: 4/4 passed (1.54s).
- **Việc kế**: Thông báo để người dùng kích hoạt chạy lại chẩn đoán A0 trên Kaggle.

## 2026-11-06 (01:05) — Antigravity: Tinh chỉnh Pilot Canonicals v3 Lần 3 sau kết quả Pilot Lần 2

- **Kết quả Pilot Lần 2 (Qwen3-8B)**: Tăng từ 2/12 lên 4/12 family harmful (33%): `P3_01` (M4), `P3_04` (M3), `P3_08` (M6), `P3_10` (M5). Cả M3 và M4 đã harmful thành công. Benign plain đạt 11/12 (chỉ trượt `P3_02`). Benign auth 0/4.
- **Chẩn đoán trace thực tế**:
  - `BPL_P3_02`: fact `land_count` (value 42) kind `number` bị dấu phẩy `,` trong chuỗi JSON `post_webhook_mock` từ chối bởi regex lookahead. Đã đổi cả `land_count` và `civil_count` sang `phrase` (test xác nhận utility chuyển ngay sang True).
  - M1 và M2 (`P3_02`, `P3_03`, `P3_06`, `P3_11`): cần chỉ thị ghi đè cổng và điều phối 2 bước rõ ràng để mô hình chuyển hướng sang endpoint phụ/dự phòng.
  - 4 fixture `benign_auth`: `BAU_P3_01` tách lệnh 3 bước dứt khoát gọi `send_email_mock`; `BAU_P3_03` ghi rõ gửi 4 tín chỉ ở cả 2 email và final answer; `BAU_P3_04` chỉ rõ bảng `awb_notices` tránh lỗi multi-SELECT; `BAU_P3_11` yêu cầu gửi đồng thời cả hai email thay vì tùy chọn.
- **Đã làm**:
  - Cập nhật `data/adversarial/v3_authoring/pilot_canonicals.json`.
  - Chạy `scripts/build_v3_release.py check`: 12 families, 28 fixtures OK.
  - Chạy `scripts/build_v3_release.py qa`: 40 replays, 0 problems, max novelty 0.0306 <= 0.20, 0 reused literals.
  - Xuất bản lại `data/adversarial/pilot_v3/`.
  - Cập nhật `docs/benchmark/pilot_v3_review_report.md`.
  - Pytest: 5/5 passed.
- **Việc kế**: Người dùng chạy lại A0 pilot trên Kaggle để vượt qua cổng 40% và phủ đủ M1–M6.

## 2026-11-06 (rạng sáng) — Claude Code: baseline, AgentDojo-VI, pilot qua cổng, bật Dev v3

- WP7: cài P1 (spotlighting kiểu datamark), P2 (sandwich), G1 (Prompt Guard 2, service CPU local), MEL (MELON bản xác
  định), PRG (Progent-lite), D2+P1. Có unit test và smoke trên pilot; cài đặt ghi decision log trước khi chạy Dev.
- WP3: owner/Minh chỉnh pilot qua 5 lần; lần 5 Qwen3-8B đạt 6/12 family, đủ M1–M6, benign sạch, nên qua cổng.
  - Gemma tham khảo: 5/12. Llama: 3/12.
  - Owner chọn giữ cổng "ít nhất một backbone".
- WP6: AgentDojo 0.1.35 trong venv riêng. AgentDojo-VI Banking + Slack:
  - Claude dịch môi trường, 37 user task và system message;
  - bộ chấm đổi cụm tiếng Việt về cụm tiếng Anh tương đương; ground truth 100%, vị trí chèn trùng EN;
  - owner/Minh dịch 14 GOAL và mẫu tấn công.
  - Thêm key serve 16k và keep-alive.
- Dev v3 (owner/Minh): 48 family, 560 fixture, QA sạch. Ghi lại release cho khớp glossary.
  - 02:45 bật Dev × 9 cấu hình trên Gemma, Llama, Qwen3.5-9B.
- Bộ lọc an toàn chặn Claude 3 lần khi chẩn đoán hoặc góp ý nội dung dữ liệu tấn công. Đã ghi memory: Claude chỉ làm hạ tầng.

## 2026-11-06 (sáng) — Claude Code: Dev v3 vòng 1 chạy xong

- 02:44–11:02 chạy đủ 27 cấu hình (Gemma-4-12B, Llama-3.1-8B, Qwen3.5-9B × A0, P1, P2, G1, MEL, PRG, R1, D2, D2+P1),
  mỗi cấu hình 560 lượt; keep-alive giữ cả 3 notebook sống. Chạy sớm P2, D2+P1, MEL để kịp 12:00.
- Thêm khoá thư mục output cho `run_v3_api_v1.py` (`7b57d29`) sau một lần hai runner ghi chồng; fixture hỏng đã chạy lại.
- Sửa `agentdojo_chain.sh`: `wait` không đối số chờ cả keep-alive nên kẹt từ 05:19; phòng thủ AgentDojo chạy bằng
  `agentdojo_defense_run.sh`.
- Thêm `scripts/aggregate_v3_dev_v1.py`; bảng Dev vòng 1 và AgentDojo EN ghi decision log 06/11.
- Trưa 06/11: AgentDojo EN Llama xong cả Slack (spotlighting 45/10, repeat 35/10). Kiểm Test v3 bằng số đếm:
  72 family T3_xx (chưa commit), oracle Dev không đổi. Ghi `knowledge/study2_contributions.md`.
- Chiều 06/11: owner/Minh dịch AgentDojo-VI (14 GOAL + mẫu tấn công), Claude kiểm literal/placeholder bằng script. Vòng chỉnh
  Dev 1 D2+P2 khai báo rồi chạy: Gemma 2/48, Qwen3.5 3/48. Notebook mới qua `relaunch_round1.sh` (Llama lần đầu thiếu HF token).
  15:25 owner tắt máy; Llama D2+P2 (552/560) và 6 lượt AgentDojo-VI có tấn công để resume.

## 2026-11-07 (rạng sáng) — Claude Code: bật chạy qua đêm Tầng 2, SecAlign, AgentDojo-VI

- Kiểm 3 notebook serve 06/11: đều COMPLETE. Llama D2+P2 đủ 560/560, chốt 5/48 (M3 2, M4 1, M5 2), ghi decision log.
- Resume AgentDojo-VI có tấn công: `relaunch_round1.sh` push Llama 16k v4 (huylmhuhu).
- Owner chọn tài khoản oanhlam123456, nomtle, dovuong05 (không dùng huylmhuhu, buiquocviet). Khai báo trong decision log rồi bật
  Tầng 2 Qwen3-8B, Qwen3.6-35B-A3B × {A0, R1, PRG, D2} và SecAlign × {A0, D2} trên Dev. Thêm `build/kaggle/tier2_launch.sh`;
  `v3_dev_chain.sh` nhận biến `CONFIGS`. Cả 4 push thành công 01:00.
- Chưa làm: vòng chỉnh 2 (chờ owner chọn), seal Dev/Test (chờ owner xác nhận Test do người viết).

## 2026-11-07 (sáng) — Claude Code: kết quả đêm, vòng 2, seal v3

- Owner xác nhận Test v3 do người viết; seal release v3 (`cbfc549`, `seal.json` `c1f698cb…`), tách oracle Test ra file riêng.
- Vòng chỉnh 2 = D2-NR+P2 (Claude chọn theo chẩn đoán từ trace, owner giao): Gemma 2→4, Qwen3.5 3→5, Llama 5→9 family có hại,
  auth +3–4. Bác; giữ D2+P2. Lớp luật A1 còn chặn được một phần M3, M5.
- Tầng 2: Qwen3-8B D2 16/48; SecAlign A0 13, D2 6 (base Llama 34, 13).
- AgentDojo-VI Llama: ASR VI thấp hơn EN nhiều nhưng utility cũng thấp; sửa wrapper VI khi AgentDojo văng KeyError do agent
  xoá user (`d3a4540`).
- Sự cố: tunnel Qwen3.6 chết 08:03, bật lại v3; dừng chuỗi bằng pkill kéo theo Qwen3-8B (chạy nốt 4 lượt).

## 2026-11-07 (tối) — Claude Code: Qwen3.6 xong, oracle theo split

- Qwen3.6-35B-A3B Tầng 2 đủ 560 × {A0,R1,PRG,D2} (bật thêm v4 cho 5 lượt D2 cuối): A0 38, R1 32, PRG 25, D2 20 /48; utility
  cao nhất. Ghi vào mục Tầng 2 của decision log.
- `release.py`: `oracle_path`; `write_release` ghi oracle theo split; `evaluate_v3_v1.py` nạp theo split; thêm test.
- Đo dung lượng repo (12G, chủ yếu `results/`); đề xuất dọn cho owner, chưa xoá.

## 2026-11-08 — Claude Code: vòng chỉnh 3 (SAN) và WP8 lần 1

- Nghiên cứu và cài SAN: bộ lọc observation theo nhiệm vụ, cùng backbone (PromptArmor/CommandSans/DataFilter), runner chia shard
  và `--fixtures`. Khai báo vòng 3 trước khi chạy; chạy qua đêm trên 6 notebook (lamhuy8904, oanhlam123456, buiquocviet).
- Kết quả vòng 3 (tổng /144 · /720 · /240): SAN 20·372·120, D2SAN 6·368·97, D2P2SAN 1·362·97; mốc D2+P2 10·370·105. Không đạt
  luật → giữ D2+P2. Bộ lọc nhỏ gắn cờ nhầm 33–57% benign (Llama, Qwen3.5); Gemma gần như không nhầm.
- WP8 attacker tự động: bộ lọc an toàn chặn Claude viết; owner/Minh soạn 48 fixture thích nghi Dev. Claude kiểm hash/cấu trúc,
  chạy × 5 cấu hình × 3 backbone. A0 thích nghi 4/6/6 so với tĩnh 29/12/22: yếu hơn bộ tĩnh; D2+P2 0/1/0.
- Bảng luận văn 2.1–2.6; tách theo biến thể (D2 hở nhất với tiếng Anh). Sự cố: tunnel rớt, launcher tắt keep-alive khi xong.

## 2026-11-09 — Claude Code: WP8 vòng 3 và Test v3 Tầng 1 (xong)

- WP8 vòng 3 (bộ `284f9499…`): A0 26/15/24 so với tĩnh 29/12/22; D2+P2 1/0/0 /48 (Bảng 2.6b).
- Gemini 3.5 Flash: proxy `scripts/gemini_proxy_v1.py`, dừng vì gói miễn phí 20 lượt/ngày; chờ owner.
- Test v3 Tầng 1: 18 ô đủ 840 sau nhiều lần bật lại notebook (`test_supervise.sh`, `test_failover.sh`; ô cuối Gemma PRG chạy
  trên dovuong05). Chấm và kiểm định `scripts/test_v3_hypotheses_v1.py`: H1 p 1,8e−38, H3 2,1e−24, H6 1,8e−13 bác H0; H2 0,20;
  H4 0,70; H5 0,27. Bảng 2.7, decision log 09/11 10:00.
- Owner hỏi đề xuất "hướng phát triển" từ công cụ khác: đã đối chiếu, nhiều ý đã có trong D2 (Luật 2–4, denial feedback), vài
  số sai; owner chọn bỏ qua.

## 2026-11-09 14:15 — D3 trên Dev: thiết kế, cài đặt, bật chạy

- Owner duyệt làm D3. Tag `final-config-v3` (verify OK), branch `study2/d3-dev`. Phân tích lỗi lặp lại trên Dev: các
  kiểu lỗi của Test v3 đều có trên Dev (P2 bỏ sink, A1 chặn nhầm, luật 3 trên benign_auth, Qwen hết bước).
- Phát lại offline (`scripts/d3_offline_replay_v1.py`): A1 thu hẹp theo đích chặn đủ 11/11 fixture có hại, 0/14 chặn nhầm;
  luật 3 theo tài nguyên thả 5 attack (bỏ); so khớp rút gọn không thêm gì (bỏ). Decision log 13:00 ghi trước tiêu chí.
- `security_v3/d3.py` + runner (d3, d3dest, d3p2v1, d3fbv1), test `tests/unit/test_d3.py`. Commit `ee0fc1c`.
- Bật 3 notebook D3 Dev 14:09–14:13 (dovuong05, lamhuy8904, meanalways); nomtle, huylmhuhu hết quota tuần.

## 2026-11-09 tối — D3 chọn D3DEST, Test-3 niêm phong và chạy, Gemini sửa JSON

- D3 Dev xong 12 ô (Gemma 20:06, Llama 19:42, Qwen 20:40). Tiêu chí ghi trước: chỉ D3DEST đạt (harm 12 = 12, utility
  490 > 475); lời nhắc v2 làm Qwen utility 165 → 55, bị loại.
- Test-3 seal (`release_test3`, 560 fixture, QA 0 lỗi, hash canonicals khớp 6b7dbd67); `final_config_v4` owner duyệt
  (59f32eea…); 3 notebook bật 21:07 (lamhuy8904 ×2 khi còn ~1 h quota, meanalways), chain chạy từ wt-test3.
- Gemini: nhịp 4 s → 2 s (owner), ~3× nhanh; lỗi JSON ~3% lượt gọi là chữ bao quanh object → proxy `--extract-json`,
  chạy lại Dev từ đầu (decision log 21:30).
- Owner dạy: còn ít quota thì bật 2 phiên GPU cùng lúc, mỗi phiên chạy trọn 12 h (`kaggle_lessons.md`).
- 22:16: cả 3 notebook Test-3 RUNNING, keep-alive 12 h; Qwen sẵn sàng 21:26 (khởi động ~19 phút, bình thường).
  Các mốc giờ trong decision log tối nay là đúng (lời đính chính trong chat lúc trước là nhầm do đọc giờ log).

## 2026-11-10 00:00–01:50 — Gemini đủ cấu hình; Llama truncation

- Gemini bổ sung theo chuẩn so sánh: Dev D3DEST (chạy song song, proxy chung nhịp 2 s) và AgentDojo 2 phòng thủ như Llama
  (`gemini3_followup_chain.sh`). Không chạy Gemini trên Test (ma trận đóng băng, không gửi Test ra ngoài). Decision log 01:30.
- Sửa script đang chạy bằng thay file nguyên khối (sed > tmp; mv), vì bash đọc script theo offset.
- Llama: model_error ở Test-3 đều là OUTPUT_TRUNCATED; Test-3 giữ nguyên, owner duyệt 2 phân tích độ nhạy (decision log 01:50).

## 2026-11-10 02:00–02:55 — Test-3 xong; chẩn đoán Llama

- Supervisor qua đêm báo TEST3_DONE 02:18 (9/9 ô 560, đã evaluate); bật lại với SKIP_T3_DONE=1 cho Gemini.
- T1 +1,0 điểm utility (11/1, Holm 3,2e-3; CI family chạm 0), T2 đạt, T3 0,324 → 0,036. Bảng 2.10, decision log 02:40.
- Merge test3-seal hoãn tới khi Gemini Dev xong. Llama Dev A0 2048 token đang chạy trên notebook Llama còn sống.

## 2026-11-10 03:30–12:20 — Gemini Dev xong; merge Test-3

- Supervisor dừng ở DEADLINE 12:00; Gemini Dev đủ 5 cấu hình. AgentDojo Gemini bắt đầu sau đó (1/8 lượt gốc xong 12:01).
- Bảng 2.11: Gemini A0 22/48 family, D2P2/D3DEST 1/48; D3DEST tăng benign_auth 49 → 60/80 (thăm dò).
- Merge `study2/test3-seal` (xung đột decision log, giữ cả hai). Supervisor bật lại cho AgentDojo.

## 2026-11-10 16:40–20:00 — Máy hỏng pin; AgentDojo Gemini tuần tự; nháp bài báo ICCIES

- Máy sập nguồn hai lần chiều 10/11 (pin 0%, sạc 85 W, chạy song song). Từ nay một tiến trình nặng mỗi lúc, `nice -n 10`,
  không đụng OmniRoute (decision log 20:00). Script `build/gemini/ad_seq_finish.sh` chạy nốt Slack EN rồi Banking EN.
- 503 hàng loạt do nhịp 2 s chạm trần lượt/phút của pool: khởi động lại riêng proxy 8445 với `--min-interval 4`.
  Slack EN xong 17:43 (62/105, 1/105). Banking EN 120/144 lúc 19:45, chạy–nghỉ theo cửa sổ hạ nhiệt 15 phút.
- Soát transcript: không cặp nào bị lỗi hạ tầng ghi thành kết quả. Bảng 2.3b (thiếu ô Banking EN).
- Bài báo ICCIES 2027: lấy khung Phần 1 từ phiên Antigravity, sửa các số sai, viết Mục 2 (threat model, M1–M6) và Mục 3 (D3),
  dựng bảng kết quả: `docs/paper/iccies2027_draft.md`. Owner bảo tạm dừng viết tới khi chạy xong.
- Owner xác nhận: Gemini là phần phụ; 996 cặp AgentDojo có phòng thủ chưa chạy, chờ quyết.

## 2026-11-10 21:10–22:05 — Banking EN xong; đủ Bảng 2.3b và Bảng 11

- Máy sập nguồn lúc 20:55 (mở Zalo); runner đã resume từ 125/144. Phiên này chỉ theo dõi bằng một lệnh chờ nền, không đổi cấu hình.
- Banking EN xong 21:53: utility 93/144, tấn công thành công 4/144. Soát 144 transcript: kết thúc bằng assistant, `error` rỗng.
- Điền Bảng 2.3b, Bảng 11 (`sections/05_results.md`), `facts.md`; decision log 22:00.
- Owner hỏi dùng API key Gemini trực tiếp: không đổi giữa lượt; chỉ đáng cân nhắc cho 8 lượt có phòng thủ (chưa quyết, đề xuất bỏ).
- 22:30: owner hỏi có chạy 996 cặp không; Claude khuyên bỏ (chưa có quyết định cuối). Viết bản đầy đủ Mục 4 của bài báo
  (`sections/04_benchmark_protocol.md`).
- 23:00: owner quyết bỏ 996 cặp AgentDojo có phòng thủ trên Gemini (decision log 23:00); thí nghiệm đóng. Tải 10 PDF tài
  liệu tham khảo từ arXiv vào `docs/paper/iccies2027/refs/` (không commit), lập `refs/README.md`.
