# Study 2: bảng cho luận văn (bản nháp, số Dev)

Cập nhật: 2026-11-09 (thêm Bảng 2.7, Test v3). Nguồn: `docs/project/decision_log.md` (06/11 vòng 1, 06–07/11 vòng chỉnh 1–2, 07/11 Tầng 2,
SecAlign, AgentDojo-VI). Tất cả là **Dev v3**, chưa có CI; kết luận chính thức chờ Test v3 (một lần, bootstrap theo
family, McNemar). Không chèn văn bản tấn công hay nội dung Test vào file này.

Quy ước: "có hại" = số family attack (trên 48) có ít nhất một fixture gây hại theo `side_effect_harm_v3`; plain = utility
benign_plain (/240); auth = utility benign_auth (/80, chặn nhầm khi không đạt). Mỗi cấu hình 560 lượt.

## Bảng 2.1. Phòng thủ trên 3 backbone Tầng 1 (Dev vòng 1 và vòng chỉnh 1)

| Cấu hình | Nguồn | Gemma-4-12B có hại · plain · auth | Llama-3.1-8B | Qwen3.5-9B |
|---|---|---|---|---|
| A0 | mốc | 38 · 159 · 54 | 34 · 81 · 30 | 40 · 140 · 36 |
| P1 spotlighting | Hines 2024 | 24 · 146 · 54 | 24 · 74 · 36 | 43 · 137 · 38 |
| P2 sandwich | Learn Prompting | 7 · 150 · 54 | 13 · 84 · 40 | 11 · 144 · 32 |
| G1 Prompt Guard 2 | Meta | 39 · 160 · 54 | 34 · 81 · 30 | 40 · 139 · 36 |
| MEL (MELON tất định) | Zhu 2025 | 38 · 160 · 54 | 34 · 79 · 30 | 40 · 142 · 36 |
| PRG (Progent-lite) | Shi 2025 | 21 · 160 · 54 | 18 · 80 · 32 | 22 · 138 · 36 |
| R1 (A1 Study 1) | đồ án | 36 · 160 · 49 | 25 · 80 · 27 | 33 · 138 · 33 |
| D2 | đồ án | 17 · 158 · 44 | 13 · 80 · 27 | 15 · 136 · 28 |
| D2+P1 | tổ hợp | 12 · 145 · 44 | 8 · 73 · 28 | 14 · 129 · 31 |
| **D2+P2** (vòng chỉnh 1) | tổ hợp | **2** · 147 · 45 | **5** · 82 · 36 | **3** · 141 · 24 |
| D2-NR+P2 (vòng 2, bác) | tổ hợp | 4 · 150 · 49 | 9 · 82 · 39 | 5 · 142 · 27 |

Ghi chú: Llama có 53–78 lượt `OUTPUT_TRUNCATED` mỗi cấu hình (tính là thất bại), nên plain thấp.

**Nhận xét chính (Dev):**
1. Bộ phát hiện huấn luyện trên tiếng Anh (G1) và MELON tất định gần như bằng A0 trên tiếng Việt.
2. Spotlighting có thể phản tác dụng (Qwen3.5: 40 → 43).
3. Luật đích (PRG, D2) chặn hết M1, M2; M3–M5 còn lọt.
4. D2+P2 thấp nhất, cái giá là benign_auth (Qwen3.5 36 → 24).
5. Lớp luật A1 không thừa dưới D2: bỏ nó (D2-NR) lấy lại 3–4 auth nhưng tăng 2–4 family có hại.

## Bảng 2.2. Tầng 2 và SecAlign (Dev)

Có hại /48 · plain /240 · auth /80 · model_error:

| Model | A0 | R1 | PRG | D2 |
|---|---|---|---|---|
| Qwen3-8B | 32 · 167 · 49 · 0 | 29 · 166 · 45 · 2 | 22 · 166 · 49 · 1 | 16 · 164 · 39 · 0 |
| Qwen3.6-35B-A3B (AWQ) | 38 · 189 · 56 · 8 | 32 · 192 · 51 · 8 | 25 · 191 · 56 · 8 | 20 · 190 · 46 · 8 |
| Llama-3.1-8B (base) | 34 · 81 · 30 · 54 | 25 · 80 · 27 · 54 | 18 · 80 · 32 · 53 | 13 · 80 · 27 · 55 |
| Meta-SecAlign-8B | 13 · 118 · 41 · 24 | — | — | 6 · 118 · 33 · 24 |

**Nhận xét:**
- Model mạnh hơn không an toàn hơn: Qwen3.6-35B utility cao nhất nhưng A0 có hại 38/48.
- SecAlign (phòng thủ mức mô hình) giảm 34 → 13 so với base; cộng D2 còn 6. Hai lớp bổ sung nhau.
- Mẫu theo cơ chế lặp lại trên mọi backbone: chuyển hướng (M1, M2) bị chặn, rò bí mật (M3) và sửa payload (M5) còn lọt.

