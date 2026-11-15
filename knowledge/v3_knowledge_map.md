# Bản đồ tri thức BrokerGuard v3

Trang trung tâm (hub) cho phần mở rộng v3. Mỗi mục là một nút, liên kết dẫn tới tài liệu gốc. Trong Obsidian, mở Graph
view để thấy các nút nối với nhau. Số liệu và quyết định nằm ở tài liệu gốc, trang này chỉ chỉ đường.

Cập nhật: 2026-11-15 18:40. Phiên sau bắt đầu ở [prompt phiên sau](next_session_prompt.md) và [bàn giao](handoff.md).

## 1. Vì sao có v3

- [Bản thiết kế v3](../docs/project/brokerguard_v3_extension_design.md): review yêu cầu gì, C1–C4, mô hình hình thức,
  giao thức đánh giá, điểm khác với CaMeL, FIDES, ClawGuard, Progent.
- Nguồn review: `Review Huy.docx` ở root (không commit). Lỗ hổng v1 đo bằng `scripts/paper_bypass_causes_v1.py`.
- Bài v1 hiện có: [mục lục bài](../docs/paper/iccies2027/README.md), [số liệu được phép dùng](../docs/paper/iccies2027/facts.md).

## 2. Quyết định (decision log, ngày 2026-11-15)

Xem [decision log](../docs/project/decision_log.md), các mục:

| Giờ | Nội dung |
|---|---|
| 15:30 | Hạn lùi, mở rộng theo review |
| 15:45 | Tạp chí Q4; cần xác nhận = từ chối; bộ trích P(u) tất định; Test-4 48 họ |
| 16:30 | Dev v4 = Dev + Test-I + Test-II; Test-4 là tập kiểm định duy nhất |
| 17:30 | Phần thích nghi 24 ca; nháp quy tắc nhãn |
| 18:00 | Quy tắc nhãn v4 đóng băng |
| 18:20 | Test-4 niêm phong, nguồn gốc dữ liệu, bộ chấm biến đổi, lực thống kê, đăng ký trước (gatekeeping) |

## 3. Dữ liệu

| Nút | Đường dẫn | Ghi chú |
|---|---|---|
| Dev v4 | `data/adversarial/release_dev4/` | 168 họ, 1.960 fixture, Dev-val 42; dựng bằng `scripts/build_dev_pool_v4.py` |
| Quy tắc nhãn v4 | `data/adversarial/v3_authoring/labelling_rules_v4.md` | Đóng băng, sha256 `d0836dd9…` |
| Phiếu nhãn, errata | `data/adversarial/v3_authoring/dev4_labelling/`, `dev4_errata.csv` | Do mã sinh, có người rà; không báo κ |
| Dev v4.1 | `data/adversarial/release_dev4_1/` | Tập phát triển duy nhất; dựng bằng `scripts/build_dev4_1.py` |
| Test-4 | `data/adversarial/release_test4/` | Seal `1f9b0070…`, commit `a1711a6`; không đọc, không chạy trước khi đóng băng v3 |
| Hướng dẫn soạn | `data/adversarial/v3_authoring/AUTHORING_TEST4.md` | Bước A–D |

## 4. Đo và chấm

| Nút | File | Đo gì |
|---|---|---|
| Đo chi phí | `src/react_agent/evaluation/run_metrics_v1.py` | Token theo vai trò, lời gọi thêm, bước, chặn, xác nhận, che đáp án, chia thời gian |
| Runner | `scripts/run_v3_api_v2.py` | Dev v4/v4.1, kiểm seal, ghi `metrics.json` |
| Evaluator | `scripts/evaluate_v3_v2.py` | Chấm nguyên văn và biến đổi, chặn nhầm, tỉ lệ xác nhận, phân bố chi phí |
| Bộ chấm biến đổi | `src/react_agent/evaluation/transformed_leakage.py` | Base64, Hex, URL, tách ký tự, viết bằng chữ |
| Lượt cũ | `scripts/cost_from_traces_v1.py` | Bước, chặn, thời gian từ trace (không có token) |
| Lực thống kê | `scripts/power_analysis_test4.py` | McNemar chính xác, N = 48 |

Lệnh chạy: [runbook, mục Bản đồ](rebuild_a_runbook.md), dòng "v3: Dev v4.1 có đo chi phí".

## 5. Đang chạy

- Mốc A0, D2P2, P2, PRG × 3 mô hình mở trên Dev v4.1: 12 notebook, mỗi notebook một cấu hình
  ([sổ Kaggle](kaggle_resources.md) mục 15/11 23:50).
- Tự động: `build/kaggle/dev4_supervise.sh` (nối lại chuỗi, bật lại notebook hết 12 giờ, tắt keep-alive khi xong) và
  `build/kaggle/dev4_kaguard.sh` (bật lại keep-alive bỏ cuộc vì lỗi mạng). Theo dõi và resume: [bàn giao](handoff.md) mục "Đang làm".
- Tốc độ đo được (SHARDS=2): Qwen ~3,2–3,5, Gemma ~2,6–3, Llama ~1,8–2 ca/phút mỗi notebook, tức 10–18 giờ một cấu hình.
- Số tạm 15/11 23:50 (chỉ phần đã chạy, chưa có benign_auth, không dùng cho bài): ca tấn công gây hại Qwen A0 246/675,
  Qwen P2 34/702, Gemma A0 345/726; utility benign_plain 50–62 %; chặn nhầm 0; bộ chấm biến đổi chưa thêm ca nào so
  với nguyên văn. Cần xem max_steps (6–8 %) và model_error (2–3 %) của Qwen trước khi dùng cho H2.

## 6. Việc tiếp theo

1. Chấm và ghi số mốc Dev v4.1.
2. C1 chính sách ý định P(u), rồi C2, C3, ablation, đóng băng `final_config_v5`.
3. Chạy Test-4 một lần; vòng thích nghi nhắm vào v3 trên Dev-val; Gemini để cuối.

## 7. Luật không đổi

- Claude chỉ làm hạ tầng, số đếm và biên soạn; không viết hay đọc nội dung tấn công và nội dung Test.
- Không sửa runner, evaluator hay `release.py` đã ghim; không sửa v1, Test cũ, số liệu cũ.
- Máy hỏng pin: một tiến trình nặng, `nice -n 10`; không tự bật OmniRoute; không render PDF.
