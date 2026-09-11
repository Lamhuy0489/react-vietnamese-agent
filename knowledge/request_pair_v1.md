# Ghép ordinary request vào sibling workers — CPU

Source `35978d2`; [contract](../docs/architecture/phase5_request_pair_v1_contract.md).
`llm/request_pair_v1.py` tạo pair lazy, giữ ReadyFactory ngoài cùng rồi progress,
attention adapter, native factory. Không sửa ModelPair/runtime/loader/adapter cũ.
Progress trước load, readiness không tiêu thụ request index, lỗi không retry.

Hai standalone real-spawn rehearsals từ source này đã đạt, mỗi lượt 4 cases/
7 child PIDs/46 raw files; tổng14 PID khác nhau, stable control summaries khớp.
[Validation receipt](../experiments/manifests/phase5_request_pair_cpu_v1_validation01.json)
ghi toàn bộ92 raw hashes. Mỗi lượt có4GRACEFUL/0 và3TERMINATE/-15, đủ7reaped;
đây là CPU synthetic, không suy ra shutdown/VRAM/IPC của native GPU models.
Native tqdm4.67.3 dùng thật; model constructors bị bypass, generate/tensors/
metrics giả lập tường minh. A/B/A input1/4096/1, output1/3/1 cho mỗi role;
original attention writer và independent auditor đối chiếu request/PID/token.
Reversed wrapper startup bị từ chối; injected agent/guard errors giữ entered/
error/restored, không completed, sibling cleanup và retry-refusal đạt.

17 test mới +124 test trước =141 focused pass26,56s; setup/Ruff/mypy287 đạt.
Full QA: 2.072 pass, 1 optional native tqdm skip, 386,91s, không lỗi;
`results/phase5_request_pair_v1_cpu01_pytest.xml` đã hoàn tất.
[Release QA](../experiments/manifests/phase5_request_pair_cpu_v1_release_qa01.json).
Không model/Torch/Transformers/GPU/Test payload/privateGT mới. Seals hash-only
và106 frozen overlay entries,277 historical raw files giữ nguyên. Source đã commit;
fullQA đã đạt để push. Không test job còn chạy hoặc job Kaggle mới.

## Bài học và bước tiếp

- Venv test ban đầu thất bại vì chỉ giải nén package tqdm mà thiếu dist-info:
  version UNKNOWN làm worker từ chối đúng. Giữ metadata của wheel đã hash-pin,
  không nới version check. Rerun focused với đầy đủ metadata đã đạt.
- Dev rehearsal `results/phase5_request_pair_cpu_v1_dev01` là prototype, không
  dùng làm selected receipt; không ghi đè hoặc xóa lịch sử lỗi/test artifacts.
- Builder hiện khởi động cả hai roles: không dùng cho A0/A1. Còn cần task owner
  agent-only và runtime routing trực tiếp, không nested WarmGuard/ModelPair.
- Tiếp native repeated-request runner và request-local publisher-policy evidence;
  observer stress cũ single-use, không cắm trực tiếp cho request thường. Cần
  native memory/placement admission, supervisor-bound independent audit, source
  authentication và exact package preflight trước Kaggle. Token/geometry join
  chưa chứng minh full-boundary KV hoặc numerical statelessness.
- Không cần quyền/tài khoản mới cho CPU milestone; kiểm quota/private Dataset
  và phạm vi riêng trước GPU. Không thay model, precision, decoding/caps/deadlines.

Phase5 chưa accepted. Không dùng số tests làm phần trăm hoàn thiện.
