# Trạng thái hiện tại

Cập nhật: 2026-10-26. **Phase 0–5 đã nghiệm thu. Đang ở R0 của
[lộ trình v2](../docs/project/roadmap_v2_rebuild.md)** (tuần 8/24, hạn 2027-02-19).

## Đã chốt ngày 2026-10-23

- Model RQ1: Qwen3-8B · Gemma 4 12B · Llama 3.1 8B. RQ2 (A0–A6) cố định Qwen3-8B.
- Guard A2: so Prompt Guard 2 86M với Llama-3.2-3B hiện tại trên 80 cặp Dev, chọn bên
  tốt hơn theo kết quả Dev.
- Chỉ số: ASR tính hành động độc hại thực thi được hoặc leakage qua final answer;
  model_error tính là thất bại; CI bootstrap theo family; McNemar cho cặp mức A(k) với A(k−1).
- Chi tiết trong [decision log](../docs/project/decision_log.md).

## Mốc đã xác minh

- **A0 Dev baseline (rebuild A, 2026-10-26):** prompt v3 đóng băng, schema `per_tool_v1`,
  chấm numfix. Qwen3-8B: smoke 12/20, clean Dev 79/150. Llama-3.1-8B: smoke 8/20,
  clean Dev 59/150. Gemma chưa chạy. Xem decision log 2026-10-26.
- Phase 5: release `419938b`, 20/20 DoD. Native 72 completed + 12 model_error.
  Guard: TP21 / FN19 / FP5 / TN35.
- Kiểm dữ liệu ngày 2026-10-23: seal adversarial_v2 hợp lệ (700 biến thể,
  `sealed_read_only`); 23 file clean v1.1 khớp hash trong manifest; hash dataset
  `692ca92a…` không đổi.
- Toàn bộ thay đổi đã push lên branch `codex/phase5-worker-v3-source-freeze-20261001`
  (commit `6509ae0`). Branch **chưa merge vào `main`**.

## Bước tiếp theo

Làm R0 theo [handoff](handoff.md). [Prompt cho phiên sau](next_session_prompt.md) ·
[Nhật ký phiên](session_log.md) · [Trạng thái trước lộ trình v2](history_20261023_before_roadmap_v2_current_status.md).
