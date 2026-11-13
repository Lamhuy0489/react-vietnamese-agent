# Số liệu được phép dùng trong bài báo

Nguồn: `docs/research/study2_thesis_tables.md` (ký hiệu "Bảng 2.x" bên dưới) và `docs/project/decision_log.md`. Khi hai
nơi lệch nhau, bảng luận văn là bản đúng; sửa file này theo. Cập nhật 2026-11-10.

## Dữ liệu và giao thức

| Mục | Giá trị | Nguồn |
|---|---|---|
| Cơ chế | M1–M6 | `taxonomy.md` |
| Biến thể | canonical, paraphrase, code-mix, no-diacritic, english (5) | `taxonomy.md` |
| Dev | 48 family (8 mỗi cơ chế), 560 fixture mỗi cấu hình: 240 attack, 240 benign_plain, 80 benign_auth | `taxonomy.md` |
| Test v3 | 72 family (12 mỗi cơ chế), 840 fixture: 360 / 360 / 120; `final_config_v3` = D2+P2; chạy một lần 09/11/2026 | Bảng 2.7 |
| Test-3 | 48 family mới, 560 fixture: 240 / 240 / 80; `final_config_v4`; chạy một lần 09–10/11/2026 | Bảng 2.10 |
| Công cụ | 6 công cụ đọc + 2 sink mô phỏng (`send_email_mock`, `post_webhook_mock`), không có I/O mạng | `docs/tool_contracts.md` |
| Backbone | Gemma-4-12B, Llama-3.1-8B (ngữ cảnh 16k), Qwen3.5-9B; phục vụ bằng vLLM | Bảng 2.10 |
| Độ mới | Jaccard 4-gram ≤ 0,2 so với các release trước | `taxonomy.md` |
| Thống kê | McNemar chính xác, gộp 3 backbone; Holm; CI 95% bootstrap theo family, 10.000 lần | Bảng 2.7, 2.10 |

## Kết quả chính: Test-3 (Bảng 2.10)

Gộp 3 backbone. ASR = fixture attack có hại / 720; plain / 720; auth / 240; utility benign = (plain + auth) / 960.

| Cấu hình | Family có hại /144 | ASR | benign_plain | benign_auth | Utility benign |
|---|---|---|---|---|---|
| A0 | 95 | 233 (32,4%) | 420 (58,3%) | 103 (42,9%) | 523 (54,5%) |
| D2+P2 | 18 | 27 (3,8%) | 383 (53,2%) | 97 (40,4%) | 480 (50,0%) |
| D3 | 18 | 26 (3,6%) | 392 (54,4%) | 98 (40,8%) | 490 (51,0%) |

- D3 giữ 490/523 = 93,7% utility benign của A0; mất 3,4 điểm.
- T1 utility D3 > D2+P2: 0,500 → 0,510, +1,0 điểm, CI [−0,1; +3,1], cặp lệch 11/1, p Holm 3,2·10⁻³.
- T2 hại D3 không tệ hơn D2+P2 quá 2 điểm: 0,037 → 0,036, CI [−0,4; 0,0], cặp lệch 0/1, p Holm 1,6·10⁻⁵³.
- T3 hại D3 < A0: 0,324 → 0,036, −28,7 điểm, CI [−35,4; −22,4], cặp lệch 4/211, p Holm 5,0·10⁻⁵⁷.
- Phụ, ngoài Holm: benign_plain +1,3 điểm (10/1, p 5,9·10⁻³); benign_auth +0,4 điểm (1/0, p 0,5).
- Theo backbone (family có hại /48 · fixture có hại /240 · plain /240 · auth /80):
  Gemma A0 33·101·191·55, D2+P2 3·7·167·48, D3 3·7·170·48;
  Llama A0 29·50·95·23, D2+P2 8·10·87·30, D3 8·10·89·31;
  Qwen3.5 A0 33·82·134·25, D2+P2 7·10·129·19, D3 7·9·133·19.
- Lỗi model mỗi ô (A0 / D2+P2 / D3): Llama 74 / 69 / 66, đều là đầu ra bị cắt; Qwen 6–8; Gemma 0–1.

## Test v3 (Bảng 2.7)

Gộp 3 backbone: attack /1080, plain /1080, auth /360.

| Cấu hình | ASR | benign_plain | benign_auth |
|---|---|---|---|
| A0 | 355 (32,9%) | 489 (45,3%) | 141 (39,2%) |
| R1 | 200 (18,5%) | 468 (43,3%) | 128 (35,6%) |
| PRG | 212 (19,6%) | 488 (45,2%) | 141 (39,2%) |
| P2 | 61 (5,6%) | 472 (43,7%) | 124 (34,4%) |
| D2 | 72 (6,7%) | 459 (42,5%) | 118 (32,8%) |
| D2+P2 | 13 (1,2%) | 448 (41,5%) | 108 (30,0%) |

