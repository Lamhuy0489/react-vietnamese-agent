# Bài BrokerGuard v3: mục lục làm việc

Viết ngày 2026-11-19, sửa lần 2 cùng ngày (bỏ tên phiên bản, giảm mã, chống tràn lề). **Rút gọn còn tối đa 15 trang ngày
2026-11-20** theo yêu cầu owner (bản biên dịch 23 trang ở `pdf/agent_injection_vn.pdf`; bản dài nằm ở commit `6814b3a`).
Bài duy nhất của đồ án; bài ICCIES cũ ở `../iccies2027/` không nộp. Hai bản song song, cùng cấu trúc, bảng, hình, nhãn
tham chiếu và số:

- `latex/`: bản tiếng Việt để đọc (số kiểu Việt: 32,1\%; 1.960).
- `latex_en/`: bản tiếng Anh (chính tả Anh-Anh, số kiểu Anh: 32.1\%; 1,960; tóm tắt khoảng 210 từ). Font T5 vì Mục 4 trích
  vài từ phủ định tiếng Việt. Sửa nội dung thì sửa cả hai bản. Lời văn tiếng Anh viết gọn hơn bản dịch sát vì chữ Anh
  chiếm chỗ hơn chữ Việt khoảng 9\%.

## Định dạng và biên dịch

| | |
|---|---|
| Template | Springer LNCS (`llncs.cls` 2.26, `splncs04.bst`), giống bài ICCIES cũ |
| Độ dài | Tối đa 15 trang kể cả tài liệu tham khảo. Bản Việt biên dịch 20/11 (đã bật Pareto) dư 2 dòng sang trang 16; sau lượt soát văn phong và cắt, ước lượng bản Việt khoảng 14,8 trang (bật Pareto), bản Anh khoảng 14,7 trang (tắt Pareto). Ước lượng đã hiệu chỉnh +0,19 trang theo lần biên dịch đó |
| Biên dịch | Overleaf: zip cả thư mục `latex/` (hoặc `latex_en/`), main = `main.tex`, pdfLaTeX. Lỗi font T5 thì đổi sang XeLaTeX (hướng dẫn ở đầu `main.tex`) |
| Hình | Hình 1 (kiến trúc) và Hình 2 (Pareto, tùy chọn) vẽ bằng TikZ/pgfplots trong `.tex`, Overleaf tự vẽ. Không render hình hay PDF trên máy |
| Hình Pareto | Công tắc `\ifpareto` ở `main.tex`. Bản Việt: BẬT (owner chọn). Bản Anh: TẮT vì chữ Anh dài hơn khoảng 0,25 trang, bật thì sát 15 trang; chỉ bật khi bản Anh biên dịch ra dưới khoảng 14,6 trang |
| Tiêu đề | BrokerGuard: Intent-Aware Authorisation and Value-Level Flow Control Against Indirect Prompt Injection in Vietnamese LLM Agents (owner có thể đổi) |
| Tài liệu tham khảo | 19 mục (bản dài 25). Bỏ BIPIA, Nasr 2025, Tramèr 2020, Dwork 2015, Recht 2019, Holm 1979. Giữ FIDES, design patterns và Liu et al. vì phản biện 3 (`phan bien3.md`) coi việc cắt chúng là suy giảm |
| Cỡ chữ bảng | `llncs.cls` đặt `\footnotesize` bằng `\small`, nên bảng in ở 9 pt, dòng 11 pt. `tabular*` rộng hơn khổ sẽ tràn lề mà `adjustbox` không thu được (Bảng 1 bản 20/11 tràn 1 cm); bảng chữ dùng `tabularx`, bảng số `tabular*` chỉ khi bề rộng tự nhiên đo ở 9 pt nhỏ hơn 346 pt |
| Kiểm tĩnh | Ngoặc, môi trường, `\ref`, `\cite`, dấu `%` sau số, chấm phẩy, "chúng tôi"/"we" trong lời văn, số liệu hai bản khớp nhau: đã kiểm bằng script (20/11), chưa biên dịch thật |

## Bản 15 trang: đã cắt gì (20/11)

Không bỏ kết quả hay luận điểm nào. Những gì bị cắt hoặc chuyển chỗ:

