# BrokerGuard Workspace

Ứng dụng web cho bản demo BrokerGuard: đăng nhập, phân quyền, hội thoại với agent, hiện quá trình xử lý và hộp thư chờ.
Thiết kế: [docs/project/app_design_v2.md](../docs/project/app_design_v2.md). Lõi agent dùng lại `src/react_agent/demo/`
(không sửa runtime nghiên cứu).

```
webapp/
  backend/     FastAPI, package brokerguard_api (cấu hình tool riêng trong backend/pyproject.toml)
    brokerguard_api/   settings, db (SQLite + migration), security (argon2id, phiên, CSRF, mã mời),
                       roles, deps, routers/, main
    manage.py          tạo tài khoản, mã mời, đặt lại mật khẩu
    tests/
  frontend/    React 19 + Vite + TypeScript, CSS variables + CSS Modules, không thư viện UI
    src/theme/         tokens sáng/tối, ThemeProvider
    src/api/           client (cookie phiên + header CSRF), kiểu dữ liệu
    src/components/    Button, TextField, Badge, SegmentedControl, Card, AppHeader, ThemeToggle, EmptyState
    src/features/      sources, chat (ProcessTimeline, CitationChip), control (OutboxCard)
    src/pages/         Login, Invite, Home, Conversation
    src/mocks/         dữ liệu mẫu, dùng tới khi có API hội thoại (W2)
```

## Chạy

Từ thư mục gốc của repo:

```bash
make webapp-install                     # pip install -r webapp/backend/requirements.txt, npm ci
make webapp-build                       # build frontend vào webapp/frontend/dist
.venv/bin/python webapp/backend/manage.py create-admin --username huy --display-name "Lâm Quang Huy"
make webapp-serve                       # http://127.0.0.1:8000
```

Phát triển giao diện: chạy `make webapp-serve` và `make webapp-dev` song song, mở http://127.0.0.1:5173 (Vite chuyển
`/api` sang cổng 8000). Kiểm tra: `make webapp-test`.

CSDL ở `results/webapp/app.db` (không track). Tài khoản khác: `manage.py create-user --role presenter|editor|viewer`
hoặc `manage.py create-invite --role viewer`. Mật khẩu luôn nhập qua getpass, ít nhất 10 ký tự.

## Trạng thái

W1 (đăng nhập, vai trò, phiên, CSRF, khóa tài khoản) và khung W3 (giao diện sáng/tối, các màn hình) đã có. Trang chủ và
màn hình hội thoại đang dùng dữ liệu mẫu. W2 sẽ nối API hội thoại, luồng sự kiện SSE và hộp thư chờ thật.