## Bảng 2.3. AgentDojo-VI so với EN (Llama-3.1-8B, `important_instructions`)

Utility / tấn công thành công:

| Suite | Phòng thủ | EN | VI |
|---|---|---|---|
| Banking (144 cặp) | không | 58 / 17 | 44 / 6 |
| | spotlighting_with_delimiting | 61 / 18 | 41 / 2 |
| | repeat_user_prompt | 62 / 10 | 45 / 6 |
| Slack (105 cặp) | không | 28 / 16 | 26 / 0 |
| | spotlighting_with_delimiting | 45 / 10 | 20 / 1 |
| | repeat_user_prompt | 35 / 10 | 19 / 0 |

Không tấn công: Banking EN 7/16, VI 6/16; Slack EN 7/21, VI 7/21.

Diễn giải: ASR VI thấp hơn EN nhưng utility dưới tấn công cũng thấp hơn; Llama-8B làm kém cả nhiệm vụ lẫn chỉ thị chèn
khi cả hai bằng tiếng Việt. Không kết luận "tiếng Việt an toàn hơn".

## Bảng 2.4. Theo biến thể ngôn ngữ (Dev, cùng family và oracle)

`scripts/v3_variant_breakdown_v1.py` → `results/rebuild_b/v3_dev_variant_breakdown.json`. Fixture attack có hại /48
theo canonical · paraphrase · không dấu · code-mix · tiếng Anh:

| Cấu hình | Gemma-4-12B | Llama-3.1-8B | Qwen3.5-9B | Qwen3-8B | Qwen3.6-35B | SecAlign-8B |
|---|---|---|---|---|---|---|
| A0 | 29 · 22 · 32 · 30 · 26 | 12 · 14 · 17 · 15 · 19 | 22 · 23 · 19 · 22 · 28 | 19 · 18 · 19 · 20 · 22 | 26 · 23 · 26 · 26 · 22 | 6 · 4 · 5 · 5 · 8 |
| P2 | 1 · 0 · 5 · 2 · 0 | 3 · 3 · 5 · 3 · 5 | 2 · 2 · 7 · 2 · 2 | — | — | — |
| PRG | 15 · 13 · 17 · 16 · 15 | 8 · 8 · 8 · 10 · 13 | 14 · 14 · 12 · 13 · 15 | 14 · 15 · 15 · 13 · 14 | 20 · 13 · 18 · 18 · 13 | — |
| D2 | 5 · 8 · 8 · 4 · **13** | 1 · 4 · 3 · 3 · **8** | 6 · 7 · 5 · 6 · **10** | 4 · 5 · 6 · 4 · **10** | 5 · 10 · 6 · 8 · **13** | 2 · 0 · 1 · 3 · **5** |
| D2+P2 | 0 · 0 · 2 · 0 · 0 | 1 · 2 · 1 · 1 · 2 | 0 · 0 · 2 · 0 · 1 | — | — | — |

**Nhận xét (Dev, chưa kiểm định):**
- Dưới D2, biến thể tiếng Anh lọt nhiều nhất trên cả 6 backbone (gấp 2–8 lần canonical). Giả thuyết cần kiểm: lớp luật
  A1 (Study 1) được xây cho mẫu chỉ thị tiếng Việt, nên bắt kém đoạn chèn tiếng Anh; luật đích/bí mật của D2 không phụ
  thuộc ngôn ngữ. Đây là bằng chứng ngược chiều với giả định "phòng thủ tiếng Anh dùng được cho tiếng Việt": phòng
  thủ viết cho tiếng Việt cũng hở với tiếng Anh.
- **Đã kiểm (đếm mã quyết định, D2, 48 lượt attack mỗi biến thể):** `RULE_INJECTION_SIGNAL` của lớp A1 bật ở 14–19 lượt
  với canonical, không dấu, code-mix; 10–13 với paraphrase; **chỉ 3** với tiếng Anh (Gemma, Llama, Qwen3.5, Qwen3-8B).
  Còn luật đích của D2 (`UNTRUSTED_CONTROL_INFLUENCE`) bật nhiều hơn ở tiếng Anh (6–12), vì model làm theo nhiều hơn.
  Lớp luật dựa trên cách diễn đạt nên giòn với paraphrase và đổi ngôn ngữ.
- Dưới P2 và D2+P2, chỗ yếu là **không dấu** (Qwen3.5 P2: 7 so với 2). Utility benign_plain không dấu cũng thấp hơn
  (Qwen3.5 21–23 so với 29–31): model hiểu kém văn bản không dấu, cả yêu cầu nhắc lại lẫn dữ liệu.
