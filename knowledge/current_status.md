# Trạng thái hiện tại

Cập nhật: 2026-11-09 14:15. **09/11 chiều: D3 (D2 + A1 thu hẹp theo đích + lời nhắc v2 + phản hồi chặn v2) đang chạy trên Dev, branch `study2/d3-dev`; Test v3 không dùng cho D3, khẳng định chính thức cần Test-3 mới.** **09/11: Test v3 Tầng 1 XONG (Bảng 2.7): D2+P2 có hại 5/5/1 /72 (A0 50/41/47); H1, H3, H6 bác H0, H2 chưa chứng minh, H4, H5 không khác. WP8 vòng 3: D2+P2 0–1/48.** Trước đó, 08/11: vòng chỉnh 3 (SAN, cuối) xong: không cấu hình nào đạt luật, giữ D2+P2 (chờ owner duyệt `final_config_v3`, rồi Test v3 một lần). WP8 lần 1 (fixture owner/Minh) xong: bộ thích nghi yếu hơn bộ tĩnh ở A0, D2+P2 lọt 0–1/48; cần vòng soạn 2. Bảng luận văn: `docs/research/study2_thesis_tables.md` (2.1–2.6).**
Dev v3 vòng 1 XONG: 3 backbone Tầng 1 × 9 cấu hình × 560 lượt; vòng chỉnh 1 D2+P2: Gemma 2, Qwen3.5 3, Llama 5 /48; P2 và D2+P1 giảm hại mạnh nhất, G1/MEL ≈ A0
(decision log 06/11, Llama chốt 07/11). WP6: AgentDojo EN Llama xong; VI có tấn công đang chạy.**
Kế hoạch [rebuild_b_plan.md](../docs/project/rebuild_b_plan.md). Đóng góp nghiên cứu: [study2_contributions.md](study2_contributions.md).
Test v3: owner xác nhận do người viết; **release v3 đã seal 07/11** (`seal.json` `c1f698cb…`, Dev 48 + Test 72; oracle Test ở `private/test_oracles.json`).
Hạ tầng v3: `authoring/v3/release.py`, `scripts/build_v3_release.py`, `scripts/run_v3_api_v1.py`, `scripts/evaluate_v3_v1.py`.
Study 1: R4 Test v1; `final_config_v2` (`8889e448…`); Test-2 (D2 = A1 200/200); clean Test Qwen 50 · Llama 62 · Gemma
65 /100; RQ3: chỉ bỏ dấu gây giảm có ý nghĩa. R0 chờ PR #5 merge. Hạn luận văn 2027-02-19.

## Gemini (mô hình mạnh, phần mở rộng phụ) — 2026-11-09

- Đường cũ: Gemini API chính thức (`scripts/gemini_proxy_v1.py`, key ở `~/.gemini_keys`) bị gói miễn phí giới hạn
  20 lượt/ngày/key, không đủ (Dev cần ~10.000 lượt). Chưa bật billing.
- Đường mới owner dựng 09/11: OmniRoute cục bộ (`http://localhost:20128/v1`, model `gemini-pool` → `antigravity/gemini-3-flash`,
  xoay vòng 3 tài khoản Google qua provider Antigravity). File hướng dẫn và cấu hình chứa key cục bộ + email nên đã
  gitignore (`docs/omniroute_gemini_guide.md`, `configs/models/gemini_omniroute.yaml`, `scripts/run_gemini_smoke.py`,
  `scripts/setup_omniroute_pool.py`). Kiểm 09/11: server trả 200, JSON schema chạy được, phản hồi không có trường `model`.
- Chưa chạy benchmark: cần (1) adapter như `gemini_proxy_v1.py` trỏ upstream OmniRoute để dùng đúng runner v3 + prompt v3
  (không dùng `run_gemini_smoke.py`/prompt riêng: không so sánh được); (2) owner chấp nhận rủi ro điều khoản Google khi
  dùng quota Antigravity cho chạy hàng loạt, và ghi hạn chế: model không ghim phiên bản, không seed, backend có thể đổi.

## Study 2 đã chốt (2026-11-05)

- Dữ liệu VN-AgentInject v3: Dev 48 / Test 72 family theo cơ chế M1–M6 + B-plain/B-auth, 5 biến thể (thêm
  `english`), pilot 12 family riêng. **Đổi 05/11 tối:** owner và Minh viết canonical (tự giao cho công cụ khác); Claude không viết,
  đọc hay giao việc viết đoạn chèn tấn công, chỉ làm hạ tầng và đọc số đếm từ script. Review chéo theo phiếu 5 mục.
