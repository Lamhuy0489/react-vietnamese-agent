# Kế hoạch v2: BrokerGuard Workspace (ứng dụng web hoàn chỉnh)

Cập nhật: 2026-11-22. Trạng thái: **kế hoạch, chưa có code.** Thay giao diện Gradio của
[kế hoạch v1](deployment_plan_v1.md). Lõi `src/react_agent/demo/` (session, trace, outbox, Gmail) giữ nguyên và
được dùng lại. Quyết định gốc: [decision log 2026-11-22](decision_log.md).

## 1. Mục tiêu

Một ứng dụng web có đăng nhập và phân quyền. Bố cục tham khảo NotebookLM: **nguồn tài liệu ở cột trái, hội thoại ở
giữa, bảng kiểm soát ở cột phải**. Người dùng ra lệnh cho agent như khi chat với trợ lý AI. Với mỗi câu trả lời, giao
diện hiện **quá trình xử lý** theo thời gian thực: agent đọc tài liệu nào, truy vấn gì, đề xuất gửi thư ra sao,
BrokerGuard cho qua hay chặn và vì sao. Lịch sử hội thoại được lưu theo tài khoản. Giao diện có chế độ sáng và tối, dùng
chữ thay cho emoji và biểu tượng, phong cách tối giản như một sản phẩm phần mềm, không theo kiểu "AI" (không gradient tím,
không hiệu ứng lấp lánh).

Giữ nguyên các ràng buộc của v1: không sửa file pinned, không dùng dữ liệu Dev/Test, mỗi tin nhắn là một task độc lập,
thư thật chỉ đi qua hộp thư chờ.

## 2. Các quyết định chính

| # | Quyết định | Lý do |
|---|---|---|
| D1 | **Backend FastAPI** (`src/react_agent/webapp/`), gọi lõi `react_agent.demo` | Cùng tiến trình Python với runtime, dùng lại được code và test đã có. FastAPI đã có sẵn trong `.venv` |
| D2 | **Frontend React + Vite + TypeScript** (`web/`). Style bằng CSS variables (design tokens) + CSS modules, không dùng thư viện UI nặng. Bản build tĩnh được FastAPI phục vụ | Toàn quyền về thiết kế. Một tiến trình duy nhất khi chạy demo. Node 22 đã có trên máy |
| D3 | **Luồng sự kiện SSE** `GET /api/turns/{id}/events`: backend đọc `trace_security.jsonl` trong lúc runtime chạy và đẩy từng bước | Hiện quá trình xử lý theo thời gian thực mà không đổi runtime |
| D4 | "Quá trình xử lý" chỉ gồm **hành động quan sát được** (tool, tham số, kết quả rút gọn, quyết định cổng, lý do). **Không hiện chain-of-thought** | Bất biến của dự án: không lưu hay yêu cầu suy luận ẩn. Hiện bước nào cũng có trong trace |
| D5 | **SQLite** `results/webapp/app.db` (không track) qua `sqlite3` thư viện chuẩn: users, sessions, conversations, messages, outbox, audit_log | Nhẹ, không cần server CSDL, dễ xóa sạch sau buổi demo |
| D6 | **Mật khẩu băm argon2id** (`argon2-cffi`). Phiên đăng nhập bằng cookie `HttpOnly; SameSite=Strict`. Chống CSRF bằng header đôi. Giới hạn số lần đăng nhập sai | Chuẩn tối thiểu cho ứng dụng có tài khoản |
| D7 | **Không tự đăng ký công khai.** Quản trị viên tạo tài khoản, hoặc phát **mã mời** có hạn dùng. Tài khoản quản trị đầu tiên tạo bằng lệnh `scripts/webapp_admin.py create-admin` | Demo có gửi thư thật, không cho người lạ tự lập tài khoản |
| D8 | **4 vai trò** (mục 4). Quyền gửi thư thật chỉ có ở Quản trị và Người trình diễn | Tách người xem khỏi hành động có tác động ra ngoài |
| D9 | **Trích dẫn nguồn** như NotebookLM: câu trả lời gắn số [1], [2] trỏ tới tài liệu agent đã đọc (`doc_read` trong trace). Bấm vào thì mở tài liệu ở cột trái | Lấy từ trace, không cần model sinh trích dẫn |
| D10 | Chạy local `127.0.0.1:8000`. Truy cập từ xa (tùy chọn, chỉ trong buổi demo) qua Cloudflare Tunnel, bắt buộc đăng nhập | Không mở cổng công khai lâu dài |
| D11 | Giao diện Gradio v1 giữ lại tới khi v2 đạt nghiệm thu, sau đó xóa | Luôn có một bản chạy được |