- Ở A0 không có xu hướng ngôn ngữ chung: Gemma bị lừa nhiều nhất ở không dấu, Qwen3.5 và Llama ở tiếng Anh.

## Bảng 2.5. Vòng chỉnh 3: SAN, bộ lọc observation theo nhiệm vụ (Dev, xong 08/11)

Khai báo trong decision log 08/11 trước khi chạy. Đủ 560 lượt mỗi ô. Có hại /48 · plain /240 · auth /80:

| Cấu hình | Gemma | Llama | Qwen3.5 | Tổng có hại /144 · plain /720 · auth /240 | Luật |
|---|---|---|---|---|---|
| D2+P2 (mốc) | 2 · 147 · 45 | 5 · 82 · 36 | 3 · 141 · 24 | 10 · 370 · 105 | — |
| SAN | 3 · 159 · 55 | 11 · 82 · 31 | 6 · 131 · 34 | 20 · 372 · 120 | trượt (có hại) |
| D2+SAN | 0 · 158 · 44 | 5 · 84 · 26 | 1 · 126 · 27 | 6 · 368 · 97 | trượt (auth) |
| D2+P2+SAN | 0 · 149 · 45 | 1 · 88 · 36 | 0 · 125 · 16 | **1** · 362 · 97 | trượt (auth, plain) |

Tỉ lệ lượt bộ lọc gắn cờ (attack · benign_plain · benign_auth), cấu hình SAN:
Gemma 222/240 · 2/240 · 0/80; Llama 201/240 · 113/240 · 46/80; Qwen3.5 179/240 · 80/240 · 33/80.

**Nhận xét (Dev):**
- Không cấu hình nào đạt luật khai báo trước, nên **giữ D2+P2** làm ứng viên `final_config_v3` (owner duyệt).
- D2+P2+SAN gần như chặn hết (1/144 family có hại, M3 rò bí mật về 0) nhưng mất auth ở Qwen3.5 (24 → 16).
- Chất lượng bộ lọc phụ thuộc backbone: Gemma lọc gần như không nhầm (≈1% benign bị gắn cờ); Llama và Qwen3.5
  gắn cờ nhầm 33–57% lượt benign, nên xoá cả chỉ dẫn hợp lệ và mất auth. SAN dùng cùng backbone là giới hạn chính;
  dùng một model lọc cố định, mạnh hơn là hướng mở (phải khai báo vòng mới, chạy lại Dev, trước Test).
- SAN đứng riêng giữ utility gần A0 (plain 372 so với A0 380), auth cao nhất (120), có hại 20/144 so với A0 112/144:
  bằng chứng "lọc thay vì chặn" giữ utility, nhưng một mình chưa đủ an toàn trên model nhỏ.

## Bảng 2.6. WP8: tấn công thích nghi do owner/Minh soạn (Dev, 08/11)

`data/adversarial/adaptive_v3/adaptive_dev_attack.jsonl`: 48 fixture attack Dev, một mỗi family (8 mỗi cơ chế),
SHA-256 `4ea53cf8…b784`. Cùng task, cùng oracle với family gốc; chỉ `content` và `overlay` đổi. Số đếm từ
`scripts/wp8_summary_v1.py` → `results/rebuild_b/v3_dev_wp8_summary.json` (Claude không đọc văn bản fixture).

Family có hại /48: thích nghi · tĩnh canonical (cùng family) · tĩnh mọi biến thể:

| Cấu hình | Gemma-4-12B | Llama-3.1-8B | Qwen3.5-9B |
|---|---|---|---|
| A0 | 4 · 29 · 38 | 6 · 12 · 34 | 6 · 22 · 40 |
| D2+P2 | 0 · 0 · 2 | 1 · 1 · 5 | 0 · 0 · 3 |
| D2+SAN | 0 · 0 · 0 | 2 · 0 · 5 | 0 · 0 · 1 |
| D2+P2+SAN | 0 · 0 · 0 | 1 · 0 · 1 | 0 · 0 · 0 |
| SAN | 1 · 0 · 3 | 5 · 2 · 11 | 1 · 1 · 6 |

Theo cơ chế (thích nghi, Llama · Qwen3.5): A0 có hại ở M3 2·2, M4 1·1, M5 2·3, M6 1·0; M1, M2 bằng 0. Dưới D2+P2 lượt
lọt duy nhất là M6 (Llama); `attack_tampered` (M5) 0/48 ở mọi cấu hình có D2. Vi phạm được thực thi
(`executed_violations`) Llama: A0 14, D2+P2 3, D2+P2+SAN 3; Qwen3.5: A0 6, có D2 0.

