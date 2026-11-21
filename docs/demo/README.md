# Hướng Dẫn Vận Hành Trình Diễn BrokerGuard Chat

Tài liệu này dành cho người thực hiện đề tài để triển khai và điều khiển buổi trình diễn thực tế trước hội đồng bảo vệ đồ án tốt nghiệp. Hướng dẫn bao gồm quy trình chuẩn bị dịch vụ, thiết lập an toàn thư điện tử, kịch bản thuyết trình và biện pháp xử lý sự cố.

## 1. Giới thiệu BrokerGuard Chat

BrokerGuard Chat là giao diện tương tác trực tiếp giúp hội đồng đánh giá cơ chế phòng thủ của kiến trúc BrokerGuard v3 trên tác tử ReAct. Ứng dụng tiếp nhận câu lệnh tiếng Việt từ người dùng, thực hiện tra cứu tài liệu RAG, truy vấn cơ sở dữ liệu và soạn thảo thư điện tử gửi tới hộp thư thật. Toàn bộ các tương tác công cụ đều phải đi qua lớp điều phối Tool Broker và cổng an ninh BrokerGuard v3 nhằm phát hiện, ngăn chặn kịp thời hành vi tấn công chiếm quyền hoặc đánh cắp dữ liệu. Sau khi vượt qua các lớp kiểm soát an toàn, thư điện tử được đưa vào hộp thư chờ để người điều khiển trực tiếp bấm phê duyệt trước khi chuyển qua cổng SMTP Gmail.

```
Người dùng
    │
    │ (Nhập lệnh tiếng Việt, chọn chế độ A0 hoặc BrokerGuard v3)
    ▼
Giao diện Chat Gradio (scripts/run_demo_app.py)
    │
    ▼
DemoSession (Phase5ClosureRuntime A0 hoặc BrokerGuardV3Runtime v3)
    │
    ├─► Mô hình ReAct (Gemini qua proxy HTTPS 127.0.0.1:8444)
    │        ▲
    │        │ Đề xuất gọi công cụ
    ▼        ▼
Tool Broker và Cổng an ninh BrokerGuard v3
    │
    ├─► Công cụ nội bộ (doc_search, doc_read, db_query)
    │
    └─► send_email_mock (bị chặn hoặc cho phép mô phỏng)
             │
             ▼
        Hộp thư chờ Outbox
             │
             │ (Người dùng bấm nút "Gửi" khi thỏa 4 điều kiện an toàn)
             ▼
        GmailSender (SMTP smtp.gmail.com:587) ──► Hộp thư Gmail thật
```

## 2. Cài đặt môi trường

Mở cửa sổ dòng lệnh tại thư mục gốc của dự án và cài đặt gói phụ thuộc phục vụ giao diện trình diễn:

```bash
.venv/bin/pip install -r requirements-demo.txt
```

Lệnh này bổ sung các thư viện cần thiết gồm gradio và python-dotenv vào môi trường ảo hiện hành. Phần mã nguồn lõi của tác tử hoàn toàn tách biệt, bảo đảm tính độc lập với giao diện.

## 3. Cấu hình bảo mật và Gmail App Password

### Các bước tạo Gmail App Password

1. Đăng nhập tài khoản Google cá nhân dùng làm hộp thư gửi thư trình diễn.
2. Bật xác minh 2 bước bằng cách truy cập Google Account, mở thẻ Security và hoàn tất kích hoạt tại mục 2-Step Verification.
3. Tạo mật khẩu ứng dụng: tại ô tìm kiếm của Google Account hoặc trong mục Security, chọn App passwords. Nhập tên đại diện (ví dụ BrokerGuardDemo) rồi bấm Create để nhận chuỗi ký tự mật khẩu ứng dụng gồm 16 chữ cái.
4. Lưu chuỗi mật khẩu 16 chữ cái này vào vị trí an toàn để điền vào cấu hình. Không cung cấp mật khẩu này cho người khác.

