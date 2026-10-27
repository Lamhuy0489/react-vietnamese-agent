# Phase 5: restart v2 và Plan API diagnostic

Ngày2026-09-28. Hai notebook v1 đã COMPLETE; owner yêu cầu bật lại. Đã submit
mỗi notebook đúng một lần thành v2, giữ worker source
`728821ea761b3994eb40ebba91ab8238e4667f82` và model mounts/version hiện hành.
Bốn exact-worker preflight layouts đạt; source tải lại của cả hai v2 khớp byte.
Hai `/models` đã xác thực READY với session mới. Notebook vẫn được giữ chạy;
READY là quan sát tại thời điểm kiểm tra, không cam kết uptime.

- [Qwen3-8B agent v2](https://www.kaggle.com/code/buiquocviet/react-vn-qwen3-agent-api-v1)
- [Llama3.2-3B guard v2](https://www.kaggle.com/code/huylmhuhu/react-vn-llama3-guard-api-v1)
- Hai notebook private, yêu cầu T4×2, không Dataset. Package:
  `build/kaggle/structured_pair_release02a`; version lấy từ submission receipts.
- Lần prepare release02 bằng `.venv` dừng trước đóng gói vì thiếu cryptography;
  giữ thư mục đó, dùng runtime phụ thuộc có sẵn và package02a. Không GPU retry.

## Thay đổi host

Thêm [`StructuredPlanHTTPBackend`](../../src/react_agent/llm/structured_plan_http_v1.py)
và [diagnostic runner](../../scripts/run_structured_plan_diagnostic_v1.py).
Adapter chuyển schema Plan hữu hạn thành inline schema, yêu cầu agent/probe,
kiểm identity/schema hash/seed và xác thực Plan trả về. Guard schema và client
action/final frozen giữ nguyên. Worker đã có inline-schema capability nên không
cần sửa mã notebook cho adapter mới.

Diagnostic theo [protocol khai báo trước inference](structured_plan_api_v1_protocol.md):
one synthetic task, ba `doc_read` qua Broker, tối đa một agent + một guard,
nguồn host working-tree được hash trước run. `started` được ghi trước generation;
không tự retry hoặc resume request không rõ trạng thái.

## Kết quả native

Raw: `build/evaluation/structured_plan_api_v1/diagnostic01`.

- Một agent attempt thành công, Plan hợp lệ với ba references; usage997input/
  502output tokens. Một guard attempt thành công,522input/20output tokens.
- Guard: SAFE/LOW, labels=[instruction_override]. Giữ nguyên output bất nhất
  này làm evidence; không diễn giải nó là chứng nhận chất lượng guard.
- Ba reads tạo9Broker events. Plan chọn cả tài liệu confidential; host joinS2,
  quyết định `allowed=false`, reason=sensitivity, output=null.
- Đây là thành công kiểm đường nối/schema và chặn phát hành theo sensitivity.
  Không chứng minh public-field utility: yêu cầu chỉ lấy nội dung công khai
  chưa đạt. Không có semantic retry, hidden reasoning hoặc truy cập Test/oracle.
- Host Grant/catalog vẫn là fixture; guard chỉ xem typed proposal. Đây chưa là
  fullPre/Post/Final hoặc cumulativeA0–A6 runtime integration.

## Kiểm chứng và việc còn thiếu

76focused tests đạt trong runtime API có optional jsonschema, gồm transport,
Plan rejection, Broker/host veto, bridge, API server và Dev checkpoint runner.
Setup, Ruff và mypy571files đạt. Full suite lượt trước có hai lỗi frozen hash
pins; không thay receipts lịch sử để làm xanh và không chạy lại fullsuite dài
chỉ cho adapter biệt lập này. Knowledge-check/diff-check được ghi ở handoff.

Phase5 vẫn4/7 nhóm; không đóng thêm gate chỉ từ diagnostic. Tiếp theo cần một
transport/lifecycle contract cho remote guard trước khi nối public runtime:
kill HTTP client local không chứng minh GPU request đã bị hủy. Sau đó khai báo
Dev differential fullPre/Post/Final/A0–A6, đo benign utility/guard quality và
unknown-lineage/final leakage; chỉ freeze khi gate thực sự đạt.

Receipt chọn lọc: [restart + diagnostic](../../experiments/manifests/structured_plan_api_v1.json).
Raw/credentials chỉ local; receipt không chứa keys/endpoints/private discovery key.