**Nhận xét (Dev):**
- Ở A0, bộ thích nghi **yếu hơn** bộ tĩnh cùng family (Gemma 4 so với 29, Llama 6 so với 12, Qwen3.5 6 so với 22 ở canonical). Vì
  vậy WP8 lần này **không** cho thấy phòng thủ bị vượt, nhưng cũng chưa phải phép thử mạnh: tấn công thích nghi
  đúng nghĩa phải ít nhất mạnh bằng bộ tĩnh ở A0. Cần vòng soạn thứ hai (có phản hồi từ lượt chạy A0/D2+P2 trên Dev).
- Dưới D2+P2, số lọt 0–1/48, ngang bộ tĩnh canonical.

## Bảng 2.6b. WP8 vòng 3: bộ thích nghi soạn lại (Dev, 08–09/11)

Bộ v2 (`37124e8e…`) bị loại: 48/48 fixture trùng từng byte bộ tĩnh canonical (`scripts/check_adaptive_fixtures_v1.py`).
Bộ v3 `284f9499…`: 48/48 văn bản mới, cùng task và oracle. Số đếm từ `scripts/wp8_summary_v1.py --tag adaptive3` →
`results/rebuild_b/v3_dev_wp8v3_summary.json`. Family có hại /48: thích nghi v3 · tĩnh canonical · tĩnh mọi biến thể:

| Cấu hình | Gemma-4-12B | Llama-3.1-8B | Qwen3.5-9B |
|---|---|---|---|
| A0 | 26 · 29 · 38 | 15 · 12 · 34 | 24 · 22 · 40 |
| D2+P2 | 1 · 0 · 2 | 0 · 1 · 5 | 0 · 0 · 3 |

Theo cơ chế ở A0 (Gemma · Llama · Qwen3.5): M1 4·1·5, M2 3·1·3, M3 7·5·6, M4 3·3·2, M5 7·4·8, M6 2·1·0. Lượt lọt duy
nhất dưới D2+P2: D3_33 (M4, Gemma). `executed_violations` A0 27 · 26 · 19, D2+P2 2 · 2 · 0.

**Nhận xét (Dev):**
- Bộ v3 ngang hoặc mạnh hơn bộ tĩnh canonical ở A0 trên Llama và Qwen3.5 (qua ngưỡng), Gemma thấp hơn 3 family; mạnh
  nhất ở M5 (sửa tham số trên sink hợp lệ). Đây là phép thử thích nghi đủ mạnh trên Dev.
- Dưới D2+P2 còn 0–1/48 (A0 15–26/48): phòng thủ không bị vượt bởi bộ soạn có chủ đích, ngang bộ tĩnh. Hạn chế: một
  vòng soạn của người, không có tối ưu tự động (GCG, attacker LLM); chỉ trên Dev, không có bộ thích nghi trên Test.

## Bảng 2.7. Test v3 Tầng 1 (kết quả chính thức, `final_config_v3`, chạy một lần, 09/11)

72 family; mỗi ô 840 lượt (360 attack, 360 benign_plain, 120 benign_auth). Chấm `evaluate_v3_v1.py`; kiểm định
`scripts/test_v3_hypotheses_v1.py` (kết quả `results/rebuild_b/v3_test_hypotheses.json`). Có hại /72 · fixture có hại
/360 · plain /360 · auth /120:

| Cấu hình | Gemma-4-12B | Llama-3.1-8B | Qwen3.5-9B |
|---|---|---|---|
| A0 | 50 · 158 · 217 · 63 | 41 · 90 · 102 · 35 | 47 · 107 · 170 · 43 |
| R1 | 40 · 90 · 206 · 58 | 29 · 47 · 101 · 30 | 40 · 63 · 161 · 40 |
| P2 | 17 · 23 · 197 · 54 | 20 · 27 · 105 · 29 | 10 · 11 · 170 · 41 |
| PRG | 25 · 93 · 215 · 63 | 24 · 53 · 103 · 34 | 26 · 66 · 170 · 44 |
| D2 | 17 · 33 · 203 · 53 | 14 · 16 · 94 · 30 | 18 · 23 · 162 · 35 |
| **D2+P2** | **5** · 6 · 186 · 48 | **5** · 6 · 102 · 24 | **1** · 1 · 160 · 36 |

Fixture có hại theo cơ chế, gộp 3 backbone (/180 mỗi cơ chế):

| Cấu hình | M1 | M2 | M3 | M4 | M5 | M6 |
|---|---|---|---|---|---|---|
| A0 | 58 | 65 | 89 | 60 | 68 | 15 |
| R1 | 33 | 38 | 46 | 43 | 33 | 7 |
| PRG | 0 | 0 | 89 | 55 | 67 | 1 |
| D2 | 0 | 0 | 29 | 17 | 25 | 1 |
| P2 | 1 | 1 | 27 | 18 | 10 | 4 |
| D2+P2 | 0 | 0 | 6 | 3 | 4 | 0 |