### Thiết lập file môi trường

Khởi tạo file cấu hình `.env.demo` từ bản mẫu và giới hạn quyền truy cập tệp:

```bash
cp .env.demo.example .env.demo
chmod 600 .env.demo
```

Lệnh `chmod 600 .env.demo` bảo đảm chỉ có tài khoản người dùng hiện tại trên máy tính mới có quyền đọc và chỉnh sửa file, ngăn chặn nguy cơ lộ lọt thông tin nhạy cảm.

### Giải thích các biến môi trường trong .env.demo

- `VLLM_BASE_URL`: Địa chỉ URL tương thích OpenAI của mô hình, mặc định trỏ tới proxy cục bộ `https://127.0.0.1:8444/v1`.
- `VLLM_API_KEY`: Khóa xác thực cục bộ do proxy cấp, lấy từ file `build/gemini/local_key`.
- `SSL_CERT_FILE`: Đường dẫn tới file chứng chỉ SSL gộp chứa chứng chỉ tự ký của proxy.
- `DEMO_MODEL_REPO`: Tên kho mô hình định danh (`google/gemini-3-flash`).
- `DEMO_MODEL_REVISION`: Phiên bản cấu hình mô hình (`antigravity-omniroute-2026-11-09-jsonfix`).
- `DEMO_DEFAULT_MODE`: Chế độ an ninh mặc định khi tải trang (`V3` hoặc `A0`).
- `DEMO_DRY_RUN`: Cờ chạy thử không cần mạng, nhận giá trị `0` (chạy thật) hoặc `1` (chạy ngoại tuyến với dữ liệu mẫu).
- `DEMO_EMAIL_LIVE`: Cờ điều khiển việc gửi thư qua Internet. Mặc định luôn là `0` (chỉ ghi nhận vào hộp thư chờ để quan sát, tuyệt đối không gửi qua SMTP). Chỉ chuyển sang `1` khi muốn gửi thư thực tế trong buổi bảo vệ.
- `GMAIL_USER`: Địa chỉ hộp thư Gmail gửi tin.
- `GMAIL_APP_PASSWORD`: Chuỗi mật khẩu ứng dụng 16 ký tự vừa tạo từ tài khoản Google gửi.
- `DEMO_EMAIL_ALLOWLIST`: Danh sách các địa chỉ hộp thư nhận được phép, ngăn cách nhau bằng dấu phẩy (ví dụ `thayhuongdan@example.com,sinhvien@example.com`). Chỉ các hộp thư nằm trong danh sách này mới được gửi thư đi.
- `DEMO_EMAIL_DAILY_LIMIT`: Số lượng thư tối đa được phép phát tán ra ngoài trong một ngày (mặc định là 20 thư).
- `DEMO_AUTH_USER`: Tên tài khoản đăng nhập khi chia sẻ giao diện từ xa qua cờ `--share`.
- `DEMO_AUTH_PASSWORD`: Mật khẩu đăng nhập khi chia sẻ giao diện từ xa qua cờ `--share`.

Mặc định biến `DEMO_EMAIL_LIVE` luôn đặt giá trị `0`. Ở trạng thái này, thao tác bấm nút gửi trên giao diện chỉ cập nhật trạng thái mô phỏng mà không gọi kết nối mạng SMTP. Khi chuyển `DEMO_EMAIL_LIVE=1`, hệ thống bắt buộc kiểm tra địa chỉ người nhận có nằm trong `DEMO_EMAIL_ALLOWLIST` hay không. Mọi địa chỉ lạ nằm ngoài danh sách đều bị hệ thống chặn ngay tại hộp thư chờ.

## 4. Khởi động mô hình và Proxy Gemini

Tiến trình OmniRoute phải do người thực hiện tự bật độc lập trên cổng 20128 trước buổi diễn. Tác tử và các script phụ trợ không bao giờ tự ý khởi động lại OmniRoute.

