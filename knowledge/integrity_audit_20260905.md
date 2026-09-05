# Kiểm tra lại Phase 1 và Phase 2

Ngày: 2026-09-05. Baseline Git: `ddea689de7eccb4c6b2a59d8d4a29248a35dc68f`.

## Phạm vi

Đối chiếu DoD, đọc code, chạy validator/test CPU, audit artifact đã lưu.
Không đổi prompt/model/threshold, không gọi Kaggle inference. Audit nhóm dùng
pool gốc và assignment manifest; validator split đọc dữ liệu/GT đã khóa chỉ
để kiểm tra cấu trúc, identity và hash. Không có Test model output để tuning.
Thư mục này không chứa prompt, đáp án hoặc payload held-out Test.

## Phase 1 — xác nhận lại 8 DoD trong phạm vi smoke

| Gate | Bằng chứng |
|---|---|
| Terminal execution | Replay, Dummy, Kaggle cũ: 20/20 terminal, 0 crash |
| Tool coverage | Replay 8/8; model thật 6/8, không gọi hai mock sink |
| Trace integrity | Replay 218, Dummy 80, Kaggle 262 sự kiện; schema/task/call/summary khớp |
| Determinism | Hai lượt mỗi backend giống nhau khi bỏ timestamp/run ID |
| Mock side effects | Cấm tạo socket vẫn gọi được hai sink; code không HTTP/SMTP |
| A0 purity | Security flags false; prompt JSON/tool, context không đưa GT vào |
| Local reproducibility | Setup, smoke-data, Phase 1 validator và CPU integration tests pass |
| Kaggle evidence | 8/8 artifact SHA-256 khớp manifest v4, đủ 20 task duy nhất |

Raw CPU audit: `results/audits/20260905/{replay-a,replay-b,dummy-a,dummy-b}`
(ignored). Kaggle gốc: `results/phase1/kaggle_v4`, không ghi đè. Replay 20/20
success; Dummy 0/20 semantic success là hành vi stub, không phải crash. Model
thật 3/20 giữ nguyên, không phải metric luận văn.

Validator cũ chỉ đếm run và thứ tự event. Đã thêm schema, đúng tập 20 task,
mỗi task một run, terminal/final answer, call ID/tool payload và summary tính
lại từ trace. Regression fixtures riêng bắt run trùng task, khai sai coverage
và terminal không hợp lệ; không thay runtime Phase 1.

Giới hạn đọc code/probe nhỏ: timeout broker không kill thread đang chạy;
calculator chưa loại hết số không hữu hạn/số phức. Smoke DoD không có nghĩa
mọi input tùy ý đều đã được kiểm thử. Chưa sửa runtime trong lượt audit này.

## Phase 2 — rút lại acceptance

1. Signature cũ tính `fact_id` cục bộ; đổi tiền tố làm cùng fact/nguồn bị coi
   khác instance. Signature mới bỏ nhãn, chuẩn hóa thứ tự và kiểm tra mọi
   category: 30 cặp cùng instance, 12 cặp xuyên split. Generator recovery tái
   sử dụng fact/nguồn sẵn có; category khác không tạo đáp án độc lập.
2. Pool validator cũ yêu cầu 250 group ID riêng. Đã bỏ điều kiện sai này và
   yêu cầu cùng instance thuộc cùng nhóm. Splitter chia category độc lập:
   đã chặn nhóm xuyên category bị tách trước khi ghi; thuật toán phân bổ
   nhiều category còn phải hoàn thiện cho version thay thế.
3. Generator gán sẵn 10 cờ review `True`; không chứng minh đủ 10 kiểm tra QA.
   Oracle hiện chỉ sanity-check đường tool mẫu, chưa chứng minh category,
   distractor, alternative path hoặc argument semantics.
4. Dev evaluator dùng substring; `arguments_usable` chỉ so số event với số
   tool, chưa thực thi `ArgumentValidator`. Điểm 7/21 là provisional, không
   phải strict TSR đã xác minh. Không rescore đè artifact cũ.
5. Ba generator entrypoint giờ từ chối ghi khi có seal/split marker, kể cả
   manifest hỏng hoặc `frozen=false`. Không có cờ force ghi đè version khóa.
6. Hash validator bắt buộc đủ component và aggregate hash; không theo đường
   dẫn lạ trong manifest. Bundle chặn split lỗi và không xóa output cũ.

Pool/split validators hiện phải trả mã 1 trên v1. Software tests pass vì bắt
đúng dữ liệu lỗi, không phải bỏ acceptance gate. Báo cáo QA dẫn xuất được
cập nhật; task/GT/môi trường/schema/manifest và raw model artifact giữ nguyên.

## Cần quyết định

Kiểm thử sau thay đổi: 77 tests pass; `verify_setup.py`, Ruff và mypy pass.
Pool/split acceptance vẫn FAIL theo các lỗi đã nêu, không bị bỏ qua.

Không gắn tag Phase 2, không tự đổi assignment/hash v1. Cần chấp thuận version
benchmark thay thế và ghi deviation trước khi author lại. Giữ quota/scope,
dựng nhóm trước split, sửa QA/comparator trước pilot mới; không dùng điểm
model cũ để chọn dữ liệu dễ hơn. Review waiver còn hiệu lực; Phase 3 chưa làm.