## 3. Bố cục màn hình

### 3.1 Trang đăng nhập
Một khung giữa trang: tên ứng dụng, ô tài khoản, ô mật khẩu, nút "Đăng nhập", liên kết "Dùng mã mời". Không ảnh nền.

### 3.2 Trang chủ: danh sách hội thoại
```
┌──────────────────────────────────────────────────────────────────────────┐
│ BrokerGuard Workspace                       [Sáng/Tối]  Lâm Quang Huy ▾  │
├──────────────────────────────────────────────────────────────────────────┤
│ Hội thoại                                            [ Hội thoại mới ]   │
│ ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐     │
│ │ Lịch bảo vệ đồ án  │ │ Học bổng SV2026... │ │ Thử kịch bản A0    │     │
│ │ 6 lượt · BG v3     │ │ 2 lượt · BG v3     │ │ 4 lượt · A0        │     │
│ │ 22/11 09:40        │ │ 21/11 23:58        │ │ 21/11 23:10        │     │
│ └────────────────────┘ └────────────────────┘ └────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Màn hình hội thoại (3 cột, như NotebookLM)
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ‹ Hội thoại   Lịch bảo vệ đồ án     Chế độ: [BrokerGuard v3 | A0]   [Sáng/Tối]  Huy ▾ │
├──────────────────┬───────────────────────────────────────────┬───────────────────────┤
│ NGUỒN (60)       │                                           │ KIỂM SOÁT             │
│ [Tìm nguồn    ]  │  Bạn                                      │ Hộp thư chờ (2)       │
│ Lọc: Tất cả ▾    │  Tìm lịch bảo vệ tháng 12 rồi gửi tóm     │ ┌───────────────────┐ │
│                  │  tắt cho huy.lqforwork@gmail.com           │ │ huy.lqforwork@... │ │
│ ▪ Lịch bảo vệ    │                                           │ │ Lịch bảo vệ 12/26 │ │
│   S0 · Tin cậy   │  Trợ lý · BrokerGuard v3                  │ │ Chờ xác nhận      │ │
│ ▪ Hướng dẫn nộp  │  ┌ Quá trình xử lý · 4 bước · 12 giây ──┐ │ │ [Xem] [Gửi] [Hủy] │ │
│   S0 · Tin cậy   │  │ 1 Tìm tài liệu "bảo vệ đồ án 12/2026"│ │ └───────────────────┘ │
│ ▪ Biên bản điểm  │  │ 2 Đọc "Lịch bảo vệ đồ án..."  [1]    │ │                       │
│   S2 · Mật       │  │ 3 Soạn thư tới huy.lqforwork@...     │ │ Lượt này              │
│ ▪ Tin tuyển dụng │  │   BrokerGuard: Cho qua               │ │ Bước: 4 · Chặn: 0     │
│   S0 · Ngoài     │  └──────────────────────────────────────┘ │ Model: gemini-3-flash │
│ ...              │  Lịch bảo vệ diễn ra 08:00 ngày 18/12 tại │ Thời gian: 12 giây    │
│                  │  phòng B1-302 [1]. Thư tóm tắt đang chờ   │                       │
│ [Thêm nguồn]     │  xác nhận ở Hộp thư chờ.                  │ Nhật ký kiểm soát     │
│ (Biên soạn)      │                                           │ 09:41 Cho qua send... │
│                  ├───────────────────────────────────────────┤ 09:38 Chặn send...    │
│                  │ [ Nhập yêu cầu cho agent...        ][Gửi] │                       │
└──────────────────┴───────────────────────────────────────────┴───────────────────────┘
```

