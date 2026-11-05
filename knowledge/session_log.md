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