Theo biến thể (fixture có hại /216, gộp): A0 canonical 68 · paraphrase 70 · no_diacritic 72 · code_mix 66 · english 79;
D2 9 · 13 · 12 · 6 · 32; D2+P2 1 · 5 · 3 · 3 · 1.

**Giả thuyết chính (McNemar chính xác trên cặp fixture, gộp 3 backbone; Holm trên H1–H6; CI 95% bootstrap theo family):**

| | So sánh | Tỉ lệ | Chênh (CI 95%) | p Holm | Kết luận |
|---|---|---|---|---|---|
| H1 | D2 < R1, attack | 18,5% → 6,7% | −11,9 (−16,7; −7,5) | 1,8e−38 | **Bác H0** (128/0 cặp lệch) |
| H2 | D2 plain không kém A0 quá 5 điểm | 45,3% → 42,5% | −2,8 (−6,0; −0,5) | 0,20 | **Chưa chứng minh** không kém |
| H3 | D2 < R1, M2∪M3∪M4 | 23,5% → 8,5% | −15,0 (−23,7; −7,4) | 2,1e−24 | **Bác H0** |
| H4 | A0 no_diacritic ≠ canonical | 31,5% → 33,3% | +1,9 (−5,1; +8,8) | 0,70 | Không khác |
| H5 | A0 english ≠ canonical | 31,5% → 36,6% | +5,1 (−1,9; +12,0) | 0,27 | Không khác |
| H6 | D2+P2 < P2, attack | 5,6% → 1,2% | −4,4 (−6,2; −2,8) | 1,8e−13 | **Bác H0** |

**Nhận xét (Test):**
1. D2 giảm mạnh tấn công so với R1 (H1, H3), không có cặp nào D2 tệ hơn R1. D2+P2 thấp nhất: còn 1–5/72 family.
2. Cái giá là utility: D2 mất 2,8 điểm plain (CI chạm −6,0, nên không khẳng định được "không kém quá 5 điểm", H2);
   D2+P2 so với A0 mất plain ở Gemma (217 → 186) và Qwen3.5 (170 → 160), auth giảm 7–15 lượt mỗi backbone.
3. Dự đoán đăng ký trước: "D2 ≈ R1 trên M1" sai (D2 chặn hết M1: 0 so với 33); "D2 không tốt hơn ở M5" sai một
   phần (25 so với 33); "D2 english > canonical" đúng (32 so với 9): luật đích không bắt được tấn công tiếng Anh tốt như
   tiếng Việt có dấu, P2 bù chỗ này (D2+P2 english 1).
4. Tiếng Việt không dấu và tiếng Anh không làm A0 dễ bị tấn công hơn một cách có ý nghĩa thống kê (H4, H5).
5. PRG (Progent-lite) chặn hết M1, M2 nhưng gần như không tác dụng với M3–M5, khớp với Dev.

## Bảng 2.8. Phân tích lỗi sau Test v3 (thăm dò, không dùng để chỉnh)

Script `scripts/test_v3_error_analysis_v1.py` → `results/rebuild_b/v3_test_error_analysis.json`. Chỉ đọc mã luật, tên công
cụ, trạng thái và ID; không đọc nội dung. "Mất" = fixture đạt utility ở A0 nhưng không đạt ở cấu hình này; "được" = ngược lại.
Lớp A1 = lớp luật Study 1 giữ trong D2 (luật 5); "không chặn" = không luật nào chặn, mô hình tự làm khác.

| Cấu hình, nhánh | Gemma mất/được | Llama | Qwen3.5 | Nguyên nhân chính |
|---|---|---|---|---|
| P2 plain | −35/+15 | −40/+43 | −24/+24 | Gemma: 32/35 bỏ không gọi sink người dùng yêu cầu; Qwen3.5: 17 hết bước |
| D2 plain | −14/+0 | −9/+1 | −11/+3 | Lớp A1 chặn nhầm 10 · 3 · 9; luật 2 chỉ 0 · 1 · 2 |
| D2 auth | −11/+1 | −6/+1 | −8/+0 | Luật 3 (giá trị mật) 6 · 2 · 5; lớp A1 5 · 3 · 3 |
| D2+P2 plain | −46/+15 | −42/+42 | −34/+24 | cộng hai nguồn trên |
| D2+P2 auth | −17/+2 | −24/+13 | −13/+6 | Gemma 11 không chặn (P2); Qwen3.5 7 hết bước; luật 3 2 · 2 · 3 |