- **Cột Nguồn:** danh sách tài liệu, có nhãn độ nhạy cảm (S0/S2) và độ tin cậy (Tin cậy/Ngoài) dạng chữ trên nền màu
  nhạt. Bấm vào thì xem nội dung. Tài liệu agent đã đọc trong lượt hiện tại được đánh dấu. Người Biên soạn thêm được tài
  liệu (nhãn mặc định: Ngoài, không tin cậy).
- **Khung chat:** tin nhắn của người dùng căn phải trên nền xám nhạt. Câu trả lời căn trái, không có khung bao. Phía trên
  mỗi câu trả lời là khối **"Quá trình xử lý"**: trong lúc chạy thì mở và cập nhật từng bước, xong thì tự thu gọn, bấm để
  mở lại. Bước bị chặn có viền trái màu đỏ và dòng lý do. Câu trả lời có trích dẫn [n].
- **Cột Kiểm soát:** hộp thư chờ (thẻ thư, trạng thái, nút Gửi/Hủy theo quyền), số liệu của lượt (số bước, số lần chặn,
  model, thời gian), nhật ký kiểm soát (các quyết định cổng gần đây).
- **Thanh trên:** tên hội thoại (sửa được), công tắc chế độ BrokerGuard v3 / A0 dạng nút đoạn, nút Sáng/Tối, menu tài khoản.
- **Màn hình hẹp (< 1100 px):** hai cột bên thành ngăn trượt, mở bằng nút chữ "Nguồn" và "Kiểm soát".

### 3.4 Trang Quản trị (chỉ vai trò Quản trị)
Các tab: Người dùng (tạo, khóa, đổi vai trò, đặt lại mật khẩu), Mã mời, Danh sách địa chỉ cho phép, Cài đặt (model,
hạn mức thư, công tắc gửi thật), Nhật ký kiểm toán.

## 4. Vai trò và quyền

| Quyền | Quản trị | Người trình diễn | Biên soạn | Người xem |
|---|---|---|---|---|
| Chat, xem quá trình xử lý | Có | Có | Có | Có |
| Đổi chế độ A0 / BrokerGuard v3 | Có | Có | Có | Không (chỉ v3) |
| Xem hộp thư chờ | Có | Có | Có | Có |
| **Bấm "Gửi thật"** | Có | Có | Không | Không |
| Thêm/sửa tài liệu nguồn | Có | Không | Có | Không |
| Xem hội thoại của người khác | Có | Không | Không | Không |
| Quản lý tài khoản, mã mời, allowlist, cài đặt | Có | Không | Không | Không |

Mọi hành động gửi thật, đổi vai trò, sửa allowlist, thêm tài liệu đều ghi vào `audit_log` (ai, lúc nào, cái gì). Không
ghi mật khẩu hay nội dung bí mật.

## 5. Hệ thống thiết kế

**Nguyên tắc:** tối giản, nhiều khoảng trắng, một màu nhấn. Trạng thái thể hiện bằng **chữ + màu**, không bằng emoji
hay biểu tượng. Không gradient, không bóng đổ đậm, không hiệu ứng lấp lánh. Bo góc nhỏ (6 px). Chuyển động ngắn
(150 ms), tắt khi người dùng bật `prefers-reduced-motion`.

**Chữ:** `Be Vietnam Pro` (thiết kế cho tiếng Việt, dấu rõ), tự host trong `web/public/fonts` để chạy offline. Chữ đơn
cách `JetBrains Mono` cho tham số tool và mã. Cỡ chữ: 13 / 14 (thân) / 16 / 20 / 24, dòng 1,5.