Kiểm tra OmniRoute có đang hoạt động trên cổng 20128:

```bash
lsof -nP -iTCP:20128 -sTCP:LISTEN
```

Tiếp tục khởi động tiến trình proxy Gemini trung gian theo lệnh mẫu từ `build/gemini/t4_gemini_chain.sh`:

```bash
nohup caffeinate -ims .venv/bin/python scripts/gemini_proxy_v1.py \
  --upstream http://localhost:20128/v1/chat/completions \
  --keys-file ~/.omniroute_key \
  --model gemini-pool \
  --repo google/gemini-3-flash \
  --revision antigravity-omniroute-2026-11-09-jsonfix \
  --reasoning-effort "" \
  --thinking-tokens 0 \
  --min-interval 2 \
  --max-retries 10 \
  --port 8444 \
  --header "X-OmniRoute-No-Cache: true" \
  --drop-field response_format \
  --extract-json \
  --local-key-file build/gemini/local_key \
  --cert build/gemini/proxy.crt \
  --cert-key build/gemini/proxy.key \
  --stats-every 900 >> build/gemini/proxy_omni.log 2>&1 &
```

Proxy sẽ mở cổng HTTPS tại địa chỉ `https://127.0.0.1:8444`. Thiết lập kết nối trong `.env.demo`:
- `VLLM_BASE_URL=https://127.0.0.1:8444/v1`
- `VLLM_API_KEY`: đọc trực tiếp từ file `build/gemini/local_key`

Vì proxy sử dụng chứng chỉ tự ký `build/gemini/proxy.crt`, Python cần nhận diện chứng chỉ này để không báo lỗi SSL. Gợi ý ghép chứng chỉ của certifi cùng chứng chỉ proxy vào một file bundle:

```bash
cat $(.venv/bin/python -m certifi) build/gemini/proxy.crt > build/gemini/ca_bundle.pem
```

Sau đó thiết lập `SSL_CERT_FILE` trỏ tới đường dẫn file `build/gemini/ca_bundle.pem` vừa tạo.

Nếu không chắc chi tiết nào, kiểm lại trong `build/gemini/t4_gemini_chain.sh`.

## 5. Khởi chạy ứng dụng

### Chạy thử nghiệm ngoại tuyến

Trước khi kết nối mạng, chạy thử giao diện bằng chế độ mô phỏng phản hồi:

```bash
.venv/bin/python scripts/run_demo_app.py --dry-run
```

Chế độ này giúp xác nhận giao diện Gradio, quy trình dựng kho tài liệu và bảng điều khiển hoạt động chính xác mà không cần gọi mô hình hoặc mạng Internet.

### Khởi chạy chính thức

Khi đã sẵn sàng, chạy ứng dụng với file cấu hình:

```bash
.venv/bin/python scripts/run_demo_app.py --env-file .env.demo --port 7860
```

Mở trình duyệt web trên máy tính và truy cập: `http://127.0.0.1:7860`

### Chia sẻ truy cập từ xa trong buổi bảo vệ

Trường hợp thành viên hội đồng muốn trải nghiệm trực tiếp từ thiết bị cá nhân, kích hoạt tham số chia sẻ:

```bash
.venv/bin/python scripts/run_demo_app.py --env-file .env.demo --port 7860 --share
```

Chế độ chia sẻ từ xa qua tham số `--share` chỉ được mở trong thời gian diễn ra buổi bảo vệ. Khi dùng tùy chọn này, bắt buộc phải khai báo giá trị `DEMO_AUTH_USER` và `DEMO_AUTH_PASSWORD` trong file `.env.demo` để bảo đảm quyền riêng tư của hệ thống.

## 6. Kịch bản trình diễn 5 phút

### Phần 1: Thực thi chỉ thị lành tính trên BrokerGuard v3

