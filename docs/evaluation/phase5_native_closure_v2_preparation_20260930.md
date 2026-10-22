# Native runner v2 — chuẩn bị và giới hạn compute

Cập nhật 2026-09-30. Phase5 chưa accepted. Không Test/private GT.

- Runner mới giữ manifest/source snapshot trước request, pin model/worker boot,
  config/generation và actual constructed environment. Resume chỉ chạy condition
  chưa bắt đầu; checksum sai, started-only hoặc journal uncertain đều chặn.
- 15 kiểm thử runner/lifecycle/entrypoint đạt, gồm toàn lịch84conditions qua
  synthetic v3 transport. Đây không phải native/model-quality evidence.
- 65 kiểm thử transport/recovery/package/deployment đạt. Quota0 chặn trước
  submit; package tamper và submission đã bắt đầu không được tự submit lại.
- Entry point truyền discovery failure/tunnel exit về owner và đóng server;
  shutdown signal retire/cancel không được tuyên bố GPU đã dừng nếu còn active.
- Gói `build/kaggle/request_worker_v3_candidate_20260930_01` preflight4/4,
  chưa freeze Git hoặc submit. Ruff/mypy629 đạt. Full pytest chưa hoàn tất ở lượt
  trước, không tuyên bố toàn kho đạt.
- Native scorer tách `not_exercised` và unsafe dispatch/PRE block; không buộc
  model thực hiện unsafe proposal mới được tính safe, không tự accept20DoD.

Lần CLI kiểm quota trước lượt bị ngắt trả: buiquocviet38.60hused/0hremaining,
 huylmhuhu38.42hused/0hremaining; refreshAt2026-10-03T00:00:00. Đây là quan sát
đã có, chưa phải health/availability hiện tại. Lệnh kiểm status bị ngắt không
có receipt hoàn tất; không suy READY/RUNNING/COMPLETE. Hai credential còn lại
được nhận diện cục bộ là lamhuy8904 và meanalways; không đọc quota hoặc submit.

Không luân phiên tài khoản để vượt quota. Đã xác minh
[điều khoản Kaggle](https://www.kaggle.com/terms), mục3 cấm một người vận hành
nhiều tài khoản active. Chờ quota hoặc dùng nguồn compute được phép khác;
không tự thay model/runtime hoặc chạy Test để bù thiếu evidence.

Bước tiếp: kiểm end-to-end discovery/native khi có compute hợp lệ, freeze/push
source và chạy đúng protocol v2. Script deploy vẫn là candidate, chưa có native
source-pull hoặc round-trip encrypted discovery evidence. Không đề nghị người
dùng gửi lại key. Chưa có notebook/Dataset URL/version mới.

[Receipt và source hashes](../../experiments/manifests/phase5_native_closure_v2_preparation_20260930.json).
