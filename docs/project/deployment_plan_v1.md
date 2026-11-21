# Kế hoạch triển khai thực tế v1: BrokerGuard Chat (giao diện chat, RAG, Gmail thật)

Cập nhật: 2026-11-21. Trạng thái (21/11): **M0–M3 có code và test, chạy được ở `--dry-run`; M2 chưa thử Gmail thật; M4 chờ tài liệu injection của nhóm; M5 chưa làm.** Quyết định gốc: [decision log 2026-11-21](decision_log.md).
Nhánh: `deploy/demo-v1`.

## 1. Mục tiêu

Một ứng dụng chạy được để người xem (hội đồng, thầy hướng dẫn) **ra lệnh bằng tiếng Việt cho agent trong khung chat**.
Agent tự tra kho tài liệu (RAG qua `doc_search`/`doc_read`), tự truy vấn CSDL và gửi email **thật qua Gmail**. Mọi lời gọi
tool đều đi qua Tool Broker và BrokerGuard v3. Ngay trong chat, người xem thấy từng bước agent làm, các quyết định cho
qua hay chặn kèm lý do, và câu trả lời cuối (đã che dữ liệu nhạy cảm).

Hai kịch bản phải chạy được khi bảo vệ:

1. **Lành:** "Tìm lịch đăng ký học phần rồi gửi tóm tắt cho huy@…". Agent tra tài liệu, soạn mail, người dùng bấm
   *Gửi*, mail tới hộp thư Gmail thật.
2. **Tấn công:** agent đọc phải tài liệu bị cài lệnh gửi dữ liệu ra địa chỉ lạ. Ở chế độ **A0** lời gọi gửi mail
   lọt tới hộp thư chờ, còn ở chế độ **BrokerGuard v3** lời gọi bị chặn và chat hiện lý do. Hai chế độ chuyển bằng một
   công tắc trên giao diện.

Bản demo này không phải thực nghiệm: không sinh số liệu cho bài, không dùng dữ liệu Dev/Test, không chỉnh v3.

