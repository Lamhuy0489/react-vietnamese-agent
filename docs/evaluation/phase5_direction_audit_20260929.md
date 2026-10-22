# Phase 5 direction audit — 2026-09-29

> Correction 2026-09-29: the root-fix review supersedes the v12-only candidate
> recommendation and any inference that the current C1–C12 alone close all DoD.
> Candidate v14 integration remains unaccepted with original metadata preserved.
> Actual C11/C12 are untrusted-action/benign-webhook controls, not guard faults
> or a classifier dataset. See the [root-fix report](../evaluation/phase5_root_fix_20260929.md)
> and decision log. Historical native v1 runs must not be resumed with revised fixtures.

## Kết luận điều hành

Đề tài không đi sai hướng ở cấp nghiên cứu. RQ1/RQ2/RQ3, phạm vi một
ReAct agent, tám mock tools, dữ liệu synthetic, A0–A6 tích lũy, tách Dev/Test
và cấm dùng hidden chain-of-thought vẫn khớp với contract đã đóng băng và kế
hoạch Word. Phase 1–4 đã có trạng thái accepted trong hồ sơ; Phase 5 **chưa
accepted**.

Điểm cần sửa là quản trị triển khai: nhiều runtime và prototype được tạo ra
liên tiếp (v10–v14, doc-read, field-reference, encoded-final, room-ticket,
API plan/lifecycle), làm bằng chứng cơ học, CPU prospective, API diagnostic và
bằng chứng nghiệm thu bị đặt cạnh nhau. Điều này tạo cảm giác lan man và có
nguy cơ làm sai câu hỏi “cùng runtime, chỉ đổi SecurityConfig”. Không cần đập
bỏ repository hoặc dữ liệu lịch sử. Cần khóa một đường đóng Phase 5 và dừng
patch mới ngoài đường đó.

## Căn cứ được đối chiếu

- [Research contract](../project/research_contract.md) và [invariants](../project/invariants.md)
  là nguồn kỹ thuật hiện hành: ba RQ, một agent, tám tool synthetic, không
  side effect thật, không CoT, một backbone cố định cho A0–A6 và ba backbone
  cho RQ1.
- [Phase map](../project/phase_map.md), [Phase 5 plan](../../plan/phase5.md)
  và master Word plan xác định A0 baseline; A1 rules; A2 guard; A3
  sensitivity; A4 untrusted/taint; A5 joint session sensitivity+trust; A6
  per-value provenance với PRE/POST/FINAL.
- [20-DoD readiness](phase5_gate_readiness_v1_report.md) ghi rõ 20/20 mục
  vẫn `open`; các file CPU-indexed là admissibility evidence, không tự động là
  acceptance. Các blocker chính vẫn là guard quality, native A0–A6 parity,
  provenance/final-release coverage, lifecycle và formal freeze.
- [Current status](../../knowledge/current_status.md) và [handoff](../../knowledge/handoff.md)
  là trạng thái vận hành hiện hành. Các file trong `knowledge/history/` và
  report cũ giữ lại để audit nhưng không phải hàng đợi công việc mới.
- `docs/BAO_CAO_TIEN_DO_DO_AN.md` và PDF cùng tên là draft tiến độ. PDF được
  render trước đợt chỉnh claim này, nên không dùng nó làm báo cáo cuối cho tới
  khi Markdown được re-audit và PDF được render/kiểm tra lại.

## Những gì đang đúng

1. **Hướng nghiên cứu và phạm vi** vẫn đúng contract. Không có bằng chứng cần
   đổi RQ, đổi dữ liệu sang thật, hoặc thêm multi-agent.
2. **Tính toàn vẹn thực nghiệm** được giữ: Test/private ground truth chưa mở
   trong các diagnostic gần đây; mock email/webhook không mở mạng; không lưu
   chain-of-thought; các thất bại cũ được giữ nguyên.
3. **Phân biệt evidence đã tốt hơn trước**: các report readiness, API
   diagnostic, CPU candidate và handoff đều nói rõ giới hạn, không nâng một
   unit test thành chất lượng model.
4. **Hạ tầng host có tiến bộ thực chất**. Candidate request-worker host có
   HTTPS no-redirect, identity/boot binding, journal immutable, recovery
   fail-closed và không semantic retry. Đây là nền tảng lifecycle, chưa phải
   bằng chứng native cancellation hay Phase 5 acceptance.

## Những gì đang lệch hoặc còn thiếu