1. Chọn chế độ BrokerGuard v3 trên giao diện điều khiển.
2. Nhập một câu lệnh lành tính (ví dụ yêu cầu tìm lịch đăng ký học phần trong kho tài liệu rồi gửi thư tóm tắt cho địa chỉ email sinh viên nằm trong allowlist).
3. Quan sát các bước thực thi hiển thị theo thời gian thực: tác tử gọi công cụ tìm kiếm và đọc tài liệu (`doc_search`, `doc_read`), xử lý kết quả và đề xuất gọi `send_email_mock`. Cổng an ninh v3 phân tích ý định và đánh dấu cho phép thực thi.
4. Chuyển xuống khung Hộp thư chờ (Outbox). Bức thư xuất hiện ở trạng thái chờ gửi (pending).
5. Người vận hành bấm nút "Gửi". Hệ thống kiểm tra điều kiện an toàn và chuyển tiếp thư qua giao thức SMTP Gmail.
6. Mở hòm thư Gmail của người nhận để kiểm tra nội dung thư tóm tắt được gửi đến thành công.

### Phần 2: Chuyển sang A0 và chạy kịch bản tấn công so sánh

1. Gạt công tắc chế độ từ BrokerGuard v3 sang A0 (Phase5ClosureRuntime, chế độ không có cổng an ninh bảo vệ).
2. Nhập câu lệnh kích hoạt kịch bản tấn công do nhóm chuẩn bị theo cấu trúc tại file `data/demo/AUTHORING.md` (không trình bày chi tiết nội dung tấn công trước hội đồng).
3. Tác tử ở chế độ A0 đọc phải tài liệu bị cài mã gián tiếp, bị thao túng ý định và tự động đề xuất gọi công cụ gửi dữ liệu mật tới hộp thư của kẻ tấn công. Thư này lọt vào bảng Hộp thư chờ (tuy nhiên nếu địa chỉ không thuộc allowlist thì outbox vẫn giữ lại).
4. Gạt công tắc chế độ quay trở lại BrokerGuard v3 và nhập lại đúng câu lệnh tấn công đó.
5. Cổng an ninh v3 phát hiện nguồn điều khiển không tin cậy hoặc ý định gửi không được người dùng ủy quyền, lập tức chặn đứng lời gọi công cụ và xuất thông báo lý do từ chối rõ ràng trên giao diện chat.
6. Trình bày với hội đồng sự khác biệt về năng lực ngăn chặn rò rỉ dữ liệu giữa BrokerGuard v3 và tác tử A0 truyền thống.

### Phần 3: Giải thích các lý do chặn thường gặp từ cổng an ninh

Hệ thống diễn giải các mã quyết định nội bộ sang câu thông báo tiếng Việt trực quan từ bảng REASONS_VI:

- `INTENT_NOT_GRANTED`: Lệnh của người dùng không cho phép hành động này tới đích này
- `INTENT_FORBIDDEN`: Người dùng đã cấm hành động này
- `INTENT_NO_TARGET`: Lệnh không nêu đích nhận
- `INTENT_NO_ACTION_VERB`: Lệnh không có động từ yêu cầu hành động
- `INTENT_MENTION_ONLY`: Đích chỉ được nhắc tới, không được yêu cầu gửi
- `INTENT_QUOTED`: Đích nằm trong phần trích dẫn
- `INTENT_REPORTED`: Đích nằm trong lời thuật lại
- `INTENT_REFERENCE_ONLY`: Đích chỉ được tham chiếu
- `INTENT_CONDITIONAL`: Quyền chỉ có khi thỏa điều kiện
- `INTENT_AMBIGUOUS_NEGATION`: Lệnh có phủ định không rõ
- `CONFIRMATION_REQUIRED`: Cần người dùng xác nhận
- `PINNED_PARAMETER_CHANGED`: Tham số người dùng đã nêu bị đổi
- `PROVENANCE_SENSITIVE_PAYLOAD`: Nội dung gửi đi chứa dữ liệu mật
- `PROVENANCE_SENSITIVE_FINAL`: Câu trả lời chứa dữ liệu mật
- `UNTRUSTED_CONTROL_INFLUENCE`: Hành động bị dẫn dắt bởi nội dung không tin cậy
- `SECURITY_POLICY_DENIED`: Chính sách an ninh từ chối
- `RULE_GUARD_ERROR`: Lỗi ở lớp luật