## 2. Các quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| Q1 | Giao diện **Gradio** (`gr.ChatInterface` / `gr.Chatbot` kiểu `messages`), chạy local `127.0.0.1:7860` | Nhẹ, viết bằng Python thuần, có sẵn khung chat. Mỗi bước gọi tool hiện thành một khối thu gọn nhờ `ChatMessage.metadata`. Không phải viết frontend |
| Q2 | Model mặc định: **Gemini qua OmniRoute** local (`OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY` từ env), dùng `OpenAICompatBackend` có sẵn. Tùy chọn: endpoint vLLM Kaggle (`endpoint.env`) | Đã chạy ổn ở cột Gemini của Test-4 và không cần GPU. Kaggle tự tắt sau 30 phút không có request, không hợp với demo tương tác |
| Q3 | Runtime dùng **nguyên** `BrokerGuardV3Runtime` (cấu hình mặc định đã chọn trên Dev-val, như `final_config_v5`) và `Phase5ClosureRuntime` cho A0. **Không sửa file pinned nào** | Demo phải đúng là hệ thống đã đánh giá trong bài |
| Q4 | **Email thật theo mô hình hộp thư chờ (outbox).** Agent vẫn gọi `send_email_mock`, file đó giữ nguyên, không gọi mạng. Khi Broker và BrokerGuard đã cho qua và mock trả `simulated`, lớp demo đọc lời gọi trong trace và đưa vào **hộp thư chờ**. Người dùng bấm *Gửi* thì `GmailSender` mới gửi qua SMTP | BrokerGuard nhận diện sink theo **tên** (`SINK_DESTINATION = {"send_email_mock": "to", …}`, 23 chỗ trong `security_v1`/`security_v3`). Tool mới tên khác sẽ **đi vòng qua lớp bảo vệ**. Cách này cũng giữ bất biến "mock không gọi mạng" và tính tái lập của kết quả trong bài |
| Q5 | Rào chắn cho mail thật: (a) **danh sách địa chỉ cho phép** `DEMO_EMAIL_ALLOWLIST`, (b) **người dùng xác nhận** từng mail, (c) giới hạn `DEMO_EMAIL_DAILY_LIMIT` (mặc định 20), (d) công tắc `DEMO_EMAIL_LIVE=0/1`, mặc định 0 (chỉ hiện, không gửi), (e) chỉ gửi văn bản thuần, không đính kèm, thêm dòng chân "[BrokerGuard demo]" | Demo có cả kịch bản tấn công. Địa chỉ ngoài danh sách không bao giờ nhận được mail, kể cả ở A0. Muốn diễn "kẻ tấn công nhận được mail" thì dùng một Gmail thứ hai của nhóm làm hộp thư kẻ tấn công và cho vào danh sách |
| Q6 | Gửi bằng **SMTP `smtp.gmail.com:587` STARTTLS + App Password** (`smtplib` thư viện chuẩn) | Không cần OAuth hay Google Cloud project, không thêm thư viện. App Password cần bật xác minh 2 bước trên tài khoản gửi |
| Q7 | **RAG = tool truy xuất có sẵn** (`DocumentStore` + `doc_search` + `doc_read`) trên kho demo riêng `data/demo/`. Bước sau (tùy chọn): cho tải tài liệu lên qua giao diện, gắn nhãn **untrusted**. Tìm kiếm ngữ nghĩa bằng embedding để ngoài v1 | Giữ đúng giao diện tool mà BrokerGuard đã đánh giá. Đổi sang vector search sẽ đổi nguồn dữ liệu đi vào ngữ cảnh mà chưa được đánh giá |
| Q8 | Mỗi tin nhắn là **một task độc lập** (v1 không nhớ hội thoại khi chạy). Lịch sử chỉ để hiển thị | Ý định P(u) của C1 được trích từ lệnh của người dùng. Ghép nhiều lượt sẽ làm quyền cấp ở lượt cũ còn hiệu lực, điều này chưa được đánh giá. Hội thoại nhiều lượt để v2, phải ghi decision log riêng |
| Q9 | Bí mật để trong `.env.demo` (gitignore, quyền 0600), nạp bằng `os.environ`. Không log App Password, không đưa vào prompt. Sửa luôn chỗ khóa OmniRoute viết cứng trong `scripts/run_gemini_smoke.py` để đọc từ env | Bất biến: không commit credential |
| Q10 | Chạy **local trên Mac của owner**. Nếu cần cho người khác truy cập từ xa: `share=True` kèm `auth=(user, pass)`, chỉ bật trong buổi demo | OmniRoute và App Password đều nằm ở máy local. Không đưa lên server công khai |

## 3. Kiến trúc

```
Người dùng ──► Gradio Chat (demo/app.py)
                 │  tin nhắn + chế độ (A0 | BrokerGuard v3)
                 ▼
           DemoSession (demo/session.py)
                 │  tạo RuntimeTask(instruction), thư mục chạy results/demo/<phiên>/<lượt>/
                 ▼
     Phase5ClosureRuntime (A0)  |  BrokerGuardV3Runtime (v3)   ← không sửa
                 │  ReAct: model ⇄ Tool Broker ⇄ 8 tool (doc_search, doc_read, db_query, …, send_email_mock)
                 ▼
           trace_legacy.jsonl + run_metadata.json
                 │
                 ▼
     TraceView (demo/trace_view.py): bước, quyết định cổng, lý do, câu trả lời cuối
                 │                         │
                 ▼                         ▼
         các khối trong chat        Outbox (demo/outbox.py): mail đã được cho qua
                                           │  người dùng bấm "Gửi" + allowlist + hạn mức
                                           ▼
                                   GmailSender (demo/gmail_sender.py) ──SMTP──► Gmail
```

## 4. Cấu trúc code

Code đặt ở `src/react_agent/demo/` (lõi typed, có test) và `scripts/run_demo_app.py` (mỏng, chỉ dựng và chạy app).