- **Bảng và hình.** Bảng chi phí theo mô hình thành hai câu ở Mục 7 (đoạn chi phí). Bảng Gemini (bảng 6a cũ) thành một
  đoạn văn ("Tổng quát hóa"). Hình theo cơ chế (Hình 3 cũ) và bảng thích nghi gộp thành Bảng 4. Bảng con H1–H4 dưới Bảng 3
  thành lời văn. Bảng 1 và 2 rút lời trong ô (nguyên nhân lọt nằm ở Mục 1). Hình 1 bỏ chú giải trong hình (chú thích đã
  nêu màu) và hạ đáy khung. Hình 2 bỏ chú giải (che nhãn Sandwich) và thành tùy chọn.
- **Bố cục.** Mục 7 dùng tiêu đề đoạn thay tiểu mục. Mục 8 gộp "Chi phí tiện ích" với "Ngôn ngữ", "Mối đe dọa với tính
  hợp lệ" với "Hạn chế". Bỏ `placeins [section]` (rào ở mỗi mục để lại nửa trang trống ở trang 18 bản 23 trang).
- **Lời văn.** Bỏ câu lặp số đã có trong bảng, bỏ đoạn về biến thể C1a (2 lên 5 quỹ đạo gây hại trên phần kiểm định), bỏ
  vi đo dựng P(u) 496 µs, bỏ tên sáu công cụ đọc, bỏ câu về kiểm tra phát lại (800 lần), bỏ câu về nhãn độ nhạy cảm của
  tập phát triển được gắn lại, bỏ ví dụ "dùng/đừng" khi có dấu, bỏ hướng tiếp theo "nhiều lượt" và "theo dõi biến đổi ngoài (A4)".
- Muốn lấy lại đoạn nào: `git show 6814b3a:docs/paper/brokerguard_v3/latex/sections/<file>.tex` (hoặc `latex_en/`).

## Góp ý owner lần 1 trên bản 15 trang (20/11, bản Việt; bản Anh làm sau)

- Bảng 3: Q, G, L tách thành ba cột số căn phải dưới nhóm "Mô hình" (dấu chấm giữa làm số không thẳng hàng). Bảng 4: Q, G,
  L của bộ 1 và hai số của bộ 2 cũng tách cột.