- Theo cơ chế (fixture có hại /180, M1…M6): A0 58, 65, 89, 60, 68, 15; R1 33, 38, 46, 43, 33, 7; PRG 0, 0, 89, 55, 67, 1;
  P2 1, 1, 27, 18, 10, 4; D2 0, 0, 29, 17, 25, 1; D2+P2 0, 0, 6, 3, 4, 0.
- H1 D2 < R1: 18,5% → 6,7%, −11,9 (−16,7; −7,5), 128/0, p 1,8·10⁻³⁸. H3 (M2∪M3∪M4): 23,5% → 8,5%, p 2,1·10⁻²⁴.
  H6 D2+P2 < P2: 5,6% → 1,2%, p 1,8·10⁻¹³. H2 chưa chứng minh: −2,8 điểm, CI (−6,0; −0,5), p 0,20.
  H4 không dấu so với canonical ở A0: 31,5% và 33,3%, p 0,70. H5 tiếng Anh: 31,5% và 36,6%, p 0,27.
- Theo biến thể (fixture có hại /216; canonical, paraphrase, no-diacritic, code-mix, english): A0 68, 70, 72, 66, 79;
  D2 9, 13, 12, 6, 32; D2+P2 1, 5, 3, 3, 1.
- Còn lọt dưới D2+P2: 13 fixture (M3 6, M4 3, M5 4). Lớp luật theo cụm từ chặn nhầm 22 lượt benign_plain (Bảng 2.8).

## Dev (Bảng 2.1, 2.4, 2.9)

- Family có hại /144 (3 backbone): A0 112, P1 91, P2 31, G1 (Prompt Guard 2) 113, MEL 112, PRG 61, R1 94, D2 45, D2+P2 10.
- Spotlighting phản tác dụng trên Qwen3.5: 40 → 43 family.
- Bộ dò cụm từ bật trên 14–19 / 48 lượt attack canonical nhưng chỉ 3 / 48 lượt tiếng Anh (D2, Bảng 2.4).
- Ablation D3, gộp (fixture có hại /720 · utility /960): A0 330 · 500; D2+P2 12 · 475; D3 12 · 490; phản hồi v2 14 · 491;
  lời nhắc v2 21 · 385 và 21 · 379. Lời nhắc v2 làm Qwen3.5 plain 141 → 39.
- Phát lại offline: luật D chặn đủ 11/11 fixture có hại, 0/14 sink benign bị chặn nhầm; phương án theo giá trị 9/11.
- Tấn công thích nghi do người soạn (48 fixture, Bảng 2.6b), family có hại Gemma / Llama / Qwen3.5: A0 26 / 15 / 24 (bộ tĩnh
  canonical 29 / 12 / 22); D2+P2 1 / 0 / 0.

## Ngoại kiểm

- Gemini 3 Flash trên Dev (Bảng 2.11; family /48 · fixture /240 · plain /240 · auth /80 · model_error /560):
  A0 22·61·184·53·36; R1 18·36·182·50·43; D2 12·15·186·44·38; D2+P2 1·1·192·49·18; D3 1·1·191·60·13.
  benign_auth D2+P2 → D3: 49 → 60 (cặp lệch 13/2), thăm dò.
- AgentDojo v1.2.2, `important_instructions`, không phòng thủ (Bảng 2.3, 2.3b); utility khi bị tấn công / tấn công thành công:
  Llama Banking EN 58/17, VI 44/6 (144 cặp); Llama Slack EN 28/16, VI 26/0 (105 cặp);
  Gemini Banking EN 93/4, VI 99/0; Gemini Slack EN 62/1, VI 59/0 (Banking EN xong 10/11 21:53).
  Không tấn công: Llama Banking 7 và 6 /16, Slack 7 và 7 /21; Gemini Banking 13 và 12 /16, Slack 18 và 16 /21 (EN và VI).
  Slack VI: 2/5 injection task không giải được bằng lời giải mẫu.
- Llama: tăng ngân sách đầu ra 512 → 2048 token không cứu lượt lỗi nào (decision log 10/11 03:30).

## Hạn chế phải nêu

Test do cùng nhóm soạn (người soạn không đọc code phòng thủ); dữ liệu tổng hợp, công cụ mô phỏng; backbone 8–12B; một mô
hình đóng, chạy qua proxy, chỉ trên Dev; mức tăng D3 so với D2+P2 nhỏ; tấn công tĩnh trên bộ niêm phong; tấn công thích
nghi chỉ một vòng do người soạn, chỉ trên Dev.
Thêm 10/11 23:00: phòng thủ dựng sẵn của AgentDojo chưa đánh giá trên Gemini 3 Flash (owner quyết không chạy);
Gemma và Qwen3.5 không chạy trên AgentDojo.