| File | Nội dung |
|---|---|
| `src/react_agent/demo/config.py` | `DemoConfig` (pydantic): model, chế độ mặc định, allowlist, hạn mức, `live`, đường dẫn kho, thư mục chạy. Nạp từ env |
| `src/react_agent/demo/corpus.py` | Dựng môi trường demo (`documents.json`, `university.db`, `pages.json`) từ `data/demo/`, kiểm schema. Bước M4: thêm tài liệu tải lên với nhãn untrusted |
| `src/react_agent/demo/session.py` | `DemoSession.run(message, mode) -> TurnResult`: dựng backend, registry (`build_clean_registry`), runtime theo chế độ, gọi `run_instrumented`, trả trace đã phân tích. Chạy trong thread worker để UI không treo |
| `src/react_agent/demo/trace_view.py` | Đọc trace thành danh sách `Step(kind, tool, args, verdict, reasons, result_preview)`, cắt gọn nội dung dài, đổi mã lý do (`CONFIRMATION_REQUIRED`, `INTENT_*`, rò dữ liệu…) sang câu tiếng Việt dễ hiểu |
| `src/react_agent/demo/outbox.py` | `Outbox`: thêm mail đã được cho qua, trạng thái `pending/sent/rejected/blocked_allowlist/over_limit`, lưu `outbox.jsonl` của phiên, đếm hạn mức trong ngày |
| `src/react_agent/demo/gmail_sender.py` | `GmailSender.send(to, subject, body)`: `smtplib.SMTP` + `starttls` + `login`, timeout 15 giây, lỗi trả kiểu rõ ràng. Có `DryRunSender` cho `live=0` và cho test |
| `src/react_agent/demo/app.py` | `build_app(config) -> gr.Blocks`: khung chat, công tắc chế độ, ô chọn model, bảng hộp thư chờ với nút *Gửi*/*Hủy*, khung "Kho tài liệu" (xem, sau này tải lên) |
| `scripts/run_demo_app.py` | Nạp `.env.demo`, kiểm OmniRoute có sống không (`GET /models`), in URL, `app.launch()` |
| `data/demo/` | Kho demo (track): `documents/documents.json`, `database/seed.json` → build `university.db`, `cached_pages/pages.json`, `scenarios.md` (câu lệnh mẫu để diễn) |
| `tests/demo/` | Test (mục 6) |

Phụ thuộc: `requirements-demo.txt` (gradio 5, python-dotenv), cài bằng `.venv/bin/pip install -r requirements-demo.txt`.
Không sửa `pyproject.toml` vì file này nằm trong seal của `release_v2`. Lõi `react_agent` không import gradio. Chỉ `demo/app.py` import.

## 5. Các bước làm (mỗi bước có tiêu chí nghiệm thu)

| Bước | Việc | Nghiệm thu |
|---|---|---|
| **M0** Chốt và chuẩn bị | Decision log, kế hoạch này, dòng Bản đồ trong runbook. Owner chuẩn bị Gmail gửi (2FA + App Password), danh sách nhận, `.env.demo` | `make knowledge-check` qua. `.env.demo` nằm trong `.gitignore` |
| **M1** Lõi chạy một lệnh | `config.py`, `corpus.py`, `session.py`, `trace_view.py`. Chạy CLI một lệnh với `--dry-run-dummy` và với Gemini | A0 và v3 đều trả câu trả lời cuối và danh sách bước. Không file pinned nào đổi (`final_config_v5` vẫn khớp hash) |
| **M2** Hộp thư chờ + Gmail | `outbox.py`, `gmail_sender.py`, nối với `session` | Test giả lập SMTP qua. Owner gửi thử 1 mail thật tới chính mình (`DEMO_EMAIL_LIVE=1`). Địa chỉ ngoài danh sách bị từ chối |
| **M3** Giao diện chat | `app.py`, `run_demo_app.py`: chat, công tắc A0/v3, khối bước thu gọn, câu báo chặn, bảng hộp thư chờ có nút | Owner chạy `run_demo_app.py`, diễn được kịch bản lành từ đầu tới mail nhận được trong Gmail |
| **M4** Kho demo + kịch bản tấn công | Claude dựng kho **sạch** (tài liệu, CSDL tổng hợp) và bộ nạp. **Owner/Minh viết tài liệu chứa injection** theo khuôn `data/demo/AUTHORING.md` (Claude chỉ viết khuôn và bộ kiểm schema, không đọc nội dung). Tùy chọn: tải tài liệu lên qua UI | Ở A0 kịch bản tấn công tạo được mail chờ tới hộp thư "kẻ tấn công". Ở v3 bị chặn và hiện lý do. Kịch bản lành vẫn chạy ở v3 |
| **M5** Hoàn thiện cho buổi bảo vệ | Hiện từng bước khi đang chạy (đọc trace theo thời gian thực), nút "Chạy lại ở chế độ kia", xuất log phiên, `docs/demo/README.md` hướng dẫn chạy 5 phút, ảnh chụp màn hình | Tổng duyệt: owner chạy hết `scenarios.md` trên máy, không lỗi. Thời gian một lượt ghi vào README |

Thứ tự đề xuất: M0 → M1 → M2 → M3 → M4 → M5. M2 và M3 có thể làm song song sau khi M1 xong.

## 6. Kiểm thử

- `tests/demo/test_outbox.py`: allowlist (khớp không phân biệt hoa thường, bỏ khoảng trắng, chặn `a@x.com,b@y.com`
  và dạng `"Tên" <x@y>` lạ), hạn mức ngày, chuyển trạng thái, không gửi khi `live=0`.
- `tests/demo/test_gmail_sender.py`: dùng `smtplib.SMTP` giả (monkeypatch), kiểm `starttls` trước `login`, tiêu đề
  không chứa xuống dòng (chặn chèn header), mật khẩu không xuất hiện trong log hay exception.
- `tests/demo/test_session.py`: chạy `DummyBackend` qua cả A0 và v3. Ở v3 một lời gọi `send_email_mock` tới địa chỉ
  không có trong lệnh bị chặn và **không vào outbox**. Ở A0 lời gọi đó vào outbox với trạng thái `blocked_allowlist`
  nếu địa chỉ ngoài danh sách.
- `tests/demo/test_trace_view.py`: phân tích trace mẫu, đổi mã lý do sang tiếng Việt.
- Kiểm bất biến: test xác nhận `send_email_mock.py` và các file trong `final_config_v5` không đổi hash. Lõi
  `react_agent` import được khi không cài gradio.
- Trước khi xong mỗi bước: `ruff check .`, `mypy src scripts`, `pytest`, `python scripts/verify_setup.py`.

## 7. Rủi ro và cách xử lý

| Rủi ro | Xử lý |
|---|---|
| Gửi nhầm mail ra ngoài khi demo tấn công | Allowlist + xác nhận từng mail + `DEMO_EMAIL_LIVE` mặc định 0 + hạn mức ngày |
| Lộ App Password | Chỉ ở `.env.demo` (gitignore, 0600). Không log, không hiện trên UI. Thu hồi App Password sau buổi bảo vệ |
| Google chặn đăng nhập SMTP | Dùng App Password (không dùng mật khẩu chính). Nếu tài khoản thuộc Workspace trường chặn thì dùng Gmail cá nhân |
| OmniRoute hết quota hoặc chưa bật | `run_demo_app.py` kiểm trước khi mở. Trên UI cho chọn endpoint khác (vLLM Kaggle) hoặc chế độ phát lại `replay_responses` để diễn khi mất mạng |
| Gemini chậm làm UI treo | Chạy runtime trong thread worker, hiện "đang chạy bước n", timeout mỗi lượt (mặc định 120 giây) |
| Hành vi demo khác hệ thống trong bài | Không sửa file pinned. Test kiểm hash. Mỗi lượt ghi `run_metadata.json` có profile v3 |
| Người xem hỏi "sao không nhớ câu trước" | Nói rõ trên UI: v1 coi mỗi lệnh là một task độc lập, đúng như phạm vi đã đánh giá (Q8) |

## 8. Việc owner cần làm

1. Chọn Gmail gửi, bật xác minh 2 bước, tạo App Password (Google Account → Security → App passwords).
2. Chốt danh sách địa chỉ nhận (mail của owner, Minh, thầy, và một Gmail làm "kẻ tấn công" nếu muốn diễn lọt ở A0).
3. Điền `.env.demo` theo mẫu `.env.demo.example` (Claude tạo ở M0, chỉ có tên biến).
4. Bước M4: viết tài liệu chứa injection cho kịch bản tấn công theo `data/demo/AUTHORING.md`.
5. Bật OmniRoute trước khi chạy demo (Claude không tự khởi động lại OmniRoute).

## 9. Ngoài phạm vi v1

Hội thoại nhiều lượt có nhớ, OAuth Gmail API, đính kèm file, đọc hộp thư đến, tìm kiếm ngữ nghĩa bằng embedding,
triển khai lên server công khai, nhiều người dùng đồng thời, webhook thật. Mỗi mục nếu làm phải ghi decision log riêng.