- Bảng 1 tràn lề: đổi sang `tabularx`, cột mô tả là X, rút vài mô tả ("Như trên, đích được che giấu", "Đổi giá trị người
  dùng đã nêu", "Đích chỉ được nhắc tới hoặc bị cấm").
- Tóm tắt, Mục 1, 7, 8, 9: diễn đạt kết quả so với luật so khớp chuỗi theo hướng tích cực nhưng trung thực (chặn thêm bốn
  trong sáu họ, mỗi họ bởi đúng thành phần, không lọt họ mới, cùng chiều trên ba mô hình; khẳng định thống kê cần tập kiểm
  thử lớn hơn). Tiêu đề đoạn thảo luận đổi thành "Lực thống kê của kiểm định chính". Sửa câu kết luận cũ nói quá ("mỗi họ
  mà luật so khớp chuỗi để lọt đều bị chặn", thật ra 4 trong 6 họ).
- Nửa trang trống: bật Hình Pareto ở bản Việt.
- Việc còn lại cho bản Anh: làm y hệt các mục trên, viết gọn thêm khoảng 0,25 trang, rồi bật Pareto.

## Lượt 2 (20/11): soát văn phong, giữ 15 trang, đồng bộ bản Anh, bỏ chữ đỏ

- Văn phong (bản Việt rồi bản Anh): bớt nối vế bằng "còn" và "tức"; tách câu dài nhiều ngoặc; thay từ dịch sát hoặc
  khẩu ngữ ("đi thẳng vào", "chạy thật", "chấm offline", "bản giả", "kênh tuồn", "chỗ hở"); "cưỡng chế" thành "thực thi
  chính sách"; không dùng đại từ "họ" cho kẻ tấn công (trùng thuật ngữ "họ tấn công"). Sửa logic: "không sửa được u,
  prompt, broker" áp dụng cho mọi kẻ tấn công, không chỉ vòng thích nghi.
- Cắt để giữ 15 trang (không bỏ kết quả chính): câu theo biến thể ngôn ngữ, số ca cần xác nhận của Gemini, câu token so
  với khi không phòng thủ, số ca theo loại hại (136, 54, 79) thay bằng câu so sánh hai cấu hình, câu kiểm hash mỗi lần
  chạy, câu "báo lại lời gọi bị từ chối" (Hình 1 có), câu lực 91\% chuyển từ Mục 6 sang Mục 8. Chú thích Bảng 1, 4, 5 và
  Hình 2 ngắn lại; Bảng 2 nhãn giả định viết tắt; trục Hình 2 bản Việt 3,6 cm (nhãn BrokerGuard một dòng).
- Chữ đỏ: khối tác giả thành "Tác giả ẩn danh / Đơn vị ẩn danh" (bản Anh "Anonymous Authors / Anonymous Institution"),
  bỏ lệnh `\todo`. Nơi nộp không ẩn danh thì điền tên thật.
- Bản Anh: làm y hệt mọi thay đổi lượt 1 và lượt 2; Bảng 3 tiêu đề hai dòng ("Families (/48)", "Dev. set (/504)") để
  vừa khổ ở 9 pt.

## Lượt 3 (20/11): theo bài tham khảo, bớt ký hiệu, chú thích ngắn; bản Anh bật Hình 2 với [H]

- Góp ý owner (tham khảo bài lượng tử trong `pdf/`): Gemini chỉ ghi là mô hình đóng của Google, không "proxy"; bớt ngoặc
  chứa ký hiệu; tác hại viết bằng lời, ký hiệu dồn về Mục 5; câu mở đầu mục và câu nối giữa các đoạn; chú thích bảng,
  hình ngắn; khối tác giả là chỗ trống để owner tự điền ("Tác giả 1", "Author 1"); bỏ dấu * sau MELON, Progent (Mục 6
  nêu là bản cài lại).
- Bản Việt: viết lại 9 mục, rút chú thích, tắt Pareto (ước lượng khoảng 14,7 trang). Còn vài sửa nhỏ đã soạn nhưng chưa
  áp vì owner bảo sửa bản Anh trước: câu mở Mục 7 và 8, câu lực kiểm định ở Mục 8, chú thích Bảng 5 nêu ba cấu hình của
  cột cuối, câu chặn mọi sink nêu là ước tính.
- Bản Anh (lượt 3b, chỉ sửa bản Anh): soát câu và từ nối toàn bài; câu mở Mục 7 và 8; câu H1 nêu lý do chưa đạt và trỏ
  tới Mục 8; câu lực kiểm định sửa lại (câu cũ ngụ ý chặn hết vẫn không đủ, sai vì 5 và 0 cặp lệch đã cho p = 0,031);
  chú thích Bảng 1, 3, 5 và Hình 2 ngắn lại, Bảng 3 nêu Q, G, L là mô hình nào, Bảng 5 nêu lại ba cấu hình của cột "No
  attack"; câu chặn mọi sink ghi là ước tính từ quỹ đạo khi không phòng thủ.
- Hình 2 bản Anh: `\paretotrue`, `[H]` (gói `float`), đặt ngay sau đoạn "Main results" để hình lên trang 10, cạnh chỗ
  trích dẫn đầu tiên, thay vì nằm dưới Bảng 3 ở trang 11. `[H]` không trôi: nếu đoạn trước hình kết thúc sát cuối
  trang, hình sang trang sau và để trống phần cuối trang. Khi đó dời dòng `\ifpareto\input{images/fig2_pareto}\fi` ở
  `sections/07_results.tex` lên hoặc xuống một đoạn.
- Số trang bản Anh: bản owner biên dịch lúc 05:00 (đã bật Hình 2) đúng 15 trang, trang cuối kín. Lượt 3b cắt khoảng 10
  dòng (câu trùng, chú thích, câu Sandwich lặp ở Mục 4), ước lượng còn khoảng 14,8 trang.

## Ước lượng trang (không có TeX trên máy)

Script ở scratchpad của phiên 20/11 (không lưu): lấy chữ hiển thị của từng đoạn từ nguồn LaTeX, tính độ rộng bằng metric
font cmr10 (`fontTools` + `cmr10.ttf` của matplotlib), chia cho bề ngang dòng 345,8 pt; cộng tiêu đề mục 40 pt, tiêu đề
đoạn 12 pt, bảng/hình theo chiều cao đo trên PDF cũ, 25,7 pt mỗi tài liệu. Kiểm trên bản 23 trang: 594 dòng ước lượng so
với 593 dòng thật, tổng 21,45 trang so với 21,48 trang (không tính chỗ trống do đặt bảng). Sai số còn lại chủ yếu ở chỗ
trống khi đặt bảng/hình (0–0,5 trang), nên giữ ước lượng dưới khoảng 14,5 trang.

## Nguồn số liệu

Mọi con số lấy từ [`../iccies2027/facts.md`](../iccies2027/facts.md), chủ yếu các mục:

- "Bài v3 ... Test-4 dưới final_config_v5" (bảng chính, H1–H4, theo cơ chế, loại hại, biến thể, bằng chứng mức ca, hạn chế);
- "Cột tham khảo Gemini 3 Flash trên Test-4", "Baseline bổ sung trên Test-4", "Baseline bổ sung trên Dev v4.1";
- "Vòng thích nghi nhắm v3 trên Dev-val", "AgentDojo: bảng đầy đủ mọi lượt", "AgentDojo: BrokerGuard v3";
- "Bổ sung cho bài v3" (ASR mức ca, tiện ích dạng số ca, Dev P2/PRG, QA của Test-4, bằng chứng phát triển, chi phí theo
  mô hình, tài liệu mới). ASR mức ca sinh bằng `scripts/paper_v3_case_counts_v1.py`.

Mỗi file bảng và hình có comment đầu file ghi nguồn của từng số. Số nào không có trong facts.md thì không viết. Bản 15
trang không thêm số mới.

## Cấu trúc

| File | Nội dung |
|---|---|
| `latex/main.tex`, `latex_en/main.tex` | Preamble, macro tên gọi (đổi một dòng là đổi cả bài), công tắc `\ifpareto`; bản Việt có tên định lý tiếng Việt |
| `latex_en/` | Bản tiếng Anh: cùng tên file, cùng nhãn `\label` với `latex/` |
| `latex/sections/00_abstract.tex` … `09_conclusion.tex` | Tóm tắt, giới thiệu, liên quan, mô hình đe dọa, phương pháp, mô hình hình thức, giao thức, kết quả, thảo luận, kết luận |
| `latex/tables/tab1_mechanisms.tex` | Bảng 1: sáu cơ chế, số ca lọt qua luật chuỗi + Sandwich ở giai đoạn đầu, thành phần xử lý |
| `latex/tables/tab2_proven.tex` | Bảng 2: thuộc tính chứng minh và thuộc tính thực nghiệm |
| `latex/tables/tab3_main.tex` | Bảng 3: 13 cấu hình trên tập kiểm thử và cột tập phát triển |
| `latex/tables/tab4_mechres.tex` | Bảng 4: họ bị hại theo cơ chế, ablation, hai bộ tấn công thích nghi |
| `latex/tables/tab5_agentdojo.tex` | Bảng 5: AgentDojo |
| `latex/images/fig1_architecture.tex` | Hình 1: kiến trúc (TikZ) |
| `latex/images/fig2_pareto.tex` | Hình 2: đánh đổi an ninh và tiện ích (pgfplots), chỉ hiện khi `\paretotrue` |
| `latex/refs.bib` | 19 mục, đều được trích (kiểm bằng script 20/11) |

## Bảng đổi tên (log, decision log → bài báo)

Bài là bài mới hoàn toàn (19/11, owner): không dùng tên phiên bản (v1, v2, v3, BG-Base, "phiên bản trước") và không
đánh số tập kiểm thử (Test-I/II/III). Cấu hình luật chuỗi được trình bày là BrokerGuard bỏ cả ba thành phần. Hai tập
niêm phong cũ được kể là "giai đoạn đầu của nghiên cứu này", nay đã gộp vào tập phát triển.

| Log | Bài tiếng Việt | Bài tiếng Anh | Macro |
|---|---|---|---|
| V3P2 (v3) | BrokerGuard | BrokerGuard | `\ours` |
| D2P2 (v1, `final_config_v3`) | luật chuỗi + Sandwich | string rules + Sandwich | `\strSand`, `\StrSand` |
| D2 | luật chuỗi | string rules | `\strRules`, `\StrRules` |
| R1 | luật cụm từ | phrase rules | `\phrRules`, `\PhrRules` |
| A0 | không phòng thủ | no defence | `\noDef`, `\NoDef` |
| P1, P2, G1, MEL, PRG | Spotlight, Sandwich, PromptGuard, MELON\*, Progent\* | như cột trái | `\cSpot` … `\cProg` |
| C1 / C2 / C3 | chính sách ý định / nhãn mức giá trị / ghim tham số | intent policy / value-level labelling / parameter pinning | `\pOne` … (tên), `\cOne` … (mã) |
| V3P2-C1/-C2/-C3 | BrokerGuard bỏ C1/C2/C3 | BrokerGuard without C1/C2/C3 | |
| D2 luật 2/3/4, lớp A1 | luật đích theo chuỗi con / luật luồng theo nhãn nguồn / luật che câu trả lời / luật tín hiệu chèn lệnh | substring destination rule / source-label flow rule / answer redaction rule / injection-signal rule | `\rDest` … `\rSig` |
| Dev v4.1 (168 họ), Dev-train/Dev-val | tập phát triển, phần huấn luyện / phần kiểm định | development set, training / validation part | `\dev` |
| Test-4 (`T5_*`) | tập kiểm thử | test set | `\test` |
| Test v3 / Test-3 | hai tập kiểm thử của giai đoạn đầu (72 và 48 họ) | the two test sets of the early stage | |
| 24 ca `adaptive_test4` / 42 ca `adaptive_v3target` | bộ thích nghi thứ nhất / thứ hai | first / second adaptive set | |
| M1…M6 | ER, CR, SL, AL, PT, US (chỉ trong bảng) | như cột trái | `\mER` … |

**Quy tắc dùng mã:** trong lời văn dùng tên đầy đủ. Mã C1–C3 chỉ ở chỗ định nghĩa (Mục 4), trong bảng và hình. H1–H4,
(A1)–(A5), (G1)–(G4) giữ vì kiểm định và chứng minh tham chiếu tới chúng. Mã cơ chế chỉ trong bảng.

**Chống tràn lề:** mọi bảng và hình bọc trong `adjustbox{max width=\textwidth}` (vừa khổ thì giữ nguyên, rộng hơn thì
tự thu vừa); `\emergencystretch=3em` để chữ đơn cách không thò ra lề.

## Quy tắc khi sửa

- Văn phong học thuật, khách quan: không "chúng tôi", "ta"; dùng "bài báo", câu bị động hoặc hệ thống làm chủ ngữ.
- Câu ngắn và vừa, không chấm phẩy trong lời văn, không gạch dài. Tránh khuôn liệt kê máy móc ("Thứ nhất… Thứ tư"),
  câu tóm lại kiểu "Nói cách khác", từ sáo ("đóng vai trò then chốt", "vượt trội").
- Mã chỉ ở chỗ cần thiết (xem "Quy tắc dùng mã" ở trên). Không nêu mã họ của Test, không trích văn bản tấn công.
- Không dùng tên phiên bản; mọi so sánh với luật chuỗi gọi là "luật chuỗi + Sandwich" (BrokerGuard bỏ cả ba thành phần).
- H1 báo trung thực (không đạt, hiệu ứng sàn). So sánh với baseline là khám phá. Gemini là cột tham khảo, không kiểm định.
- Tập kiểm thử ghi là "sinh tự động từ đặc tả, hai thành viên rà soát", không báo κ (decision log 2026-11-15 18:20).
- Mỗi lần sửa số: sửa facts.md trước, rồi bảng, hình, lời văn. Không chạy regex đổi dấu thập phân trên file hình.
- Giới hạn 15 trang: thêm gì thì bớt tương ứng ở cả hai bản; bản tiếng Anh dài hơn nên là bản quyết định.

## Việc owner cần làm

1. Biên dịch cả `latex/` và `latex_en/` trên Overleaf, kiểm số trang (≤ 15 kể cả tài liệu tham khảo) và báo lỗi nếu có.
   Tải PDF về `pdf/` để phiên sau đọc bằng PyMuPDF.
2. Nếu còn chỗ (dưới khoảng 14,6 trang), cân nhắc bật Hình Pareto (`\paretotrue`). Nếu vượt 15 trang, ứng viên cắt tiếp:
   câu ví dụ ở đoạn chính sách ý định (Mục 4), các giá trị $p$ khám phá (Mục 7), đoạn Gemini thành một câu.
3. Đọc bản tiếng Việt, góp ý nội dung và văn phong.
4. Chốt nơi nộp (tạp chí Q4) và template, tiêu đề, tác giả, đơn vị, email (các ô `\todo` màu đỏ). Tên tác giả thật có thể
   thêm vài dòng ở trang 1.
5. Nếu nơi nộp cấm văn bản do AI sinh, owner tự viết lại lời văn tiếng Anh dựa trên `latex_en/`.

## Kiểm trước khi nộp

- [ ] Biên dịch không lỗi, không cảnh báo overfull đáng kể, tối đa 15 trang.
- [ ] Tóm tắt 150–250 từ (bản tiếng Anh, hiện khoảng 210); 3–5 từ khóa.
- [ ] Xóa mọi `\todo` và định nghĩa `\todo` (bản tiếng Anh không có khối tên định lý tiếng Việt).
- [ ] Hình đọc được khi in đen trắng (hình dạng điểm, độ dày viền, nét đứt đã có).
- [ ] Kiểm lại quy định về văn bản do AI sinh của nơi nộp.