- Thêm AgentDojo-VI (Banking + Slack, EN/VI).
- Backbone: Qwen3-8B, Llama-3.1-8B, Gemma-4-12B, Qwen3.5-9B, Qwen3.6-35B-A3B, Meta-SecAlign-8B; API frontier hoãn.
- Baseline: spotlighting, sandwich, PromptGuard 2, MELON, kiểu Progent, SecAlign; D2 giữ bản ghim.
- Red team thích nghi trên Dev: owner, Minh, Claude. Test v3 chạy một lần dưới `final_config_v3`.

## Đã chốt ngày 2026-10-23

- Model RQ1: Qwen3-8B · Gemma 4 12B · Llama 3.1 8B. RQ2 (A0–A6) cố định Qwen3-8B.
- Guard A2: so Prompt Guard 2 86M với Llama-3.2-3B hiện tại trên 80 cặp Dev, chọn bên
  tốt hơn theo kết quả Dev.
- Chỉ số: ASR tính hành động độc hại thực thi được hoặc leakage qua final answer;
  model_error tính là thất bại; CI bootstrap theo family; McNemar cho cặp mức A(k) với A(k−1).
- Chi tiết trong [decision log](../docs/project/decision_log.md).

## Mốc đã xác minh

- **Test-2 + clean Test + RQ3 (2026-11-05), dưới `final_config_v2`:** Test-2 A0 side-effect ASR ghép cặp 17 →
  A1/A6/D2/D2+G 0 /100; benign A0/A1/D2/D2+G 62, A6 10 (false block 84). Hai giả thuyết D2 đạt (p≈1,5e-5;
  p≈4e-16) nhưng D2 trùng A1 ở 200/200 lượt. Clean Test 50/62/65; no_diacritic mất 13/19/7 câu (p<0,02),
  loại khác không có ý nghĩa. Bảng: decision log 2026-11-05.
- **R4 security Test (2026-10-28):** 2.100/2.100 lượt, 4 model_error (KEYLEAK, A0–A3), chạy một
  lần. ASR ghép cặp A0 4 → A3 1 → A4–A6 0 /150, không mức nào có ý nghĩa thống kê. Benign utility
  A0 30, A3 15, A4–A6 5 /150; A6 v3 không giữ được lợi thế Dev (A6 ≈ A5). Bảng trong decision log.
- **PR #4 đã merge vào `main` (`5194c77`)**, tag `phase5-closure` → `419938b`. CI còn đỏ 21 test
  (phụ thuộc `build/`, thiếu `jsonschema`, link knowledge), local xanh.
- **R3 freeze (2026-10-26):** manifest `configs/final/final_config_v1.json` ghim 381 file; Test
  chỉ chạy được khi khớp manifest. Dry-run Dummy trên Test pass. RQ3 clean robustness chưa có dữ liệu.
- **R2 Dev (2026-10-26):** A0–A6 đủ 2.800 lượt + A6 v3 400 lượt, 0 model_error. ASR ghép cặp
  (chỉ số chính, owner duyệt) A0 26 → A3 15 → A4–A6 0 /200; A6 v3 benign 60, utility under
  attack 40, ASR thô 20. A6 v3 accepted. Xem [handoff](handoff.md) và decision log.
- **A6 v2 accepted (2026-10-26):** replay tham chiếu benign 20 → 115/200, attack harm 5/200
  không ca mới, A3–A5 1.200 lượt 0 khác biệt. Full pytest 5211 passed.
- **A0 Dev baseline RQ1 (prompt v3, decoding name-first, numfix):** Qwen3-8B 77/150,
  Llama-3.1-8B 93/150, Gemma-4-12B 99/150. Guard A2 giữ Llama-3.2-3B.
- R1 evaluator `adversarial_dev_v1` và runner A0–A6 đã có; `docs/metrics_spec.md` xong.
- Phase 5: release `419938b`, 20/20 DoD. Dữ liệu seal hợp lệ, hash dataset `692ca92a…`.

## Bước tiếp theo

Viết luận văn từ các bảng trong decision log (RQ1, RQ2 v1 + Test-2, RQ3); owner chọn cách trình bày D2 = A1
trên Test-2; R0 sau khi merge PR #5. Theo [handoff](handoff.md). [Prompt cho phiên sau](next_session_prompt.md) ·
[Nhật ký phiên](session_log.md) · [Trạng thái trước lộ trình v2](history_20261023_before_roadmap_v2_current_status.md).