**Màu (CSS variables, dark theo `prefers-color-scheme` và nút chuyển, lưu lựa chọn trong `localStorage`):**

| Token | Sáng | Tối | Dùng cho |
|---|---|---|---|
| `--bg` | `#FAFAF9` | `#111110` | Nền trang |
| `--surface` | `#FFFFFF` | `#1A1A19` | Cột, thẻ |
| `--surface-2` | `#F4F4F2` | `#232321` | Tin nhắn người dùng, ô nhập |
| `--border` | `#E4E4E0` | `#2E2E2B` | Đường kẻ |
| `--text` | `#1C1C1A` | `#EDEDEA` | Chữ chính |
| `--text-muted` | `#6B6B66` | `#9A9A94` | Chữ phụ |
| `--accent` | `#1F5F8B` | `#6AA9D8` | Nút chính, liên kết, trích dẫn |
| `--allow` | `#1E7A46` | `#5DBB85` | "Cho qua", "Đã gửi" |
| `--deny` | `#B42318` | `#F07A6E` | "Chặn", lỗi |
| `--pending` | `#A15C07` | `#E3A649` | "Chờ xác nhận" |
| `--s2` | `#7A2E8E` | `#C590D4` | Nhãn dữ liệu mật S2 |

Mọi cặp chữ và nền phải đạt tương phản WCAG AA (≥ 4,5:1). Có script kiểm ở bước W6.

**Thành phần dùng chung** (`web/src/components/`): Button (chính, phụ, nguy hiểm), SegmentedControl, Badge (chữ + màu),
Card, Drawer, Dialog xác nhận, ProcessTimeline, MessageBubble, CitationChip, SourceItem, OutboxCard, DataTable, Toast,
EmptyState. Điều hướng bằng bàn phím đầy đủ, có `aria-live` cho khối quá trình đang chạy.

## 6. API

| Phương thức | Đường dẫn | Quyền |
|---|---|---|
| POST | `/api/auth/login`, `/api/auth/logout`, `/api/auth/redeem-invite` | Công khai / đã đăng nhập |
| GET | `/api/me` | Đã đăng nhập |
| GET/POST | `/api/conversations`, `GET/PATCH/DELETE /api/conversations/{id}` | Chủ hội thoại (Quản trị: tất cả) |
| POST | `/api/conversations/{id}/turns` → `{turn_id}` | Đã đăng nhập (Người xem: chỉ V3) |
| GET | `/api/turns/{id}/events` (SSE: `step`, `decision`, `final`, `outbox`, `error`, `done`) | Chủ hội thoại |
| GET | `/api/sources`, `/api/sources/{doc_id}`, POST `/api/sources` | Đã đăng nhập / Biên soạn |
| GET | `/api/outbox`, POST `/api/outbox/{id}/send`, `/api/outbox/{id}/reject` | Đã đăng nhập / Quản trị, Trình diễn |
| GET/POST/PATCH | `/api/admin/users`, `/api/admin/invites`, `/api/admin/allowlist`, `/api/admin/settings`, GET `/api/admin/audit` | Quản trị |

Cổng gửi thật vẫn nằm trong `Outbox.confirm` của lõi. API chỉ thêm kiểm tra vai trò và ghi kiểm toán.

## 7. Cấu trúc thư mục

```
src/react_agent/demo/            lõi (đã có): session, trace_view, outbox, gmail_sender, corpus, config
src/react_agent/webapp/
  main.py                        tạo app FastAPI, phục vụ web/dist, middleware bảo mật
  db.py                          sqlite3, migration đơn giản theo version
  auth.py                        argon2, phiên, CSRF, giới hạn đăng nhập sai
  roles.py                       vai trò và bảng quyền (mục 4)
  routes/                        auth.py, conversations.py, turns.py, sources.py, outbox.py, admin.py
  events.py                      đọc trace khi runtime đang chạy, phát SSE
  schemas.py                     model pydantic của API
web/                             React + Vite + TypeScript
  src/theme/tokens.css           design tokens sáng/tối (mục 5)
  src/components/                thành phần dùng chung
  src/features/                  auth, conversations, chat, sources, outbox, admin
  src/api/                       client gọi API, SSE
  public/fonts/                  Be Vietnam Pro, JetBrains Mono (tự host)
scripts/run_webapp.py            build check, chạy uvicorn 127.0.0.1:8000
scripts/webapp_admin.py          create-admin, reset-password, create-invite
tests/webapp/                    test API, quyền, SSE, bảo mật
results/webapp/                  app.db, log (không track)
```

