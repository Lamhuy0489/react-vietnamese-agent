# Trạng thái hiện tại

Cập nhật: 2026-10-28 10:30. **Phase 0–5 đã nghiệm thu. Lộ trình
[v2](../docs/project/roadmap_v2_rebuild.md), rebuild A:** R1–R3 xong, **R4 security Test xong**
(2026-10-28); Test-2 đã seal (`1576b89a…`), E2 code xong, tiếp theo chạy Dev mốc E2 rồi D2; R0 còn 21 test chỉ hỏng
trên CI và dọn script (tuần 8/24, hạn 2027-02-19).

## Đã chốt ngày 2026-10-23

- Model RQ1: Qwen3-8B · Gemma 4 12B · Llama 3.1 8B. RQ2 (A0–A6) cố định Qwen3-8B.
- Guard A2: so Prompt Guard 2 86M với Llama-3.2-3B hiện tại trên 80 cặp Dev, chọn bên
  tốt hơn theo kết quả Dev.
- Chỉ số: ASR tính hành động độc hại thực thi được hoặc leakage qua final answer;
  model_error tính là thất bại; CI bootstrap theo family; McNemar cho cặp mức A(k) với A(k−1).
- Chi tiết trong [decision log](../docs/project/decision_log.md).

## Mốc đã xác minh

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

Tạo 250 biến thể robustness RQ3 → final_config_v2 → clean Test + robustness × 3 backbone, theo
[handoff](handoff.md). [Prompt cho phiên sau](next_session_prompt.md) ·
[Nhật ký phiên](session_log.md) · [Trạng thái trước lộ trình v2](history_20261023_before_roadmap_v2_current_status.md).
