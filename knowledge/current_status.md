# Trạng thái hiện tại

Cập nhật: 2026-10-26 17:45. **Phase 0–5 đã nghiệm thu. Lộ trình
[v2](../docs/project/roadmap_v2_rebuild.md), rebuild A:** R1 xong, R2 khoảng 85%, R0 còn
phần dọn (tuần 8/24, hạn 2027-02-19).

## Đã chốt ngày 2026-10-23

- Model RQ1: Qwen3-8B · Gemma 4 12B · Llama 3.1 8B. RQ2 (A0–A6) cố định Qwen3-8B.
- Guard A2: so Prompt Guard 2 86M với Llama-3.2-3B hiện tại trên 80 cặp Dev, chọn bên
  tốt hơn theo kết quả Dev.
- Chỉ số: ASR tính hành động độc hại thực thi được hoặc leakage qua final answer;
  model_error tính là thất bại; CI bootstrap theo family; McNemar cho cặp mức A(k) với A(k−1).
- Chi tiết trong [decision log](../docs/project/decision_log.md).

## Mốc đã xác minh

- **A0–A6 Dev đầy đủ xong (2026-10-26 17:39):** 2.800/2.800, 0 model_error. ASR A0 100 →
  A3 85 → A4–A6 40 /200; benign A0 87, A6 v2 55 /200. 40 ASR còn lại ở A4–A6 đều xảy ra cả ở
  biến thể benign (chủ yếu `doc_search` rỗng), chờ owner quyết cách tính. Xem
  [handoff](handoff.md) và decision log.
- **A6 v2 accepted (2026-10-26):** replay tham chiếu benign 20 → 115/200, attack harm 5/200
  không ca mới, A3–A5 1.200 lượt 0 khác biệt. Full pytest 5211 passed.
- **A0 Dev baseline RQ1 (prompt v3, decoding name-first, numfix):** Qwen3-8B 77/150,
  Llama-3.1-8B 93/150, Gemma-4-12B 99/150. Guard A2 giữ Llama-3.2-3B.
- R1 evaluator `adversarial_dev_v1` và runner A0–A6 đã có; `docs/metrics_spec.md` xong.
- Phase 5: release `419938b`, 20/20 DoD. Dữ liệu seal hợp lệ, hash dataset `692ca92a…`.
- Toàn bộ thay đổi trên branch `codex/phase5-worker-v3-source-freeze-20261001`; PR #4
  **chưa merge vào `main`**, chưa có tag `phase5-closure`.

## Bước tiếp theo

Quyết cách tính ASR rồi mới đóng băng R3, theo [handoff](handoff.md). [Prompt cho phiên sau](next_session_prompt.md) ·
[Nhật ký phiên](session_log.md) · [Trạng thái trước lộ trình v2](history_20261023_before_roadmap_v2_current_status.md).