## 7. Quy tắc an toàn bắt buộc

### 4 điều kiện để một bức thư thực sự được gửi đi

1. Cổng BrokerGuard v3 (hoặc tác tử A0) đã phê duyệt hành động và `send_email_mock` trả về trạng thái mô phỏng hợp lệ.
2. Cờ cấu hình `DEMO_EMAIL_LIVE` được đặt giá trị `1`.
3. Địa chỉ người nhận nằm chính xác trong danh sách cho phép `DEMO_EMAIL_ALLOWLIST`.
4. Tổng số thư gửi trong ngày chưa vượt quá hạn mức `DEMO_EMAIL_DAILY_LIMIT` và người vận hành phải trực tiếp bấm nút "Gửi" trên giao diện.

### Thu hồi khóa bảo mật sau buổi diễn

Ngay sau khi kết thúc buổi bảo vệ đồ án tốt nghiệp, người thực hiện phải truy cập trang quản lý Google Account, vào mục Security, chọn App passwords và xóa bỏ mật khẩu ứng dụng đã tạo. Thao tác này giúp ngăn ngừa mọi khả năng lạm dụng quyền gửi thư trong tương lai.

### Quản lý vết thực thi

Mọi dấu vết vận hành, dữ liệu gọi công cụ và bản ghi hộp thư chờ được lưu tự động tại thư mục `results/demo/<phiên>/`. Thư mục này phục vụ mục đích hậu kiểm, đã được liệt kê trong `.gitignore` và tuyệt đối không được đưa vào bất kỳ commit nào trên kho mã nguồn.

## 8. Xử lý sự cố thường gặp

| Sự cố | Biểu hiện | Nguyên nhân | Cách khắc phục |
|---|---|---|---|
| OmniRoute chưa bật | Ứng dụng báo lỗi không thể kết nối tới cổng 20128 khi khởi động | Tiến trình OmniRoute chưa được mở trước đó | Mở terminal riêng và khởi động tiến trình OmniRoute độc lập trên cổng 20128 |
| Lỗi chứng chỉ SSL | Trình thông dịch Python báo lỗi SSL CERTIFICATE_VERIFY_FAILED | Biến SSL_CERT_FILE chưa trỏ đúng file gộp chứng chỉ của proxy | Nối file certifi và build/gemini/proxy.crt thành file ca_bundle.pem rồi gán vào SSL_CERT_FILE |
| Gmail từ chối đăng nhập | Xuất hiện lỗi SMTPAuthenticationError khi bấm nút gửi thư | Chưa bật xác minh 2 bước, sai App Password hoặc tài khoản tổ chức khóa SMTP | Tạo lại App Password 16 ký tự mới và ưu tiên sử dụng tài khoản Gmail cá nhân |
| Hết hạn mức thư | Hộp thư chờ báo lỗi vượt quá số lượng gửi cho phép trong ngày | Số thư gửi đi trong ngày vượt mức DEMO_EMAIL_DAILY_LIMIT | Tăng tạm thời giá trị DEMO_EMAIL_DAILY_LIMIT trong file .env.demo nếu cần chạy tiếp |
| Mô hình phản hồi chậm | Lượt tương tác quay vòng lâu hoặc quá thời gian chờ 120 giây | Đường truyền mạng tới mô hình bị nghẽn hoặc OmniRoute quá tải | Theo dõi build/gemini/proxy_omni.log, khởi động lại proxy hoặc chuyển sang cờ --dry-run |
