# Sổ tra cứu Kaggle của đồ án

Cập nhật 2026-09-13 từ receipts/report đã lưu trong Git. Đây là **memory phát
triển cho nhóm**, không đưa vào prompt benchmark. Trạng thái dưới đây là mốc
bằng chứng lịch sử, không phải kiểm tra trực tuyến lại mọi URL hôm nay.

Kiểm offline: 26 URL code/Dataset/model trong sổ đều có handle tương ứng trong
`experiments/manifests/`. Chưa khẳng định mọi URL vẫn mở được với tài khoản khác.

## Bạn mới tham gia bắt đầu ở đâu?

1. Đọc [trạng thái hiện tại](current_status.md) và [bàn giao](handoff.md).
2. Source chính thức: [GitHub main](https://github.com/Lamhuy0489/react-vietnamese-agent).
3. Kaggle là máy chạy inference. Tài khoản sở hữu các tài nguyên bên dưới là
   `huylmhuhu`; khác với tên GitHub `Lamhuy0489`.
4. Notebook/Dataset được giữ private. Quyền GitHub không tự cấp quyền Kaggle:
   nếu bạn Minh dùng tài khoản Kaggle riêng thì chủ tài nguyên cần cấp quyền
   cộng tác phù hợp. Không chép API key/token/mật khẩu vào Git hoặc trang này,
   không chuyển public chỉ để mở được link. 403/404 có thể là thiếu quyền.

## Mốc hiện hành — đọc mục này trước

| Tài nguyên | Link | Phiên bản/bằng chứng |
|---|---|---|
| Notebook runtime A0–A6 | [react-vn-security-runtime-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-security-runtime-v1) | v1 COMPLETE; [GPU report](../docs/evaluation/phase5_security_runtime_gpu_v1_report.md), [receipt](../experiments/manifests/phase5_security_runtime_gpu_v1_audit01.json) |
| Dataset dùng chung Phase 5 | [react-vn-guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1) | v1 private/ready đã kiểm trước run; source bundle, guard snapshot và offline wheels; [preflight](../experiments/manifests/phase5_security_runtime_v1_preflight03.json) |
| Model mount agent hiện hành | [Qwen2.5 7B Instruct / Transformers / v1](https://www.kaggle.com/models/qwen-lm/qwen2.5/transformers/7b-instruct/1) | Model mount, **không phải Dataset của nhóm**; identity/file hashes nằm trong receipt |

V1 hoàn tất không có nghĩa Phase 5 đã nghiệm thu: 7 terminal/recovery, nhưng
0 tool calls/0 guard calls, 12 worker TERMINATE/-15. Không chạy lại để chọn câu
trả lời đẹp hơn. Source inference `372d685`; raw local
`results/phase5_security_runtime_gpu_v1_output01`; source tải ngược
`results/phase5_security_runtime_gpu_v1_remote02`. Raw generated không track Git;
người clone mới lấy output từ notebook, đối chiếu hash với receipt trước dùng.

## Notebook lịch sử Phase 5

Không chọn notebook chỉ vì tên mới hoặc status COMPLETE. Đọc cột bằng chứng;
model quality, lỗi hạ tầng, native OOM và thử nghiệm transport là các mục khác nhau.
Những notebook này dùng Dataset Phase 5 chung ở trên; kiểm mount/version trong
receipt của đúng lượt, không tự nâng phiên bản.

| Notebook | Vai trò / tài liệu đối chiếu |
|---|---|
| [guard15-probe-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard15-probe-run-v1) | [Guard GPU đầu tiên](guard_gpu_probe_v1.md); không dùng làm chứng nhận chất lượng guard |
| [guard-cancel-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-cancel-run-v1) | [Cancellation và recovery](guard_cancellation_v1.md) |
| [pair-gpu-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-gpu-v1) | [Agent/guard cùng GPU](pair_gpu_v1.md) |
| [pair-cancel-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-cancel-v1) | [Pair cancellation](pair_cancellation_v1.md) |
| [pair-ipc-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-ipc-v1) | [IPC diagnostic](pair_ipc_v1.md) |
| [pair-progress-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-pair-progress-v1) | [Progress-lock diagnostic](pair_progress_v1.md) |
| [policy-native-compat-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-policy-native-compat-v1) | [Native-library CPU compatibility](policy_native_compat_v1.md), không phải GPU benchmark |
| [context-policy-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-context-policy-v1) | [Lỗi factory topology lịch sử](context_policy_gpu_v1.md) |
| [context-policy-v2](https://www.kaggle.com/code/huylmhuhu/react-vn-context-policy-v2) | [OOM sau readiness](../docs/evaluation/phase5_context_policy_v2_oom_review.md) |
| [sdpa-tensor-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-sdpa-tensor-v1) | [SDPA tensor diagnostic](sdpa_tensor_v1.md) |
| [efficient-stress-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-efficient-stress-v1) | [Efficient stress](efficient_stress_v1.md) |
| [ordinary-pair-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-ordinary-pair-v1) | [Lượt lỗi giữ nguyên](../experiments/manifests/phase5_ordinary_pair_gpu_v1_error01.json) |
| [ordinary-pair-t4x2-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-ordinary-pair-t4x2-v1) | [A/B/A native transport evidence](ordinary_pair_gpu_v1.md) |

## Phase 1/2 và pilot nhiều model

| Thực nghiệm | Notebook | Dataset | Bằng chứng |
|---|---|---|---|
| Phase 1 smoke | [phase-1-real-model-smoke](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-agent-phase-1-real-model-smoke) v4 | [phase1-bundle](https://www.kaggle.com/datasets/huylmhuhu/react-vietnamese-agent-phase1-bundle) v5 | [Receipt](../experiments/manifests/phase1_kaggle_v4.json) |
| Phase 2 v1 cũ | [phase-2-clean-dev-pilot](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-agent-phase-2-clean-dev-pilot) | [phase2-dev-bundle](https://www.kaggle.com/datasets/huylmhuhu/react-vietnamese-agent-phase2-dev-bundle) | [Receipt lịch sử](../experiments/manifests/phase2_kaggle_v2.json); không thay clean_v1.1 |
| Phase 2 clean_v1.1 | [vietnamese-clean-v1-1-dev-pilot](https://www.kaggle.com/code/huylmhuhu/react-vietnamese-clean-v1-1-dev-pilot) v1 | [clean-v11-dev](https://www.kaggle.com/datasets/huylmhuhu/react-vn-clean-v11-dev) v1 | [Receipt](../experiments/manifests/phase2_clean_v11_kaggle_v1.json); dùng **actual_kernel**, không alias tên yêu cầu |
| Gemma 4 measured Dev | [gemma4-measured-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-gemma4-measured-run-v1) v1 | [gemma4-measured-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-gemma4-measured-data-v1) | [Completion](../experiments/manifests/measured_pilot_completion.json), [submission](../experiments/manifests/measured_pilot_submission.json) |
| Qwen 7B measured Dev | [qwen7b-measured-run-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-qwen7b-measured-run-v1) v1 | [qwen7b-measured-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-qwen7b-measured-data-v1) | [Báo cáo measured Dev](../docs/evaluation/measured_dev_pilot_report.md) |

Llama chưa chạy tại mốc measured pilot vì thiếu quyền Meta; không có notebook
kết quả Llama để dẫn. Các alias/preflight draft không phải lượt được nghiệm thu
không được nâng thành kết quả chỉ vì tìm thấy handle trong source.

## Cách duy trì sổ

Sau mỗi submission thêm URL notebook, version, Dataset/version, source commit,
report/receipt và trạng thái có ngày kiểm. Sau terminal bổ sung raw path và giới
hạn; giữ riêng lỗi và lượt thay thế. Không ghi credentials/private GT/Test payload.
Chạy `make knowledge-check` sau sửa liên kết. URL ngoài repo được lưu từ receipts;
knowledge-check chỉ kiểm link local/cấu trúc, không xác nhận quyền mở trên Kaggle.

[Kaggle lessons](kaggle_lessons.md) · [Runbook](runbook.md) · [Handoff](handoff.md).
