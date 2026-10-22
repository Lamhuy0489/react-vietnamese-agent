# Lộ trình v2 — tái cấu trúc sau Phase 5 (đề xuất)

Cập nhật: 2026-10-23 · Trạng thái: **đề xuất, chờ owner chốt ở R0**.
Tài liệu này không thay đổi research contract cho tới khi R0 ghi quyết định vào
[decision log](decision_log.md).

## 1. Chẩn đoán

| Hạng mục | Hiện trạng | Đánh giá |
|---|---|---|
| Benchmark | clean v1.1 (150/100), adversarial_v2 (350+350), robustness 50, Test đã seal | **Giữ.** Đây là tài sản giá trị nhất. |
| Runtime A0–A6, Broker, 8 tool, FinalGate | Đã nghiệm thu 20/20 DoD | **Giữ lõi**, sửa lỗi chất lượng ở R2. |
| Kết quả mô hình | A0 3/20, Dev 5/21; 12/84 lượt lỗi schema (`OUTPUT_SCHEMA_FAILED`); guard recall 52,5%, FPR 12,5% | **Yếu.** Phải sửa trên Dev trước khi mở Test. |
| Quy trình | 287 script, 170 báo cáo, 348 manifest, 92 ghi chú cho 5 phase | **Quá tải.** Đây là phần cần “đập”. |
| Thời gian | Hôm nay đang ở tuần 7/24 (hạn 2027-02-19). Phase 6–9 chưa bắt đầu. | Còn 17 tuần, đủ nếu cắt quy trình. |

Bối cảnh nghiên cứu 2025–2026:

- Các defense chỉ dựa vào bộ phân loại (classifier) thường không bắt được loại tấn
  công chưa thấy khi huấn luyện.
- Defense ở tầng hệ thống, bằng policy hoặc information-flow như CaMeL, cho ASR thấp
  nhất trên AgentDojo, đổi lại mất một phần utility.
- Adaptive attack phá được phần lớn defense từng báo cáo ASR ≈ 0.

Hệ quả cho đồ án: A3–A6 (sensitivity/trust và gate) là điểm mạnh, cần trình bày như
đóng góp chính. A2 (guard) nên được phân tích như một baseline yếu chứ không phải
trụ cột. Luận văn cũng phải nói rõ giới hạn: kết quả không chứng minh độ bền trước
adaptive attack.

## 2. Giữ / đập

**Giữ nguyên, không sửa:** `data/` và các seal, `src/react_agent/` (runtime, broker,
tools, security), `tests/` lõi, `plan/`, file Word gốc, `docs/project/` contract và
invariants, các manifest closure Phase 1–5.

**Đập hoặc thay:**

1. Quy trình bằng chứng: mỗi phase còn lại chỉ có **1 protocol, 1 report, 1 manifest**.
   Bỏ preflight/release/audit lặp theo từng shard. Hash chỉ áp dụng cho data, config
   và kết quả cuối.
2. Script: gắn tag `phase5-closure` trên commit đã nghiệm thu, rồi trên `main` dời các
   script một lần (v1/v2 cũ, preflight, chẩn đoán) vào `scripts/legacy/` hoặc xóa.
   Lịch sử vẫn khôi phục được qua tag. Mục tiêu: dưới 30 script đang dùng.
3. `knowledge/`: gộp còn `current_status`, `handoff`, `kaggle_resources` và
   `runbook`, chuyển `history_*` vào `knowledge/archive/`.
4. Hạ tầng Kaggle: chuẩn hóa **một** worker API có structured output, dùng chung cho
   agent và guard, thay cho nhiều package notebook.

## 3. Lộ trình 17 tuần

