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
