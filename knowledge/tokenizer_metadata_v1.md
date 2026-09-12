# Xác thực tokenizer cho ordinary A/B/A

Source `351ea21`; [contract](../docs/architecture/phase5_tokenizer_metadata_v1_contract.md).
Đã thêm admission metadata, collector và joined auditor mới. Không sửa các
auditor/runner/policy/attention/loader đã khóa. Hai pinned model dùng cùng
7.305 bytes tokenizer config, đã đối chiếu size/SHA256/Git blob với inventory
agent và snapshot guard. Suy pad=151643/EOS=151645 từ decoder metadata; CLI mới
không cho nhập pad ID tùy ý. Không thực thi publisher chat template.

26 test mới; nhóm tokenizer/ordinary audit/ordinary runner đạt 130 pass trong
30,29 giây. Setup/Ruff/mypy 301 files/knowledge đạt. Full QA hoàn tất: 2.288 pass,
1 optional skip (native tqdm), 424,88 giây, không lỗi; không test job còn chạy.
JUnit `results/phase5_tokenizer_metadata_v1_cpu01_pytest.xml` đã hash-bound trong
[release QA](../experiments/manifests/phase5_tokenizer_metadata_cpu_v1_release_qa01.json).
7 source entries/235 prior raw và audit files/106 frozen overlay entries cùng
prerequisite seals được kiểm lại, không đổi. 254 source/docs/receipt/evidence files đã
quét với 4 credential values đã biết: 0 matches; không chọn credential vào Git.

Collector đã lấy hai sidecars trong
`results/phase5_tokenizer_metadata_v1_cpu01/tokenizers`. Cả hai nguồn lấy từ
cache cấu hình guard vì bytes giống hệt agent pin; đây KHÔNG phải xác nhận
agent mount local hoặc model đã load. Collector chỉ đọc config, không weights.
Hai audit mới `audit01.json`/`audit02.json` byte-identical, đọc 84 inputs từ
hai tokenizer sidecars và fixture giả lập cũ
`results/phase5_ordinary_native_join_cpu_v1_synthetic01`, không sửa raw cũ.
Mọi model responses/tensors/timing/memory của fixture vẫn synthetic.

Layer mới xác thực metadata và nối expected IDs với policy records. Các cờ
native execution/source authentication/Phase 5 acceptance vẫn false. Không
biến việc kiểm config thành bằng chứng thực thi tokenizer hoặc GPU.

Rà soát static imports của bốn CLI (runner, supervisor audit, tokenizer audit,
collector) chạm 46 source files; 14 file chưa có trong base bundle + 42-file
efficient-stress overlay. Đây chỉ là danh sách chuẩn bị, chưa phải exactpreflight:
bốn CLI trên; `efficient_requests_v1`, `ordinary_pair_probe_v1`,
`request_policy_pair_v1`, `request_policy_v1`; sáu validators
`efficient_requests_audit_v1`, `ordinary_native_audit_v1`,
`ordinary_pair_audit_v1`, `ordinary_tokenizer_audit_v1`,
`request_policy_audit_v1`, `tokenizer_metadata_v1`. Phải kiểm thêm dynamic imports
và output routing trong wrapper mới, không giả định static closure là đủ.

## Việc tiếp theo

1. Full QA và receipt đã hoàn tất; không còn test job đang chạy.
2. Tạo wrapper/preflight ordinary mới dựa trên frozen efficient-stress bundle:
   thêm request-policy pair, ordinary runner/auditors và tokenizer collector;
   lấy config sidecars từ model mounts thật trước inference. Không dùng source
   fixture JSON envelope làm file tokenizer của model.
3. Kiểm archive/expanded layouts, imports cô lập, tám tools/Dummy/resume, source/
   model/wheel identities; push source rồi kiểm quota/private Dataset version.
4. Chạy native A/B/A trên Kaggle và release-level source/remote audit. A0/A1
   agent-only owner, runtime A0–A6/differential/lifecycle, A4/general final và
   grouped Dev gates còn mở. Không suy phần trăm từ số test.

Pending access: chưa cần tài khoản/quyền mới cho CPU; quota và Dataset readiness
cần kiểm hiện hành trước GPU. Không native/GPU/submission hoặc Test payload mới.