| Vấn đề | Bằng chứng | Cách xử lý chuẩn |
|---|---|---|
| Chưa có canonical candidate duy nhất | `phase5_direction_review_20260925.md` mô tả v12 cumulative và các A6-only adapter là các nhánh khác nhau; v14 email ghi `a6_native_ready=false` | Chọn v12 cumulative làm baseline/closure anchor. Giữ v13/v14, doc-read, field, encoded và room-ticket là historical/prospective mechanism evidence; không trộn score và không tạo v15/v16 patch |
| Same-runtime/config isolation chưa được chứng minh cho candidate cuối | Word plan và `plan/phase5.md` yêu cầu giữ loop/model/tools/prompt/schema/benchmark/env/decoding, chỉ đổi `SecurityConfig`; một số candidate đổi representation/runtime | Trước native run phải freeze một runtime/schema duy nhất; chạy cùng task/config/model/decoding qua A0–A6; nếu muốn typed provenance thì phải là một ablation được khai báo trước, không thay thế âm thầm |
| API pair hiện tại chưa đủ RQ1/RQ2 | Qwen là task agent và Llama là guard; pilot/paired/provenance vẫn là diagnostic, guard không phải task backbone thứ hai | Không tính guard là backbone. RQ1 ba backbone để Phase 7; Phase 5 chỉ cần một agent backbone cố định cho A0–A6 và guard cố định ở các mức dùng guard |
| CPU/transport evidence bị hiểu nhầm là native | `request_worker_host_v1_cpu_report.md`, `remote_api_*` reports và readiness đều ghi native/lifecycle còn mở | Dùng CPU để đóng schema, journal, source admission và evaluator. Chỉ gọi là native khi có identity pin, cùng Dev matrix, PRE/POST/FINAL, model/worker receipt và lifecycle receipt trong một run |
| API hiện không mở được | Probe đọc-only mới nhất: agent HTTP 530, guard network error; không có inference | Không retry semantic, không đổi prompt/policy, không gửi key trong chat. Chỉ mở run mới sau khi cả hai `/v1/models` trả READY và identity khớp; nếu không, ghi infrastructure blocker |
| A6 hiện còn miền hẹp | exact raw/typed/email controls chứng minh cơ chế; value-origin email v14 tương đương lexical v3 và không thêm authority | Giữ evidence làm bounded mechanism evidence. Không gọi đó là semantic lineage tổng quát, không chuyển score cũ sang representation mới |
| Phase 5 formal freeze chưa có | DoD20 mở; phase status còn các gate A2/A4/A6/grouped Dev/lifecycle | Chỉ cập nhật `phase_status.md` sau closure receipt duy nhất và audit đủ 20 DoD; nếu không đạt thì phát hành no-go/limitation report, không hạ tiêu chí |

## Đường hoàn thiện duy nhất từ đây

### Gate 0 — khóa phạm vi

Không thêm runtime, candidate, benchmark label hoặc API notebook mới. V12
cumulative là **source/representation baseline để so sánh**, chưa phải model/API
acceptance; host lifecycle v1 là component độc lập.
Mọi artifact cũ giữ nguyên và được gắn nhãn historical/prospective. Một thay
đổi mới chỉ được phép nếu đóng một DoD cụ thể, có protocol trước khi chạy và
có evaluator/report riêng.

### Gate 1 — đóng QA CPU và host

Chạy `scripts/verify_setup.py`, Ruff, mypy và pytest cho source hiện hành; hash
runtime, tests, protocol, manifest và report. Host candidate phải kiểm tra
duplicate delivery, uncertain blocking, exact cached recovery, status hash
mismatch, fresh-boot scope và structured output. Không dùng kết quả này để
claim model quality hoặc CUDA cancellation.
Nếu full suite còn hai historical frozen-pin failures như handoff đã ghi, giữ
nguyên receipt lỗi và tách chúng khỏi focused QA; không sửa historical hash chỉ
để làm xanh toàn bộ suite.

### Gate 2 — điều kiện mở API

Chỉ khi **cả agent và guard** có health GET thành công, `status=READY`,
`gpu_quiescence_attested=false` đúng contract và static identity khớp manifest
mới được tạo run native. Health cũ không mở lại một request cũ; session ID
không thay thế boot instance ID.

### Gate 3 — một Dev matrix native cho A0–A6

Freeze agent/guard/model revision/source/config/decoding/tools/tasks một lần.
Chạy matched Dev qua cùng runtime và schema; A0 không dùng guard, A1–A6 dùng
đúng component đã khai báo. Thu action dispatch, PRE, POST, FINAL, guard
decision, utility, leakage, provenance joins, request journal và uncertain
states. Không Test, không private oracle, không semantic retry và không chọn
candidate theo kết quả.

### Gate 4 — lifecycle và evaluator

Chỉ sau Gate 3 mới chạy diagnostic cancellation/lifetime đã predeclare. Tách
request delivery uncertainty, server cancellation, CUDA quiescence và task
isolation thành các cột riêng. Chạy evaluator từ raw immutable receipts, rồi
map trực tiếp vào 20 DoD; không dùng số lượng file hoặc số test làm proxy.

### Gate 5 — formal freeze hoặc no-go

Tạo một closure receipt chứa source commit, model revision, worker hash,
settings, data/config hashes, raw roots, evaluator hashes, lifecycle result và
mapping 20 DoD. Chỉ khi các gate bắt buộc đóng mới cập nhật `phase_status.md`
và chuyển Phase 6. Nếu còn blocker, đóng Phase 5 bằng báo cáo **chưa đạt với
giới hạn và bằng chứng**, giữ `phase5_accepted=false`, thay vì tạo thêm một
candidate để làm đẹp số liệu.

## Quy tắc chống lan man

- Một experiment có một manifest, một raw root, một evaluator và một report.
- Historical artifacts không bị xóa hoặc sửa để khớp candidate mới.
- Không dùng Test để chọn model, prompt, policy, threshold, representation hay
  architecture.
- Không coi guard là task-agent backbone; RQ1 ba backbone để Phase 7.
- Không chạy lại run đã terminal chỉ để tìm kết quả thuận lợi hơn.
- Không ghi credentials, endpoint riêng, private ground truth hoặc CoT vào
  report/chat/Git.

## Trạng thái sau audit

Đồ án **đúng hướng ở cấp nghiên cứu nhưng chưa thể gọi là hoàn thiện Phase 5**.
Việc cần làm ngay là Gate 1 và chuẩn bị manifest cho Gate 2–3; không cần GPU
local. Với health hiện tại, không chạy API mới. Nếu owner khôi phục được hai
notebook private để health trở lại READY, chỉ cần cung cấp quyền truy cập qua
môi trường đã lưu; không gửi API key vào chat. Nếu không khôi phục được, phần
CPU/evaluator/closure report vẫn có thể hoàn tất và phải ghi rõ infrastructure
blocker.
