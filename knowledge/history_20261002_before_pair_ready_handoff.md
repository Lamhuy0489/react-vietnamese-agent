# Bàn giao phiên làm việc

Cập nhật: 2026-10-02. **Phase 5 chưa accepted**; Test/private GT vẫn khóa.

## Đang làm

**Ưu tiên mới:** owner đã yêu cầu chạy public guard trên meanalways. Source
77bc456469ec58fb3543931066f365b15292f5f3 đã push; package
`build/kaggle/collaborator_guard_public_20261002_01` preflight4/4; guard v3 đã
submit và RUNNING, chờ authenticated discovery. Agent v1 vẫn READY; không
submit agent từ package mới. Bước xin quyền Kaggle bên dưới đã có phương án
thay thế được owner duyệt, không phải blocker hiện hành. Không suy API từ RUNNING.
62tests đạt, setup/Ruff/mypy631. Public weights cùng hash historical, nhưng
config/tokenizer khác; khai báo epoch mới, không gộp native kết quả lịch sử.


Owner yêu cầu trực tiếp setup/chạy hai worker trên hai tài khoản đã chỉ định.
Đã submit private T4: lamhuy8904/Qwen3-8B agent v1 và meanalways/Llama3.2-3B
 guard v1. Agent được authenticated READY, source e4078d7, kết nối local0600.
Guard v1 ERROR EXACT_MODEL_MOUNT_MISSING. Sửa resolver, 54 tests đạt, commit
 d6cc4fcee37b009751b94a7535b12690e257166c đã push cùng nhánh worker freeze;
chỉ submit guard v2, giữ agent v1. Guard v2 vẫn ERROR, log xác nhận input trống.
Bản sửa layout không giải quyết được quyền model; không claim đã fix startup.

Kiểm tra file model Llama trả HTTP403 cho **cả meanalways và lamhuy8904**.
Metadata công khai đọc được không chứng minh quyền đọc trọng số. Không đổi
model/tài khoản hoặc retry GPU để bỏ qua quyền truy cập. Agent API kiểm lại
READY trong lượt cuối; không suy uptime về sau. Chưa pair API, chưa native Dev mới.

## Bước tiếp theo

**Nguồn thay thế mới kiểm tra:** [Unsloth public Llama](../docs/evaluation/phase5_llama_public_source_20261002.md)
không gated, anonymous HEAD200; revision006f5dcd1393c3add266de40994ba96225e9689d.
Có thể đề xuất tải snapshot public vào guard thay Kaggle mount; chưa sửa source,
chưa download/GPU. Cần source/fingerprint/session mới và kiểm tương đương trước
native run; không phải mở quyền của tài khoản trên Kaggle. Các bước quyền Kaggle
bên dưới là phương án giữ nguồn cũ, không phải con đường duy nhất.

1. Chủ tài khoản giải quyết quyền Llama trên Kaggle (Request Access/điều khoản
   nếu được yêu cầu). Browser tool lỗi khởi động; chưa quan sát/nộp biểu mẫu.
   Không cần gửi key qua chat. Câu hỏi async về quyền meanalways còn chờ trả lời.
2. Kiểm tra ListModelInstanceVersionFiles thành công cho đúng account/model
   trước GPU. Đã thêm verify_model_access vào deployment helper và regression tests.
3. Chỉ sau quyền đọc file được xác nhận: gói/session guard mới, exact preflight,
   submit một lần, source pull/hash, encrypted discovery và model/boot probe.
   Agent v1 có thể giữ nếu còn READY; chốt riêng source/boot mỗi role trước run.
4. Ghép snapshot kết nối mới rồi chạy scripts/run_phase5_native_closure_v2.py
   trên epoch mới, khai báo nguồn/config/input trước inference, checkpoint mỗi
   condition. Không resume hai epoch v1 uncertain; không đổi held-out Test.
5. Đối chiếu 20 DoD bằng evidence.84 synthetic conditions không tự accept Phase 5.

## Bằng chứng

- [Deployment receipt](../experiments/manifests/phase5_api_deployment_20261002.json).
- [lamhuy8904 Llama file access 403](../build/operations/phase5_pair_20261002/lamhuy_llama_access_20261001T180657Z.json).
- [meanalways Llama file access 403](../build/operations/phase5_pair_20261002/model_access_20261001T180149Z/receipt.json).
- [Mount repair scope](../docs/evaluation/phase5_worker_mount_repair_20261002.md).
- Guard v1/v2 và agent v1 source remote trùng byte gói tương ứng; v2 preflight4/4.
- 54 focused tests trước commit; sau access admission:18 access/mount tests và
  21 access/mount/native-runner tests đạt. Setup/Ruff/mypy630 đạt; full pytest
  không rerun. Host deployment admission sửa mới còn working-tree.

## Giới hạn

API Qwen đã có; API Llama chưa có. Guard v2 chết trước load model do không có
input; authenticated model-files request bị403. Không native Dev mới, không
acceptance mới. Bản sửa resolver chỉ tăng tương thích layout, chưa chứng minh
sửa nguyên nhân quyền. Không có tiến trình monitor tự động. Worker agent có
lifetime tối đa8giờ; private key/API keys chỉ giữ local ignored, không ghi memory.

[Lịch sử trước source freeze](history_20261001_before_worker_freeze_handoff.md).
