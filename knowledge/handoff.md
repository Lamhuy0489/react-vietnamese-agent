# Bàn giao phiên làm việc

Cập nhật: 2026-09-06. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Theo yêu cầu owner tiếp tục Phase 3: đã tạo pilot revision `candidates_v2_2`
cho 12 cặp hiện có. Sửa attack/benign wording và quyết định gộp nhóm; không
đổi public task/private oracle bytes, scope hoặc reference scripts. 48 Replay
đạt QA, per-case typed/security scores khớp bản trước. A0 không đổi.

Bản v1 70 family/350+350 variants và workbench bốn cặp vẫn giữ nguyên.
12 ứng viên chưa split/approved, không tính vào quota chính. Có typed utility +
source evidence và audit 66 cặp so sánh; revision gộp thận trọng còn bảy review
units, không chứng nhận độc lập ngữ nghĩa. Benign/attack word ratios 1,03–1,13.
Có assistant author self-review records, không phải independent human approval.
[Ước lượng tiến độ theo DoD](phase3_readiness.md): khoảng 25–30% effort.
Đọc [tiến độ Phase 3](phase3_progress.md) để xem những thiếu sót đã xác minh.

## Bước tiếp theo

1. Đọc [Phase 3](../plan/phase3.md),
   [adversarial contract](../docs/benchmark/adversarial_contract.md) và
   [split rules](../docs/benchmark/split_rules.md).
2. Chạy `make phase3-audit`: hiện cố ý không cấp acceptance; không retry GPU
   hoặc đổi dữ liệu tại chỗ để làm xanh gate.
3. Đọc [tóm tắt v2.2](../docs/benchmark/canonical_revision_summary.md) và
   [contract revision](../docs/benchmark/canonical_revision_contract.md).
   Wording/neutral benign/length/group revision cho 12 cặp đã xong mốc QA;
   không viết lại vòng này. Bước cụ thể: author batch cơ chế mới ngoài bảy
   review units, ưu tiên retrieval/search và multi-step sources. Đóng băng
   interface mở rộng cần thiết trước implementation, mỗi case có safe/negative
   QA và private utility. Không đổi bytes các version cũ. Nếu ca mới cần
   row-level/encoded leakage thì phải có oracle/test tương ứng trước khi tính.
4. Review nhóm semantic/template, xác định split rồi mới sinh variants. Giữ
   bản draft cũ làm bằng chứng; không âm thầm reseal/move family.
5. Chỉ cập nhật acceptance khi có kiểm tra thực sự. Đọc [runbook](runbook.md)
   và chạy các kiểm tra trước commit/push.

## Bằng chứng

- Nguồn trạng thái: [phase status](../docs/project/phase_status.md).
- Phase 1 accepted; Phase 2 clean_v1.1 accepted dưới owner automated-QA waiver:
  [v1.1 progress](clean_v11_progress.md).
- Gemma 4/Qwen 7B pilot đã hoàn tất, source inference `58fdeb5`, source report
  `3b7527a`, release `2301a12`:
  [completion receipt](../experiments/manifests/measured_pilot_completion.json),
  [báo cáo](../docs/evaluation/measured_dev_pilot_report.md).
- Strict success 6/21 và 3/21; đây là Dev diagnostic, không final model ranking.
  Không cần chạy lại pilot chỉ vì điểm thấp.
- Quyết định và waiver: [decision log](../docs/project/decision_log.md).
- [Audit Phase 3](../experiments/manifests/phase3_draft_audit_20260906.json)
  xác minh số lượng/hash nhưng ghi rõ lỗi template/surface/stratification và
  gate chưa thực thi. Không có inference mới trong lượt củng cố knowledge.
- Kiểm tra lượt trước: 130 tests pass; setup/Ruff/mypy (98 source files) và
  `make knowledge-check` pass. clean_v1.1 sealed-read-only validation pass;
  hash draft v1, auditor và measured releases khớp, không thay input đã khóa.
- [Workbench receipt](../experiments/manifests/phase3_workbench_v2_validation_01.json):
  source implementation `b7ae80c`, bốn cặp, 16 Replay, tám safe/tám negative đạt
  điều kiện fixture. Test có
  chặn network và lặp lại observable traces. Kiểm tra mốc workbench: 143 tests,
  setup/Ruff/mypy 103 source files pass; không thay dữ liệu/release đã khóa.
- [Receipt mở rộng](../experiments/manifests/phase3_candidates_v2_1_validation01.json):
  source implementation `3e68814`;
  12 ứng viên, 48 Replay (24 safe/24 negative), bốn category và bốn source
  type đều ba cặp; không có action chưa đánh giá được trong reference scripts.
  168 tests pass; setup/Ruff/mypy 107 source files và clean_v1.1 seal pass.
  Hash input/source mới, v1/workbench cũ và 12 measured artifacts đều khớp.
  Receipt lưu base commit và exact source hashes, không giả source đã commit
  tại thời điểm chạy. Raw traces nằm ngoài Git.
  Quét bốn credential values trong 18 file thay đổi: không có match.
- [Review QA receipt](../experiments/manifests/phase3_candidate_review_v1_validation02.json):
  source implementation `114615d`;
  48 fresh Replay, 24 safe/24 negative, đủ 66 pair comparisons, chín review units.
  220 tests pass, gồm 52 tests mới về typed answers/evidence/sinks/trace/grouping.
  Setup/Ruff/mypy 110 source files pass. Raw preformat receipt giữ riêng dưới
  ignored results; validation02 là bằng chứng được chọn, không ghi đè lượt cũ.
  clean_v1.1 sealed validation và hash các source/input/receipt cũ, 12 measured
  artifacts đều khớp. Quét bốn credential values trong 17 file thay đổi: 0 match.
- [v2.2 revision receipt](../experiments/manifests/phase3_canonical_revision_v22_validation01.json):
  source implementation `53452a5`;
  12 revised pairs, 48 Replay, bảy review units. 244 tests pass (24 mới),
  setup/Ruff/mypy 112 source files và clean_v1.1 seal pass. Có validator cho
  allowed-field changes, markers/destinations, length/cue gates và merge-only
  grouping. Không ghi đè preflight/raw runs hoặc đổi điểm pilot cũ.
  Hash revision/parent/sidecar/source và mọi receipt cũ đã đối chiếu khớp,
  gồm 12 measured artifacts; quét bốn credential values trong 19 file: 0 match.

## Giới hạn

- Phase 3 đang authoring; Phase 4–5 chưa được triển khai trong lượt này.
- Không có held-out model run; QA split tĩnh không được dùng để tuning.
- Llama chưa chạy vì Meta access pending; không cần hỏi lại quyền Google.
- Không cần tài khoản mới cho QA offline; không có LLM/Kaggle run mới.
- Owner đã bỏ yêu cầu Minh peer-review trong workflow dùng chung máy; không
  giả reviewer hoặc coi automated QA là bằng chứng human semantic review.
- Không đổi bytes clean_v1/v1.1 hoặc measured releases. Không đưa credentials,
  private GT, held-out payloads hay hidden reasoning vào memory.
- GitHub là source of truth; remote push chỉ sau kiểm tra. Không ghi “đã push”
  nếu chưa có xác nhận thành công.
