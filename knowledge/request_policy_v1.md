# Cấu hình sinh theo từng ordinary request — CPU

Source `99dbd92`; [contract](../docs/architecture/phase5_request_policy_v1_contract.md).
Thêm observer `llm/request_policy_v1.py` và independent joined auditor
`validation/request_policy_audit_v1.py`. Giữ nguyên nguồn stress/loader/attention/
request-pair đã khóa; không đổi model, decoding, precision hoặc caps.

Observer bọc exact fresh EfficientRequestBackend. Mỗi request có index riêng,
quan sát đúng một lần resolve rồi length, input1–4096; giữ baseline publisher
và kiểm drift giữa/trong request. Khôi phục method bindings khi thành công/lỗi/
interrupt/lỗi ghi evidence; retire sau mọi admitted failure, không retry.
Không ép min_new_tokens/output length và không thêm forward hoặc copy tensors.
Ordinary submitted min_new_tokens/output_logits là None; khác stress fixed-length.

Auditor đối chiếu request policy với attention/native metrics, tái dựng precedence
submitted→publisher→global defaults và tính max/min length từ input đã đo.
Publisher snapshot và tokenizer pad ID hiện do caller cung cấp, chưa authenticated;
source/native loader/memory/supervisor và full KV/cache/statelessness chưa chứng minh.
Không diễn giải consistency thành benchmark adoption hoặc quality/ASR.

63 test mới,204 focused pass24,36s gồm repeated A/B/A, hooked/unhooked fake
differential, lỗi storage/owner/identity/config/shape và corruptions/read-only.
Hai hàm resolve/length trích từ wheel5.5.0 đã kiểm hash chạy với fake config/tensor,
4 conditions (agent/guard × inherited minimumNone/2),3variable inputs mỗi case.
Đây là authenticated method-source execution, không native thư viện/model/GPU run;
fake update/config vẫn có trong harness, không suy thành native numerical proof.
Setup/Ruff/mypy289/knowledge đạt. FullQA hoàn tất: 2.135 pass, 1 optional native
tqdm skip,429,45s, không lỗi; `results/phase5_request_policy_v1_cpu01_pytest.xml`.
[CPU QA receipt](../experiments/manifests/phase5_request_policy_v1_cpu_qa01.json)
binds source và JUnit hashes. Không test job còn chạy tại bàn giao.
Đã kiểm lại277historical GPU raw/92pair CPU raw và các source/evidence request cũ;
10file credential-value scan/4known values/0matches trước receipt.

## Bước tiếp và quyền cần thiết

1. Ghép policy vào versioned pair: Ready ngoài progress ngoài policy ngoài
   attention ngoài native factory. Builder request_pair_v1 cũ chưa có policy;
   không đưa PolicyBackend vào exact-native factory hoặc sửa source đã đo.
2. Rehearsal composition rồi native repeated-request runner, authenticated
   publisher/tokenizer metadata, native load/memory/placement, supervisor-bound
   independent audit và exact package preflight trước lượt Kaggle mới.
3. Agent-only task owner cho A0/A1, direct runtime routing cho A2–A6 và các gate
   differential/lifecycle/grouped Dev còn lại. Phase5 chưa accepted.

Không model/Torch/native tensors/GPU mới, không Test payload/privateGT.
Seals hash-only và106 frozen overlay entries không đổi. Chưa cần quyền/tài khoản
mới cho CPU; quota/private Dataset phải kiểm lại trước GPU. Không tự cycling account.