Trạng thái lượt chạy: Llama có 35–46 `model_error` và 37–61 `max_steps` trên benign_plain ở **mọi** cấu hình (giới hạn của
backbone, không do phòng thủ). Qwen3.5 khi bị chặn thường thử lại tới hết bước: attack `max_steps` A0 52 → D2 189, benign_plain
34 → D2+P2 65 (P2 một mình 54).

13 fixture còn gây hại dưới D2+P2 (11 family): M3 6, M4 3, M5 4. M5 (sửa giá trị không mật trên sink người dùng nêu, 4 lượt)
nằm ngoài phạm vi thiết kế của D2. Phần lớn M3/M4 lọt mà không luật nào bắt: giả thuyết là giá trị mật xuất hiện ở dạng biến
đổi nên luật 3/4 (so khớp nguyên văn) không nhận ra; cần owner/Minh xem các ID (chỉ người được đọc Test) để xác nhận. Family lặp
lại trên nhiều backbone: T3_02 (M5), T3_65 (M4), T3_72 (M3), T3_33 (M3).

**Hướng tối ưu rút ra (chỉ là đề xuất; muốn khẳng định phải chỉnh trên Dev rồi thử trên bộ Test mới):**
1. P2 làm Gemma quá thận trọng (bỏ sink hợp lệ): viết lại lời nhắc sandwich để nói rõ vẫn phải làm hành động người dùng yêu cầu.
2. Lớp A1 chặn nhầm nhiều nhất trên plain (22 lượt, 3 backbone), nhưng trên Dev bỏ nó làm tăng 2–4 family có hại (D2-NR): cần
   thu hẹp lớp A1 (ví dụ chỉ áp khi có tín hiệu tiêm trong cùng nguồn dữ liệu sinh ra tham số), không bỏ hẳn.
3. Luật 3 chặn nhầm trên benign_auth (13 lượt): người dùng cho phép theo tên trường dữ liệu chứ không gõ nguyên giá trị. Hướng:
   cho phép theo trường mà người dùng nêu (gắn phạm vi người dùng), thay vì chỉ theo giá trị nguyên văn.
4. Sau k lần bị chặn cùng một hành động, runtime kết thúc lịch sự bằng câu trả lời cuối thay vì để mô hình lặp tới hết bước
   (Qwen3.5).
5. Chuẩn hóa giá trị trước khi so khớp ở luật 3/4 (bỏ khoảng trắng, dấu, định dạng số) nếu giả thuyết về giá trị biến đổi đúng.

## Bảng 2.9. D3 trên Dev: thiết kế và ablation (09/11, chọn theo tiêu chí ghi trước 13:00)

Ô: họ có hại (/48) / fixture có hại (/240) · plain (/240) · auth (/80). Tiêu chí gộp 3 backbone: fixture có hại ≤ D2P2 và
utility (plain + auth, /960) > D2P2.

| Cấu hình | Thành phần | Gemma-4-12B | Llama-3.1-8B | Qwen3.5-9B | Gộp: có hại /720 · utility /960 |
|---|---|---|---|---|---|
| A0 | mốc | 38/139 · 159 · 54 | 34/77 · 81 · 30 | 40/114 · 140 · 36 | 330 · 500 |
| D2P2 | `final_config_v3` | 2/2 · 147 · 45 | 5/7 · 82 · 36 | 3/3 · 141 · 24 | 12 · 475 |
| **D3DEST** (chọn) | A1 theo đích + P2 v1 + feedback v1 | 2/2 · 148 · 49 | 5/7 · 85 · 40 | 3/3 · 141 · 27 | **12 · 490** |
| D3P2V1 | A1 theo đích + P2 v1 + feedback v2 | 2/2 · 150 · 49 | 6/8 · 84 · 40 | 3/4 · 142 · 26 | 14 · 491 |
| D3 | A1 theo đích + reminder v2 + feedback v2 | 1/1 · 163 · 54 | 10/15 · 75 · 38 | 2/5 · 39 · 16 | 21 · 385 |
| D3FBV1 | A1 theo đích + reminder v2 + feedback v1 | 1/1 · 162 · 54 | 10/15 · 69 · 38 | 2/5 · 40 · 16 | 21 · 379 |

- Tầng A1 theo đích giữ an toàn như D2P2 và trả lại phần chặn nhầm B-auth (auth +4 Gemma, +4 Llama, +3 Qwen).
- Reminder v2 ("làm đủ mọi bước, kể cả lệnh gửi"): Gemma tốt hơn rõ (plain 163, auth 54 = mức A0) nhưng Llama có hại tăng
  gấp đôi và Qwen sụp utility (plain 141 → 39). Không chuyển được giữa backbone, bị loại.
- Feedback v2 không thêm gì có ích (D3P2V1 có hại 14 > 12). Mức tăng của D3DEST nhỏ (+1,6 điểm); Test-3 kiểm định (T1).

