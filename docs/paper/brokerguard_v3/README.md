# Bài BrokerGuard v3: mục lục làm việc

Viết ngày 2026-11-19, sửa lần 2 cùng ngày (bỏ tên phiên bản, giảm mã, chống tràn lề). Bài duy nhất của đồ án; bài
ICCIES cũ ở `../iccies2027/` không nộp. Hai bản song song, cùng cấu trúc, bảng, hình, nhãn tham chiếu và số:

- `latex/`: bản tiếng Việt để đọc (số kiểu Việt: 32,1\%; 1.960).
- `latex_en/`: bản tiếng Anh (chính tả Anh-Anh, số kiểu Anh: 32.1\%; 1,960; tóm tắt 248 từ). Font T5 vì Mục 4 trích vài từ
  phủ định tiếng Việt. Sửa nội dung thì sửa cả hai bản.

## Định dạng và biên dịch

| | |
|---|---|
| Template | Springer LNCS (`llncs.cls` 2.26, `splncs04.bst`), giống bài ICCIES cũ |
| Độ dài | Owner cho phép dài hơn 15 trang (19/11); owner tinh chỉnh và cắt sau khi chốt nơi nộp. Ước lượng hiện tại khoảng 20 trang |
| Biên dịch | Overleaf: zip cả thư mục `latex/`, main = `main.tex`, pdfLaTeX. Lỗi font T5 thì đổi sang XeLaTeX (hướng dẫn ở đầu `main.tex`) |
| Hình | Cả ba hình vẽ bằng TikZ/pgfplots trong `.tex`, Overleaf tự vẽ. Không render hình hay PDF trên máy |
| Tiêu đề | BrokerGuard: Intent-Aware Authorisation and Value-Level Flow Control Against Indirect Prompt Injection in Vietnamese LLM Agents (owner có thể đổi) |
| Kiểm tĩnh | Ngoặc, môi trường, `\ref`, `\cite`, dấu `%` sau số, chấm phẩy trong lời văn: đã kiểm bằng script (19/11), chưa biên dịch thật |

## Nguồn số liệu

Mọi con số lấy từ [`../iccies2027/facts.md`](../iccies2027/facts.md), chủ yếu các mục:

- "Bài v3 ... Test-4 dưới final_config_v5" (bảng chính, H1–H4, theo cơ chế, loại hại, biến thể, bằng chứng mức ca, hạn chế);
- "Cột tham khảo Gemini 3 Flash trên Test-4", "Baseline bổ sung trên Test-4", "Baseline bổ sung trên Dev v4.1";
- "Vòng thích nghi nhắm v3 trên Dev-val", "AgentDojo: bảng đầy đủ mọi lượt", "AgentDojo: BrokerGuard v3";
- "Bổ sung cho bài v3" (ASR mức ca, tiện ích dạng số ca, Dev P2/PRG, QA của Test-4, bằng chứng phát triển, chi phí theo
  mô hình, tài liệu mới). ASR mức ca sinh bằng `scripts/paper_v3_case_counts_v1.py`.

Mỗi file bảng và hình có comment đầu file ghi nguồn của từng số. Số nào không có trong facts.md thì không viết.

## Cấu trúc

| File | Nội dung |
|---|---|
| `latex/main.tex`, `latex_en/main.tex` | Preamble, macro tên gọi (đổi một dòng là đổi cả bài); bản Việt có tên định lý tiếng Việt |
| `latex_en/` | Bản tiếng Anh: cùng tên file, cùng nhãn `\label` với `latex/` |
| `latex/sections/00_abstract.tex` … `09_conclusion.tex` | Tóm tắt, giới thiệu, liên quan, mô hình đe dọa, phương pháp, mô hình hình thức, giao thức, kết quả, thảo luận, kết luận |
| `latex/tables/tab1_mechanisms.tex` | Bảng 1: sáu cơ chế, 40 ca lọt qua luật chuỗi + Sandwich theo nguyên nhân, thành phần xử lý |
| `latex/tables/tab2_proven.tex` | Bảng 2: thuộc tính chứng minh và thuộc tính thực nghiệm |
| `latex/tables/tab3_main.tex` | Bảng 3: 13 cấu hình trên tập kiểm thử và cột tập phát triển, kèm H1–H4 |
| `latex/tables/tab4_cost.tex` | Bảng 4: token, thời gian, chặn nhầm, xác nhận theo mô hình |
| `latex/tables/tab5_adaptive.tex` | Bảng 5: hai bộ tấn công thích nghi |
| `latex/tables/tab6_general.tex` | Bảng 6: (a) Gemini 3 Flash trên tập kiểm thử, (b) AgentDojo |
| `latex/images/fig1_architecture.tex` | Hình 1: kiến trúc (TikZ) |
| `latex/images/fig2_pareto.tex` | Hình 2: đánh đổi an ninh và tiện ích (pgfplots) |
| `latex/images/fig3_mechanisms.tex` | Hình 3: họ bị hại theo cơ chế, (a) so với phòng thủ khác, (b) ablation |
| `latex/refs.bib` | 25 mục, đều được trích; 4 mục mới kiểm ngày 19/11 (CapLite, Dwork 2015, Recht 2019, Tramèr 2020) |

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
| M1…M6 | ER, CR, SL, AL, PT, US (chỉ trong bảng, hình) | như cột trái | `\mER` … |

