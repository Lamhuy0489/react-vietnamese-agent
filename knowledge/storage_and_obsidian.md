# Lưu trữ và Obsidian cho đồ án

Cập nhật: 2026-09-20. [Trang bắt đầu](../START_HERE.md).

## Một bộ ghi chú, không thêm một bộ nhớ song song

Obsidian đọc trực tiếp Markdown trong repo; dùng để tìm kiếm, xem backlinks và
local graph giữa các ghi chú. Không cần graph database hoặc bản sao knowledge.
Codex tiếp tục đọc [status](current_status.md) và [handoff](handoff.md) theo
AGENTS.md; cài Obsidian không tự tạo trí nhớ lâu dài cho Codex.

| Loại | Nơi lưu | Quy tắc |
|---|---|---|
| Kế hoạch gốc | Word ở root, `plan/` | Giữ nguyên đầu vào nghiên cứu |
| Contract và acceptance | `docs/project/` | Nguồn chính thức; chỉ tăng nghiệm thu khi checks đạt |
| Trạng thái, bàn giao, bài học | `knowledge/` | Markdown trong Git; cập nhật đúng trang, không nhân bản status |
| Protocol, báo cáo diễn giải | `docs/architecture/`, `docs/evaluation/` | Liên kết tới manifest; phân biệt CPU, native, quality |
| Biên bản/hash đã chọn | `experiments/manifests/` | Giữ identity/version và cả thất bại; không sửa receipt cũ |
| Raw traces, logs, QA và package | `results/`, `logs/`, `build/` | Local, Git-ignore; immutable sau chạy; không phải bản sao lưu |
| Notebook/Dataset từ xa | [Sổ Kaggle](kaggle_resources.md) | URL thực, version, source, ngày quan sát, quyền và receipt |
| Cấu hình Obsidian | `.obsidian/`, `.trash/` | Local, Git-ignore; không chia sẻ plugin/config cá nhân |

GitHub là nguồn chuẩn cho code và tài liệu **đã commit/push**. Thay đổi local
chưa push không được coi là đã sao lưu trên GitHub. Kaggle là inference worker;
URL trong sổ không chứng minh tài nguyên còn truy cập được hôm nay.

## Dùng vault hiện có

1. Mở `START_HERE.md` trong vault root hiện tại và bookmark nếu muốn.
2. Trong Files and links, chọn relative paths và tắt Use Wikilinks cho ghi chú
   mới: dùng Markdown links, ví dụ `[Mục lục](README.md)`, để cùng đọc được trên
   GitHub và validator.
3. Tạo ghi chú phát triển ở `knowledge/`, liên kết từ README; đặt tiêu đề, ngày,
   phạm vi, bằng chứng, giới hạn và bước tiếp theo. Chỉ chép dữ kiện đã xác minh.
4. Không kéo raw dataset, log hoặc credentials vào ghi chú. Không đổi tên/di chuyển
   protocol hay nguồn đã frozen bằng giao diện vault: có thể làm hỏng hash/package.
5. Sau cập nhật chạy `make knowledge-check`. Check này kiểm liên kết nội bộ và
   cấu trúc handoff, **không** kiểm sự đúng đắn khoa học, anchor, cloud backup
   hoặc quyền truy cập URL từ xa.

Cấu hình cá nhân đang có được giữ nguyên; không cài plugin, không bật đồng bộ,
không cấu hình tự động commit trong lần củng cố này.

## Cảnh báo vault root và đồng bộ

Repo root có cả vùng credentials và dữ liệu nghiên cứu hạn chế. Không bật
Obsidian Sync, Publish, cloud backup toàn vault hoặc plugin AI đọc toàn repo
trước khi có phạm vi chia sẻ an toàn. Ngày 2026-09-20, cấu hình core plugin có
`sync: true`; điều này **không chứng minh** đã đăng nhập/kết nối remote vault.
Chưa kiểm trạng thái đồng bộ trong ứng dụng; chủ máy cần kiểm Settings → Sync.

Có thể dùng Excluded files để giảm nhiễu tìm kiếm/graph với `credential kaggle/`,
`data/`, `results/`, `build/`, `logs/`, `.venv/` và `.trash/`.
Đây chỉ là lựa chọn hiển thị, **không phải kiểm soát truy cập hay chặn sync**.
`.gitignore` cũng chỉ điều khiển Git; không bảo vệ khỏi plugin hoặc dịch vụ khác.
Không tự di chuyển/xóa credentials, sửa vault settings hay tạo vault lồng nhau.

## Raw evidence và phục hồi

Manifest chứa hash, không chứa toàn bộ raw; mất raw thì không thể tái tạo bằng
hash. Hai tập đang cần giữ để tiếp tục Phase 5:

- CPU teardown: `results/phase5_teardown_cpu_controls02`, hai file
  `results/phase5_teardown_cpu_audit01.json` / `phase5_teardown_cpu_audit02.json`,
  `results/phase5_teardown_cpu_qa01`; giữ cả preparation01 bị loại.
  [Close receipt](../experiments/manifests/phase5_teardown_cpu_close01.json),
  [QA receipt](../experiments/manifests/phase5_teardown_cpu_qa01.json).
- Native constrained GPU: `results/phase5_constrained_gpu_monitor02`,
  `results/phase5_constrained_gpu_audit01.json`,
  `results/phase5_constrained_gpu_report01` và package gắn source trong
  [audit receipt](../experiments/manifests/phase5_constrained_gpu_audit01.json).

Đây là danh sách ưu tiên hiện hành, không phải inventory đầy đủ của cả đồ án.
Chưa tạo bản sao ngoài máy trong lần này; chưa có đích lưu riêng được chủ máy chọn.
Trước khi dọn máy, chọn ổ riêng hoặc kho riêng tư có quyền phù hợp, rồi:

1. Chọn đúng thư mục raw theo manifest; không nén toàn repo hoặc kèm credentials,
   private ground truth, payload Test hay model weights không cần thiết.
2. Quét secrets trong phạm vi xuất; lập inventory/hash, copy không ghi đè raw.
3. Kiểm hash lại bản copy và thử auditor trên bản phục hồi; không chạy lại model
   chỉ để thay thế dữ liệu đã mất. Ghi thiếu dữ liệu nếu không phục hồi được.
4. Ghi ngày, người giữ/quyền, vị trí bản sao, checksum và kết quả restore vào một
   receipt mới; không ghi khóa/mật khẩu. Chỉ khi đó mới ghi “đã sao lưu”.

## Kết thúc mỗi phần việc

Cập nhật handoff: việc đang làm, một bước kế tiếp cụ thể, checks/artifacts và
quyền còn thiếu. Cập nhật sổ Kaggle chỉ khi có submission hoặc terminal audit
mới. Gom implementation + tests + evidence + memory thành phần việc hoàn chỉnh;
commit sau QA, không commit mỗi lần ghi chú. Không amend source đã dùng thực nghiệm.

Tham khảo chính thức: [cách Obsidian lưu dữ liệu](https://help.obsidian.md/Files+and+folders/How+Obsidian+stores+data),
[Files and links, Excluded files và plugin settings](https://help.obsidian.md/settings).
