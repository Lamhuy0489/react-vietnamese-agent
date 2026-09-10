# Native policy library compatibility — CPU worker

Đang triển khai2026-09-10, chưa submit/accept native execution.
Local system Torch2.2.2 không dùng thay pinned Kaggle Torch2.10.0+cu128 và
Transformers5.5.0. KernelCPU riêng, private/offline, no model_sources/GPU/TPU.
Không materialize `guard-model.tar` hoặc tải/load weights. Dataset cũ giữ nguyên.

Harness chỉ gọi actual GenerationMixin config/special-token/length methods qua
PolicyStressBackend và so control không hook. Không gọi model.generate hoặc
Qwen forward. Hai success roles và hai injected error/interruption controls.
Mỗi policy receipt vẫn dùng protocol của **synthetic harness**, nên trường
model_generation_calls=1 trong receipt đó không phải native model inference;
summary bắt buộc ghi model_generate_calls=0 và synthetic-count qualifier.
Không lấy bài kiểm tra này thay native context-stress GPU evidence.

Source files mới: native/stub harness entry, standalone CPU wrapper25-file
additive overlay, exact builder. Local exact package dùng stub, giữ native
progress6workers/layout và8tools/21Dummy/missing-onlyresume trên archive/expanded/
PAX layouts. KernelCPU sau đó mới chạy native thư viện thật và kiểm hashes hai
native implementation source files trước khi gọi. Không local native imports.

Tiếp: commit source → exact preflight/fullQA → push source/receipt → kiểm private
Dataset/current account → submit **một** CPU kernel identity
`huylmhuhu/react-vn-policy-native-compat-v1`, timeout1800s. Không retry nếu chưa
giữ status/logs/partials và phân loại lỗi. Tải về fresh path, xác thực remote
wrapper/metadata/bundle, audit harness + Dummy; giữ giới hạn model calls0.
Sau đó mới outer publisher-metadata audit + native GPU stress wrapper.