| Giai đoạn | Tuần (ngày) | Mục tiêu | Tiêu chí hoàn thành |
|---|---|---|---|
| **R0 Reset** | T8 (24/10–30/10) | Merge branch vào `main`, tag `phase5-closure`, dọn script/knowledge. Chốt `metrics_spec.md`, 3 backbone, ngân sách GPU và quyết định giữ hay bỏ guard ở A2. | `main` xanh (ruff/mypy/pytest), decision log có mục “Roadmap v2 adopted”. |
| **R1 Evaluator** | T9–10 (31/10–13/11) | Phase 6 tối giản: chấm per-task từ trace đã lưu, aggregate, CI theo family. | Golden cases pass; chạy được trên trace Dev cũ; 1 report. |
| **R2 Sửa chất lượng trên Dev** | T11–12 (14/11–27/11) | Ép JSON bằng constrained/structured decoding để xử lý lỗi schema; xét lại `max_steps` 4 → 8; thay hoặc cải thiện guard; chạy Dev đầy đủ A0–A6 (400 lượt) và clean Dev × 3 backbone. | Model_error < 2%; có bảng Dev ASR/utility; config đóng băng. |
| **R3 Freeze** | T13 (28/11–4/12) | Tag `final-config`, dry-run pipeline Test bằng Dummy, ước lượng thời gian GPU. | Không đổi prompt, policy hay config sau mốc này. |
| **R4 Thực nghiệm cuối** | T14–17 (5/12–1/1) | Capability: 100 clean + 250 robustness × 3 backbone (≈1.050 lượt). Security: 300 × 7 mức (≈2.100 lượt). Tùy chọn: một tập adaptive attack nhỏ trên A0/A6 và baseline spotlighting. | Checkpoint đầy đủ, lỗi được giữ trong mẫu số. |
| **R5 Phân tích** | T18–19 (2/1–15/1) | McNemar/bootstrap ghép cặp theo family, phân loại lỗi, biểu đồ, kiểm tra thủ công 10% trace. | Bảng/hình cuối cho RQ1–RQ3. |
| **R6 Viết luận văn** | T20–22 (16/1–5/2) | Chương 1–3 viết song song từ R1, chương 4–5 sau R5. | Bản nháp đầy đủ gửi GVHD. |
| **R7 Buffer + bảo vệ** | T23–24 (6/2–19/2) | Sửa theo góp ý, slide, demo, tập dượt. | Nộp đúng hạn. |

Ước lượng compute: khoảng 3.150 lượt chạy cuối × 30–90 giây ≈ 26–80 giờ GPU. Với hạn
mức Kaggle khoảng 30 giờ/tuần/tài khoản (số thực tế xem trong trang Settings), R4 cần
2–3 tuần. Chỉ dùng tài khoản thuộc đúng thành viên nhóm. Nếu R2 trễ, cắt adaptive
attack trước, rồi giảm robustness xuống còn 1 backbone. Không cắt security A0–A6.

## 4. Chỉ số chốt ở R0

- **RQ1:** task success (typed), tool-call validity, step count.
- **RQ2:** ASR (hành động độc hại thực thi được tính, đề xuất bị chặn không tính),
  leakage qua final answer, benign utility, false-block rate,
  utility-under-attack, overhead (latency/token).
- **RQ3:** độ giảm success và độ tăng ASR theo từng loại biến thể tiếng Việt.
- Mẫu số: mọi task được lên lịch; model_error tính là thất bại và báo cáo riêng.
- Thống kê: CI bootstrap 95% theo canonical family; McNemar cho cặp mức A(k) với A(k−1).

## 5. Rủi ro và cách xử lý

| Rủi ro | Xử lý |
|---|---|
| Không có thành viên thứ hai để review | Nhờ GVHD hoặc một bạn khác review 10% trace; ghi rõ trong luận văn. |
| Kaggle hết quota hoặc worker không ổn định | Checkpoint resume theo task; ưu tiên security trước capability. |
| A5/A6 chặn dư (C6) | Báo cáo như trade-off utility, không nới policy sau khi đã thấy Test. |
| Hội đồng hỏi về adaptive attack | Nêu giới hạn; nếu còn thời gian thì chạy thử nghiệm nhỏ ở R4. |
