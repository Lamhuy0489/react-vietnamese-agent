# Bài báo ICCIES 2027: mục lục làm việc

Đọc file này trước khi viết. Bản thảo tiếng Anh nằm ở `sections/`, mỗi mục một file; số liệu được phép dùng nằm ở
[facts.md](facts.md). Không chép văn bản tấn công hay nội dung Test vào thư mục này.

## Hội nghị

| | |
|---|---|
| Hội nghị | International Conference on Computational Intelligence in Engineering Science (ICCIES 2027), Đại học Tôn Đức Thắng, 15–17/04/2027 |
| Kỷ yếu | Springer CCIS; template Springer LNCS/CCIS (LaTeX hoặc Word); tiếng Anh; 12–15 trang |
| Nộp bài | Microsoft CMT, `https://cmt3.research.microsoft.com/ICCIES2027` |
| Hạn | Toàn văn **15/11/2026** · báo kết quả 31/12/2026 · camera-ready 15/01/2027 |
| Track dự kiến | Generative AI & Large Language Models for Intelligent Systems (phụ: Cybersecurity) |

Thông tin hội nghị lấy từ trang `iccies.tdtu.edu.vn/2027` ngày 10/11/2026; kiểm lại hạn và template trước khi nộp.

## Luận điểm

Phần chính là cơ chế phòng thủ D3 và xác nhận trên bộ Test-3 niêm phong với 3 backbone mở. Gemini 3 Flash và AgentDojo
là ngoại kiểm phụ. Mức tăng utility của D3 so với D2+P2 nhỏ (+1,0 điểm) và phải viết đúng như vậy.

## Các mục và trạng thái (cập nhật 2026-11-10)

| File | Nội dung | Trang dự kiến | Trạng thái | Nguồn chính |
|---|---|---|---|---|
| [00_title_abstract.md](sections/00_title_abstract.md) | Tiêu đề, abstract, keywords | 0,5 | bản đầy đủ; chờ owner duyệt tiêu đề | facts.md |
| [01_introduction.md](sections/01_introduction.md) | Giới thiệu, 4 đóng góp | 1,5 | bản đầy đủ | facts.md |
| [02_threat_model_taxonomy.md](sections/02_threat_model_taxonomy.md) | Mô hình đe dọa, vị từ gây hại, M1–M6, nhánh benign, biến thể | 2 | bản đầy đủ | `data/adversarial/v3_authoring/taxonomy.md`, `docs/tool_contracts.md` |
| [03_d3_defence.md](sections/03_d3_defence.md) | Kiến trúc D3, luật R2–R4, luật D, ablation | 2,5 | bản đầy đủ; **thiếu Hình 1** | `src/react_agent/security_v1/control_data_policy_v1.py`, `src/react_agent/security_v3/d3.py`, decision log 09/11 13:00 |
| [04_benchmark_protocol.md](sections/04_benchmark_protocol.md) | Benchmark, niêm phong, backbone, baseline, thống kê | 2,5 | bản đầy đủ (10/11); chờ owner đọc | decision log 09/11 15:00–21:40, taxonomy.md, `final_config_v4.json` |
| [05_results.md](sections/05_results.md) | Bảng 5–11 và các ý cần viết | 3,5 | bảng xong (Bảng 11 đủ ô từ 10/11); **thiếu lời văn** | `docs/research/study2_thesis_tables.md` |
| [06_discussion_limitations.md](sections/06_discussion_limitations.md) | Lỗi còn lại, ngôn ngữ, hạn chế | 1 | **dàn ý** | Bảng 2.4, 2.8 |
| [07_conclusion.md](sections/07_conclusion.md) | Kết luận | 0,5 | **chưa viết** | — |
| [08_references.md](sections/08_references.md) | Tài liệu tham khảo | 1,5 | **danh sách thô, chưa đối chiếu** nơi đăng, năm, trang | — |

## Việc còn lại, theo thứ tự

1. ~~Viết Mục 4 từ dàn ý.~~ Xong 10/11. Lưu ý: T2 là kiểm định z một phía với SE theo cụm family (không phải McNemar);
   chú thích Bảng 9 ở Mục 5 đang ghi chung là McNemar, sửa khi viết lời Mục 5.
2. Viết lời cho Mục 5 quanh các bảng đã có.
3. Viết Mục 6 và Mục 7.
4. Vẽ Hình 1 (kiến trúc D3; mô tả trong Mục 3.1).
5. Đối chiếu từng tài liệu tham khảo với bản gốc; không thêm trích dẫn chưa kiểm.
6. Chuyển sang template Springer, đếm trang (mục tiêu 12–15), cắt bảng nếu vượt (ứng viên cắt: Bảng 5 hoặc Bảng 7).

## Owner cần quyết

- Tiêu đề (bản hiện tại ở `00_title_abstract.md`).
- Có công bố dữ liệu không: Mục 1 đang để chỗ trống `[owner decides: release / available on request]`.
- Tác giả, đơn vị, lời cảm ơn.

## Quy tắc khi viết

- Mọi con số lấy từ [facts.md](facts.md) hoặc `docs/research/study2_thesis_tables.md`; số nào không có ở đó thì không viết.
- Utility benign trên Test-3 là 51,0% (D3) so với 54,5% (A0). Không viết "trên 90%".
- Backbone: Gemma-4-12B, Llama-3.1-8B, Qwen3.5-9B. Gemini 3 Flash chỉ chạy trên Dev và AgentDojo, ngoài kiểm định chính.
- Quy mô: Dev 48 family, Test v3 72, Test-3 48; 5 biến thể ngôn ngữ; 6 cơ chế M1–M6.
- Thống kê: McNemar chính xác trên cặp fixture, hiệu chỉnh Holm, CI bootstrap theo family (10.000 lần).
- Không khẳng định tiếng Việt dễ bị tấn công hơn: H4 và H5 không có ý nghĩa thống kê.
- Trong bài, "D3" là cấu hình có tên `D3DEST` trong log và trong bảng luận văn.
- Không viết "state-of-the-art"; không viết "release" khi owner chưa quyết.
- Cơ chế và kết quả mô tả ở mức tổng hợp; không trích câu tấn công, không nêu ID family của Test.