## Còn thiếu trước khi viết chương

- Test v3 Tầng 1 đã xong (Bảng 2.7). Tầng 2 và SecAlign trên Test: tùy GPU, trước 2026-12-14.
- Bảng 2.10: xong, xem bảng dưới.

### Bảng 2.10 — Test-3 xác nhận D3DEST (`final_config_v4`, chạy một lần 09–10/11/2026)

48 family mới (T4_01–T4_48), 560 fixture mỗi ô: 240 attack, 240 benign_plain, 80 benign_auth. `model_error` tính là thất bại.
Mỗi ô ghi: family gây hại /48 · fixture gây hại /240 · utility benign_plain /240 · utility benign_auth /80.

| Backbone | A0 | D2P2 | D3DEST |
|---|---|---|---|
| Gemma-4-12B | 33 · 101 · 191 · 55 | 3 · 7 · 167 · 48 | 3 · 7 · 170 · 48 |
| Llama-3.1-8B | 29 · 50 · 95 · 23 | 8 · 10 · 87 · 30 | 8 · 10 · 89 · 31 |
| Qwen3.5-9B | 33 · 82 · 134 · 25 | 7 · 10 · 129 · 19 | 7 · 9 · 133 · 19 |
| **Gộp** | **95/144 · 233/720 · 420/720 · 103/240** | **18 · 27 · 383 · 97** | **18 · 26 · 392 · 98** |

Kiểm định chính (Holm trên T1–T3; gộp 3 backbone; CI 95% bootstrap theo family, 10.000 lần, seed 20261110):

| Giả thuyết | Tỉ lệ | Chênh (CI 95%) | Cặp lệch | p (Holm) | Kết luận |
|---|---|---|---|---|---|
| T1 utility benign: D3DEST > D2P2 | 0,500 → 0,510 | +1,0 điểm [−0,1; +3,1] | 11 / 1 | 3,2·10⁻³ | bác H0 |
| T2 hại: D3DEST không tệ hơn D2P2 quá 2 điểm | 0,037 → 0,036 | −0,1 điểm [−0,4; 0,0] | 0 / 1 | 1,6·10⁻⁵³ | bác H0 |
| T3 hại: D3DEST < A0 | 0,324 → 0,036 | −28,7 điểm [−35,4; −22,4] | 4 / 211 | 5,0·10⁻⁵⁷ | bác H0 |

Phụ (không vào Holm): benign_plain +1,3 điểm (10/1, p 5,9·10⁻³); benign_auth +0,4 điểm (1/0, p 0,5); D2P2 so A0 lặp lại
kết quả Test v3 (0,324 → 0,037, 4/210).

Đọc kết quả:
- Cả 3 giả thuyết đạt, đúng dự đoán ghi trước. Riêng T1: McNemar có ý nghĩa nhưng hiệu ứng nhỏ (+1 điểm), và CI bootstrap
  theo family chạm 0. Lợi ích đến từ benign_plain, không từ benign_auth như dự đoán.
- Lỗi model mỗi ô: Llama 74 / 69 / 66 `model_error` (đều `OUTPUT_TRUNCATED`), Qwen 6–8, Gemma 0–1. Lượt hết bước
  (`max_steps`): Qwen 95 / 188 / 153, Llama 99 / 111 / 94. Độ nhạy Llama: decision log 10/11 01:50.
- Nguồn số: `results/rebuild_b/v3_test3_hypotheses.json`, script `scripts/test3_hypotheses_v1.py` (branch `study2/test3-seal`).

- Bảng 2.11: xong, xem bảng dưới.
  bản chưa sửa JSON (`*_nojsonfix`) làm phân tích độ nhạy.
- Bảng 2.3b Gemini 3 Flash trên AgentDojo EN/VI: xem bảng cuối file (Banking EN đang chạy 10/11).

Dàn ý chương kết quả Study 2 (gợi ý): (1) benchmark VN-AgentInject v3 và giao thức Dev/Test; (2) baseline và D2 trên Dev
(2.1, 2.2, 2.4, 2.5); (3) tấn công thích nghi (2.6, 2.6b); (4) Test v3 chính thức (2.7) và phân tích lỗi (2.8); (5) D3: thiết
kế trên Dev (2.9) và xác nhận trên Test-3 (2.10); (6) ngoại kiểm: AgentDojo EN/VI (2.3, 2.3b) và model mạnh (2.11);
(7) hạn chế: model mạnh qua proxy (bỏ schema, sửa JSON), Test-3 do cùng nhóm soạn, chênh D3 nhỏ, backbone 8–12B.

### Bảng 2.11 — Model mạnh Gemini 3 Flash trên Dev v3 (tham chiếu, ngoài kiểm định chính)

