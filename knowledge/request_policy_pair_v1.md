# Ghép policy + attention vào sibling workers — CPU

Source `53f7e19`; [contract](../docs/architecture/phase5_request_policy_pair_v1_contract.md).
Builder `llm/request_policy_pair_v1.py` tạo pair lazy với thứ tự Ready→progress→
policy→attention→native. Kiểm cả hai roles/identities và roots fresh/disjoint trước
transport; không sửa request_pair_v1/observer/attention/native/supervisor đã khóa.
Builder vẫn load cả hai roles, chưa dùng cho A0/A1 hay runtime benchmark.

Hai standalone rehearsals đã đạt 4 control cases/run, 7 child PIDs/run; 14 PID khác nhau,
174 raw files được hash-bound trong
[validation](../experiments/manifests/phase5_request_policy_pair_cpu_v1_validation01.json).
Stable control summaries khớp; mỗi lượt 4 GRACEFUL/0 và 3 TERMINATE/-15, đủ 7 reaped.
Native tqdm thật, model/config/tensor/metrics giả lập tường minh; không suy CPU
cleanup thành native GPU graceful/VRAM/IPC proof hoặc model performance.

Success A/B/A input 1/4096/1, output 1/3/1 mỗi role: joined policy/attention/native
metric audit đạt. Reversed order vẫn từ chối startup; lỗi agent/guard giữ partials,
khôi phục policy methods/attention bindings, dọn sibling và không retry attempt.
Idle sibling READY không tạo policy request. Harness chỉ thay builder trong
module CPU ở host trong try/finally, khôi phục cả khi lỗi/interrupt; không sửa file
frozen hoặc monkeypatch production classes/native libraries ở host.

23 test mới, 227 focused pass trong 27,04 giây; setup/Ruff/mypy 291/knowledge đạt.
Full QA: 2.158 pass, 1 optional skip trong 392,21 giây; không lỗi, không job còn chạy.
`results/phase5_request_policy_pair_v1_cpu01_pytest.xml` được hash-bound trong
[release QA](../experiments/manifests/phase5_request_policy_pair_cpu_v1_release_qa01.json).
Test optional cũ thiếu native tqdm ở môi trường mặc định; test mới và standalone
đã dùng wheel tqdm 4.67.3 được xác thực. Không phát hiện 4 giá trị credential đã
biết trong 185 tệp source/docs/receipt/raw được quét; không công bố giá trị khóa.
Seals/106 frozen entries/277 historical GPU raw/92 prior CPU raw và source/evidence các
request/observer cũ không đổi. Dev01 prototype giữ riêng, không selected release.

## Bước tiếp

1. Native repeated-request runner dùng builder mới và original HF factories.
   Không dùng synthetic factory ngoài CPU harness; không ép output/min length.
2. Authenticate publisher/tokenizer/model/source; kiểm native load/memory/
   placement, supervisor-bound independent audit, then exact package preflight
   trước Kaggle. Synthetic joined auditor không chứng minh native admission.
3. Agent-only task owner cho A0/A1 và direct runtime routing A2–A6, differential/
   lifecycle/grouped Dev gates còn mở. Phase5 chưa accepted.

Pending access: chưa cần tài khoản/quyền mới cho CPU; kiểm quota/private Dataset
trước GPU mới. Không model/Torch/native tensor/GPU/Test payload/privateGT mới.
Không nới caps, đổi model/precision/decoding hoặc cycling account.