Phụ thuộc Python thêm vào `requirements-demo.txt`: `fastapi`, `uvicorn`, `argon2-cffi`. **Không sửa `pyproject.toml`**
(nằm trong seal `release_v2`). Phụ thuộc frontend ghi trong `web/package.json` + `package-lock.json`. `web/node_modules`
và `web/dist` không track.

## 8. Các bước làm

| Bước | Việc | Nghiệm thu |
|---|---|---|
| **W1** Nền backend | `webapp/` main, db, auth, roles, `webapp_admin.py create-admin`. Test đăng nhập, phiên, CSRF, khóa sau nhiều lần sai | Test qua. Mật khẩu chỉ lưu dạng băm argon2id |
| **W2** API hội thoại + SSE | conversations, turns, events (đọc trace khi đang chạy), sources, outbox với kiểm quyền | Test: Người xem không gửi được thư thật và không đổi được sang A0. SSE phát đủ các bước của một lượt chạy thử |
| **W3** Khung frontend + design system | Vite, tokens sáng/tối, font, các thành phần dùng chung, trang đăng nhập, trang chủ | Owner duyệt giao diện sáng và tối trên máy |
| **W4** Màn hình hội thoại | 3 cột, ProcessTimeline trực tiếp, trích dẫn, hộp thư chờ, nhật ký kiểm soát, màn hình hẹp | Chạy đủ `data/demo/scenarios.md` với Gemini, gửi thật một thư từ giao diện mới |
| **W5** Quản trị | người dùng, mã mời, allowlist, cài đặt, kiểm toán | Tạo đủ 4 vai trò, kiểm bảng quyền bằng tay và bằng test |
| **W6** Hoàn thiện | kiểm tương phản AA, bàn phím, `prefers-reduced-motion`, xử lý lỗi mạng/model, README chạy demo, xóa bản Gradio | Tổng duyệt buổi demo 5 phút trên máy owner |

Thứ tự: W1 → W2 → W3 (song song với W2 được) → W4 → W5 → W6.

## 9. Chia việc

- **Claude:** backend (auth, quyền, SSE, nối lõi), test bảo mật, review mọi phần Gemini viết.
- **Gemini qua proxy Antigravity:** khung React, các thành phần giao diện theo tokens ở mục 5, trang quản trị, nội dung
  README. Mỗi phần có prompt tự đủ, kết quả đưa vào worktree, Claude kiểm, chạy lint/test rồi mới gộp.
- **Owner:** duyệt giao diện ở W3 và W4, tạo tài khoản cho Minh và thầy, viết tài liệu injection (M4 cũ).

## 10. Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Lộ tài khoản khi mở truy cập từ xa | Chỉ bật tunnel trong buổi demo. Đăng nhập bắt buộc. Mật khẩu mạnh. Khóa tài khoản sau 5 lần sai |
| Người xem bấm gửi thư thật | Kiểm vai trò ở API (không chỉ ẩn nút), có test |
| SSE đứt giữa chừng | Lượt vẫn chạy xong ở backend. Frontend tải lại kết quả từ `/api/conversations/{id}` |
| Frontend phình to, khó bảo trì | Không dùng thư viện UI nặng. Thành phần ít, dùng chung tokens |
| Hiểu nhầm "quá trình xử lý" là suy luận của model | Đặt tên "Quá trình xử lý". Chỉ hiện hành động và quyết định cổng, ghi rõ trong README |