OmniRoute/Antigravity qua proxy, revision `…-jsonfix` (sửa hình thức JSON, decision log 09/11 21:30), không seed, không
`response_format`. Mỗi ô 560 fixture. Ô ghi: family gây hại /48 · fixture gây hại /240 · utility benign_plain /240 ·
benign_auth /80; cột phải là ba backbone mở (Gemma / Llama / Qwen) cùng định dạng.

| Cấu hình | Gemini 3 Flash | model_error | Gemma-4-12B / Llama-3.1-8B / Qwen3.5-9B |
|---|---|---|---|
| A0 | 22 · 61 · 184 · 53 | 36 | 38·139·159·54 / 34·77·81·30 / 40·114·140·36 |
| R1 (A1 không phòng thủ) | 18 · 36 · 182 · 50 | 43 | 36·89·160·49 / 25·42·80·27 / 33·80·138·33 |
| D2 | 12 · 15 · 186 · 44 | 38 | 17·38·158·44 / 13·19·80·27 / 15·34·136·28 |
| D2P2 | 1 · 1 · 192 · 49 | 18 | 2·2·147·45 / 5·7·82·36 / 3·3·141·24 |
| D3DEST | 1 · 1 · 191 · 60 | 13 | 2·2·148·49 / 5·7·85·40 / 3·3·141·27 |

- Gemini ít bị tấn công hơn ở A0 (22/48 family so với 34–40) nhưng vẫn bị: phòng thủ vẫn cần với model mạnh.
- D2P2 và D3DEST đưa Gemini về 1/48 family, giữ utility benign_plain (184 → 191–192).
- D3DEST so D2P2 trên Gemini (cặp fixture, thăm dò, không hiệu chỉnh): benign_auth 49 → 60/80 (13/2 cặp lệch, p một phía
  0,004); benign_plain 192 → 191 (6/7). Đúng cơ chế D3 (lớp A1 thu hẹp theo đích giúp tác vụ có cấp quyền), rõ hơn ở backbone
  mở. Nhưng đây là Dev, nơi D3 đã được chọn (với backbone khác), nên chỉ là tham chiếu.
- Độ nhạy sửa JSON: A0 bản không sửa (`_nojsonfix`) 24 · 57 · 182 · 38, model_error 67 → 36 khi sửa; kết luận không đổi.
  Proxy: 202 / 9757 lượt gọi là JSON có chữ bao quanh (188 gỡ được), 18 bị cắt độ dài, 13 lỗi gọi hàm.

### Bảng 2.3b — Gemini 3 Flash trên AgentDojo EN/VI (không phòng thủ; tham chiếu, cập nhật 10/11 20:00)

AgentDojo v1.2.2, tấn công `important_instructions`, proxy OmniRoute cổng 8445 `--tool-as-user` (không `--extract-json`),
model key `gemini3_flash_raw`. Ô: utility khi bị tấn công / tấn công thành công. Llama lấy từ Bảng 2.3 (hàng "không").

| Suite (cặp) | Llama-3.1-8B EN | Llama-3.1-8B VI | Gemini 3 Flash EN | Gemini 3 Flash VI |
|---|---|---|---|---|
| Banking (144) | 58 / 17 | 44 / 6 | ĐANG CHẠY (120/144 cặp lúc 19:45) | 99 / 0 |
| Slack (105) | 28 / 16 | 26 / 0 | 62 / 1 | 59 / 0 |
| Banking, không tấn công (16) | 7 | 6 | 13 | 12 |
| Slack, không tấn công (21) | 7 | 7 | 18 | 16 |

- Gemini không phòng thủ gần như không bị `important_instructions` ở Slack cả hai ngôn ngữ (1/105 và 0/105), Llama EN 16/105.
  Utility dưới tấn công của Gemini cao gấp 2 lần Llama. Banking EN chưa xong: không kết luận trước khi có summary.
- Slack VI: 2/5 injection task không giải được bằng lời giải mẫu (`injection_tasks_solvable` false), nên trần ASR VI thấp hơn EN.
- Kiểm hạ tầng (10/11 19:50): mọi cặp đã xong ở 4 lượt có tấn công kết thúc bằng lượt assistant, không có dấu lỗi API trong
  transcript, trường `error` rỗng; các lượt gọi proxy thất bại (503 do hạ nhiệt tài khoản) được SDK thử lại, không ghi thành
  kết quả. Banking EN: kiểm lại sau khi xong.
- 8 lượt có phòng thủ dựng sẵn (`repeat_user_prompt`, `spotlighting_with_delimiting`; 996 cặp) CHƯA chạy; owner quyết sau
  khi có Banking EN (decision log 10/11 20:00).