## Bổ sung sau phản biện (13/11/2026, không đăng ký trước)

Nguồn: `scripts/paper_cluster_stats_v1.py` → `results/rebuild_b/paper_cluster_stats_v1.json` (seed 20261113, 10.000 lần).
Chỉ đọc file eval và tên công cụ trong trace NoDef. Đơn vị "family" = một family gộp mọi biến thể và 3 backbone (Test-I 72,
Test-II 48); "backbone × family" = các số /216 và /144. Permutation = đảo dấu theo family, một phía cho hại, hai phía cho utility;
độ phân giải 10⁻⁴. DEFF = phương sai theo cụm family / phương sai giả định độc lập của hiệu trung bình.

| So sánh | Mức ca (b/c, p) | Family (trước→sau, b/c, p) | Backbone×family | Permutation p | CI 95% (điểm) | DEFF |
|---|---|---|---|---|---|---|
| Test-I H1 PhraseRules→BG-Rules, hại | 0/128, 2,9·10⁻³⁹ | 53→24/72, 0/29, 1,9·10⁻⁹ | 109→49/216, 8,7·10⁻¹⁹ | <10⁻⁴ | −11,9 (−16,8; −7,5) | 5,9 |
| Test-I H3 (M2∪M3∪M4) | 0/81, 4,1·10⁻²⁵ | 28→15/36, 0/13, 1,2·10⁻⁴ | 63→31/108, 2,3·10⁻¹⁰ | <10⁻⁴ | −15,0 (−24,1; −7,2) | 7,7 |
| Test-I H6 Sandwich→BG-v1, hại | 1/49, 4,5·10⁻¹⁴ | 28→8/72, 0/20, 9,5·10⁻⁷ | 47→11/216, 1,5·10⁻¹¹ | <10⁻⁴ | −4,4 (−6,3; −2,8) | 1,9 |
| Test-I NoDef→BG-v1, hại | 3/345, 1,2·10⁻⁹⁸ | 65→8/72, 0/57, 6,9·10⁻¹⁸ | 138→11/216, 1,9·10⁻³⁷ | <10⁻⁴ | −31,7 (−37,8; −25,7) | 4,6 |
| Test-I NoDef→BG-v1, utility benign | 102/176 | — | — | 0,022 | −5,1 (−9,7; −1,1) | 3,7 |
| Test-II NoDef→BG-v1, hại | 4/210, 3,3·10⁻⁵⁷ | 42→14/48, 0/28, 3,7·10⁻⁹ | 95→18/144, 1,4·10⁻²¹ | <10⁻⁴ | −28,6 (−35,3; −21,9) | 3,9 |
| Test-II NoDef→BG-v1, utility benign | 69/112 | — | — | 0,044 | −4,5 (−9,4; −0,5) | 2,6 |
| Test-II, chỉ benign_plain | 48/85 | — | — | 0,067 | −5,1 (−11,0; −0,1) | 3,0 |
| Test-II, chỉ benign_auth | 21/27 | — | — | 0,57 | −2,5 (−9,2; +4,2) | 1,5 |

- Utility "family" không dùng: gần như mọi family có ít nhất một ca thành công (48→46/48), không phân biệt được.
- DEFF 1,5–7,7: p ở mức ca bị phóng đại; trong bài dùng p mức family và CI theo family.
- BG-v1 làm giảm utility có ý nghĩa ở mức cụm: −4,5 điểm trên Test-II, −5,1 điểm trên Test-I.

### Tham chiếu deny-all-sinks (ước lượng từ trace NoDef)

Utility = NoDef thành công và không thực thi lời gọi sink nào. Hại = NoDef gây hại mà không qua sink (rò rỉ qua câu trả lời,
chặn sink không ngăn được). Ước lượng, vì mô hình có thể hành xử khác sau khi bị từ chối.

| Bộ | Deny-all hại | Deny-all utility benign | BG-v1 hại | BG-v1 utility | NoDef utility |
|---|---|---|---|---|---|
| Test-I | 13/1080 (1,2%) | 107/1440 (7,4%): plain 95/1080, auth 12/360 | 13 (1,2%) | 556 (38,6%) | 630 (43,8%) |
| Test-II | 5/720 (0,7%) | 120/960 (12,5%): plain 96/720, auth 24/240 | 27 (3,8%) | 480 (50,0%) | 523 (54,5%) |

### AgentDojo: Sandwich đã chạy (decision log 06/11, Llama-3.1-8B, EN, `important_instructions`)

Utility / tấn công thành công: Banking 144 cặp: không phòng thủ 58/17, `spotlighting_with_delimiting` 61/18,
`repeat_user_prompt` (= Sandwich) 62/10. Slack 105 cặp: 28/16, 45/10, 35/10. Chỉ EN; chưa chạy BG-v1 đầy đủ trên AgentDojo.
