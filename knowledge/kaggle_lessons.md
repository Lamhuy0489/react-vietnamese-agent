# Ghi chú Kaggle Phase 1

## Cập nhật v1.1 — 2026-09-06

Khi tạo kernel mới, `id` và slug sinh từ `title` cần nhất quán. Lần v1.1 đầu
server cảnh báo rồi tạo handle theo title. Đó không phải inference failure:
dùng handle từ output push cho status/logs/output, không push lại để đổi tên.

Phase 2 còn gặp lỗi fault adapter không delegate `validate_arguments`, khiến
parser dùng generic BaseModel dù unit test execute trực tiếp vẫn pass. Vì vậy
preflight mới gọi tool qua AgentRuntime/parser/Broker và có recovery case.

Runner cũ chỉ ghi results cuối suite nên mất danh sách task hoàn thành khi lỗi
giữa chừng. Runner v1.1 lưu checkpoint mỗi task, từ chối identity/hash mismatch,
và không retry semantic failure. Bundle preflight kiểm tra cả archive/expanded
mount, 8 tool, Dummy đủ 21 task và resume trước upload. GPU kiểm tra bằng phép
tính tensor thực, không chỉ `cuda.is_available()`.

Skill `.agents/skills/experiment-repro/references/kaggle-preflight.md` đã lưu
quy trình; không sửa skill global để tránh áp điều kiện repo lên dự án khác.

Ba attempt đầu là lỗi hạ tầng và đều dừng trước inference:

1. Kaggle tự bung file `tar.gz` của Dataset thay vì mount nguyên archive.
2. Nội dung bung nằm trong một thư mục tên sinh tự động, không ở mount root.
3. Python subprocess không tự có `<repo>/src` trong `PYTHONPATH`.

Wrapper hiện tại xử lý cả archive và expanded mount, tìm đúng một package root,
kiểm tra SHA-256 từng file tracked, chấp nhận `Transformers` khác hoa/thường,
xác minh các file model bắt buộc, rồi truyền `PYTHONPATH` và frozen commit cho
mọi subprocess.

Quy tắc giữ nguyên:

- Chỉ một account cho authoritative run; không gộp quota nhiều account.
- Retry chỉ khi lỗi hạ tầng; không retry semantic failure để lấy điểm đẹp.
- Dataset/kernel đều private, model revision cố định, internet tắt.
- Chạy `make kaggle-bundle-validate` trước mọi lần upload.
## Measured pilot metadata — 2026-09-06

SaveKernel returned HTTP 409 when the kernel title matched the Dataset name.
The standard CLI hid the detailed server message; the API HTTP response body
identified the collision. Use distinct Dataset/kernel slugs and titles. CPU
machine_shape should be omitted/null, not the literal string `None`.
Failed SaveKernel requests are not completed or failed inference attempts.

## Measured pilot completion lessons — 2026-09-06

- Real Gemma 4/Qwen 7B tokenizers/configs and tiny random generation passed on
  a Kaggle CPU kernel before GPU submission. Local Intel macOS PyTorch 2.2.2
  is not a substitute for validating this newer Transformers runtime.
- Offline wheelhouse pins Transformers 5.5.0 and compatible dependencies with
  hashes; provide CPython 3.11/3.12 regex wheels for the images in scope.
  Do not replace Kaggle's Torch/CUDA stack blindly. Both measured runs actually
  reported Torch 2.10.0+cu128, Transformers 5.5.0, tokenizers 0.22.2,
  accelerate 1.10.1 and two Tesla T4 GPUs.
- Both GPU kernels completed on v1 after CPU/bundle preflight. Record this
  separately from the earlier metadata 409 calls, which never ran inference.
- `kernels output --page-size 1000` returned HTTP 400 in this session;
  `--page-size 100` worked. This is observed behavior, not a universal API limit.
- Select only bundle info and run artifacts when downloading. Installing the
  offline dependencies under `/kaggle/working` causes thousands of dependency
  files to appear in exported outputs; CLI pagination can remain slow even
  with filename filtering. Check required checkpoint coverage, not CLI silence.
- Never download over audited files. Retain manifest hashes; regenerate tables
  from saved measurements without spending another GPU attempt for low scores.
# Phase 5 guard preparation — 2026-09-08

- Bundle02 local preflight bắt `validation.__init__` eager-import pool validator
  khi chỉ mang environment validator. Bundle03 bỏ initializer khỏi archive,
  dùng namespace directory; both isolated layouts pass. Không sửa source cũ,
  không mang authoring/pool modules vào GPU để che missing import.
- Kaggle CLI nằm ở `python3 -m kaggle` (2.2.4), không phải `.venv/bin/kaggle`.
  Help/version hoạt động; không cần cài lại chỉ vì thiếu entrypoint trong venv.
- Python.org Python 3.11 cục bộ gặp `CERTIFICATE_VERIFY_FAILED` khi dùng CA mặc
  định với HF. Curl TLS-verified đọc được metadata. Acquisition dùng explicit CA
  bundle hợp lệ từ certifi; **không dùng ssl unverified/curl insecure**.
- Guard snapshot pin cần metadata upstream độc lập: Git blob SHA-1 gồm header
  `blob <size>\0`; LFS weights dùng publisher SHA-256. HF commit label tự khai
  cộng hash tự tính không đủ chứng minh publisher. Không tải model từ branch main.
- Quota đã đọc cho tài khoản pilot `huylmhuhu`: GPU còn 29,49h ngày 2026-09-08.
  Đây là snapshot quota, không reservation và không lý do đổi accounts để bypass.
- Bundle guard mới đang kiểm chứng môi trường venv sạch/offline, both layouts,
  no inherited development imports. Không coi unit tests là GPU readiness.
