# Cấu hình sinh thực tế — observation v1

Cập nhật2026-09-10. [Contract](../docs/architecture/phase5_generation_policy_v1_contract.md).
Đã thêm lớp ghi nhận quanh context backend cũ, auditor độc lập, HF entry riêng,
script kiểm nguồn thư viện và38 tests mới. Không sửa source đã chốt ởd07e914
hay auditor23files; không đổi decoding/publisher defaults/model placement.

## Trạng thái

38 tests mới đạt; full suite1.709pass/1optional native skip trong399,13s
(JUnit399,014s). Setup/Ruff/mypy257files/knowledge đạt.
[Release receipt](../experiments/manifests/phase5_generation_policy_v1_release_qa01.json)
ghim5sourcefiles/JUnit/hai static checks. Full XML:
`results/phase5_generation_policy_v1_release01_pytest.xml`.
Hai static checks trên wheel thật có byte-identical receipts:
`results/phase5_generation_policy_source_check01.json` và02.
Không import native Transformers/Torch, không tải/load weights, không GPU submit
hoặc Test/privateGT access trong bước này.
Sau fullsuite đã audit lại policy của cả2roles từ fake test artifacts,
cùng input cho cùng audit, token/cache summaries khớp controls không hook.
146frozenentries/296oldGPUraw/17overlay/4contextsource và sealed hashes nguyên vẹn.
Không job local/Kaggle mới đang chạy sau mốc CPU này.

## Cách hoạt động và bằng chứng

- Hook tạm ở đúng hai native methods, delegate đúng một lần và trả nguyên kết quả.
  Ghi submitted/publisher/defaults/resolved/length; gỡ hook trong finally, lỗi
  retire instance. Không gọi resolver thêm lần nữa để giả lập effective config.
- Mỗi role có5policyfiles riêng ngoài23probe files. PID/model IDs/config hashes
  và hook counts bind từng stage; error giữ partials, không semantic retry.
- Whitelist69public serialized fields, bỏ private special-token tensors không
  deepcopy/serialize. Test có tensor giả sẽ báo lỗi nếu vô tình bị copy.
- Test có/không hook cho cùng token/cache summaries trên fake model. Đo được
  publisher repetition_penalty1.1 được giữ và explicit do_sample=False thắng;
  không coi temperature/top_p còn trong config là chứng minh sampling.
- Auditor tự tính precedence và length, so exact inventory/values/hashes;18
  mutations bị từ chối. Errors/KeyboardInterrupt/missing/duplicate resolver đều
  khôi phục methods và không có completed policy receipt.
- Pinned wheel SHA821a9ff…, generation/utils.py SHAdde2df…; script AST xác nhận
  native global defaults và ba update calls theo đúng thứ tự. Không native execution.

## Việc tiếp theo và giới hạn

`source_authenticated=False` và `phase5_accepted=False` ở policy auditor. Cần
outer release audit ghép23probe+10policy files và xác thực publisher metadata
từ pinned model/snapshot; không dùng entered receipt tự khai làm nguồn độc lập.
Hook observation chỉ chốt resolution và length stages, không claim mọi runtime
mutation về sau. Chưa exact packaged/native compatibility hoặc GPU evidence.

Sau full QA/source push: kiểm actual native library hooks trong môi trường
isolated không weights, tạo wrapper/builder/release audit mới. Carry riêng native
progress-policy preflight; context stub không cover tqdm. Sau8tools/21Dummy/
resume+archive/expanded/PAX, kiểm quota/private mounts rồi submit một GPU identity.
Không sửa frozen benchmark, không lấy outputs để tune. Phase5 runtime/A4/final/
grouped Dev/freeze còn mở. Không cần tài khoản mới cho bước CPU hiện tại.