**Quy tắc dùng mã:** trong lời văn dùng tên đầy đủ. Mã C1–C3 chỉ ở chỗ định nghĩa (Mục 4), trong bảng và hình. H1–H4,
(A1)–(A5), (G1)–(G4) giữ vì kiểm định và chứng minh tham chiếu tới chúng. Mã cơ chế chỉ trong bảng và hình.

**Chống tràn lề:** mọi bảng và hình bọc trong `adjustbox{max width=\textwidth}` (vừa khổ thì giữ nguyên, rộng hơn thì
tự thu vừa); Bảng 4 và 6a xoay (chỉ số theo hàng) để vừa khổ không phải co chữ; Hình 3 hai panel xếp dọc;
`\emergencystretch=3em` để chữ đơn cách không thò ra lề; công thức độ đo tách $\Delta U$ ra lời văn.

## Quy tắc khi sửa

- Văn phong học thuật, khách quan: không "chúng tôi", "ta"; dùng "bài báo", câu bị động hoặc hệ thống làm chủ ngữ.
- Câu ngắn và vừa, không chấm phẩy trong lời văn, không gạch dài. Tránh khuôn liệt kê máy móc ("Thứ nhất… Thứ tư"),
  câu tóm lại kiểu "Nói cách khác", từ sáo ("đóng vai trò then chốt", "vượt trội").
- Mã chỉ ở chỗ cần thiết (xem "Quy tắc dùng mã" ở trên). Không nêu mã họ của Test, không trích văn bản tấn công.
- Không dùng tên phiên bản; mọi so sánh với luật chuỗi gọi là "luật chuỗi + Sandwich" (BrokerGuard bỏ cả ba thành phần).
- H1 báo trung thực (không đạt, hiệu ứng sàn). So sánh với baseline là khám phá. Gemini là cột tham khảo, không kiểm định.
- Tập kiểm thử ghi là "sinh tự động từ đặc tả, hai thành viên rà soát", không báo κ (decision log 2026-11-15 18:20).
- Mỗi lần sửa số: sửa facts.md trước, rồi bảng, hình, lời văn. Không chạy regex đổi dấu thập phân trên file hình.

## Việc owner cần làm

1. Tải `latex/` lên Overleaf, biên dịch, báo lỗi nếu có (bài chưa từng được biên dịch).
2. Đọc bản tiếng Việt, góp ý nội dung và văn phong.
3. Chốt nơi nộp (tạp chí Q4) và template, tiêu đề, tác giả, đơn vị, email (các ô `\todo` màu đỏ).
4. Nếu nơi nộp giới hạn trang, ứng viên cắt: Bảng 6a thành một đoạn văn; Bảng 4 thành hai câu; Hình 3b; gộp đoạn
   "Mối đe dọa với tính hợp lệ" vào "Hạn chế"; bớt ví dụ ở mục C1.
5. Bản tiếng Anh đã có ở `latex_en/` (19/11). Nếu nơi nộp cấm văn bản do AI sinh, owner tự viết lại lời văn tiếng Anh
   dựa trên bản này.

## Kiểm trước khi nộp

- [ ] Biên dịch không lỗi, không cảnh báo overfull đáng kể (Bảng 4 và 6 rộng nhất).
- [ ] Tóm tắt 150–250 từ (bản tiếng Anh); 3–5 từ khóa.
- [ ] Xóa mọi `\todo` và định nghĩa `\todo` (bản tiếng Anh không có khối tên định lý tiếng Việt).
- [ ] Hình đọc được khi in đen trắng (hình dạng điểm, vân sọc, độ dày viền đã có).
- [ ] Đối chiếu mục UNVERIFIED trong `refs.bib` (Holm 1979).
- [ ] Kiểm lại quy định về văn bản do AI sinh của nơi nộp.
