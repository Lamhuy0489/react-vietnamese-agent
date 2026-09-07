# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Đã chốt `boundary_batch_v1`, source `c5e1030`: thêm tám cặp private projection,
final-policy, quota chung và revocation. **72 ứng viên, 70 đại diện tạm giữ**, giữ hai merge
hexcode → encoded và rowretry → rowdirect; không xóa ca gốc. Không đồng nghĩa
70 family độc lập đã nghiệm thu. 20 nhóm bảo thủ, 2.556 pair comparisons.
288 standard paths hiện hành = 256 tái dùng + 32 mới (16 safe/16 negative).
Thêm hai safe alternatives: tổng **34 fresh Replay**. Sáu counterexample/control
admission cũ vẫn là bằng chứng riêng, không cộng vào standard paths.
A0, dataset/source/scorer cũ và model scores không đổi.

Bản v1 70 family/350+350 variants và workbench bốn cặp vẫn giữ nguyên.
72 ứng viên chưa split/approved, không tính vào quota family đã nghiệm thu.
Replay là reference QA, không phải model
runs. Không giả independent review. [Tiến độ theo DoD](phase3_readiness.md):
ước lượng 55–60% effort, không metric nghiệm thu. Đủ 70 đại diện tạm giữ nhưng
chưa quyết định nhận/gộp family toàn pool; review có thể yêu cầu gộp/thay thế.
Đọc [tiến độ Phase 3](phase3_progress.md) để xem những thiếu sót đã xác minh.

## Bước tiếp theo

1. Đọc [Phase 3](../plan/phase3.md),
   [adversarial contract](../docs/benchmark/adversarial_contract.md) và
   [split rules](../docs/benchmark/split_rules.md).
2. Đọc [tóm tắt boundary](../docs/benchmark/boundary_batch_summary.md) và
   [review batch](../data/adversarial/boundary_batch_v1/README.md). Dùng verifier
   `verify_boundary_batch.py` trong runbook khi cần tái kiểm tra snapshot;
   completion/disclosure/admission/v3 là các mốc trước. Draft v1 vẫn chưa accepted;
   không retry GPU hoặc sửa dữ liệu tại chỗ để làm xanh gate.
3. Không chạy lại từng batch để báo thêm tiến độ. Không sửa bytes 72 candidates,
   review snapshot hoặc source đã có receipt; tạo version mới nếu cần sửa.
   Bước cụ thể: review semantic/pair và quyết định admission toàn bộ 70 đại diện,
   rồi kiểm tra khả năng grouped 40/30 split, báo imbalance trước khi gán split.
   Không author thêm chỉ để tăng số; không đổi tên để đủ 70. 20 review units phải
   chung split, không đòi 70 abstract mechanisms khác nhau. Business group có 25
   đại diện, không tách để ép strata. Categories retained: 20 indirect/15 output/
   20 exfiltration/15 policy; sources: 19 document/15 cache/21 DB/15 output.
   BoundaryOracle thêm private outcome `final_policy`; dùng loader riêng cho
   batch mới. Không gọi generic loader cũ lên batch này. Final-policy và derived
   disclosure là field riêng, không giả raw-artifact leakage hoặc tool violation.
   Coverage chỉ bounded projection/exact lines, chưa general entailment.
4. Review nhóm semantic/template, xác định split rồi mới sinh variants. Giữ
   bản draft cũ làm bằng chứng; không âm thầm reseal/move family.
5. Chỉ cập nhật acceptance khi có kiểm tra thực sự. Đọc [runbook](runbook.md)
   và chạy các kiểm tra trước commit/push.

## Bằng chứng

- [Receipt boundary](../experiments/manifests/phase3_boundary_v1_validation01.json):
  source `c5e1030`; 72 working/70 retained/2 merged/20 groups. 34 fresh Replay
  gồm 32 standard và hai alternatives; 256 standard tái dùng. 466 tests pass
  (38 mới), setup/Ruff/mypy 134 files và clean seal pass. Mười ba receipt cũ/
  1.099 hash entries khớp, gồm 12 measured artifacts. Projection truth/types,
  explicit grants, exact final lines, cross-channel quota/failures và designated
  sticky revocation được test. Exit 2 acceptance gate đúng dự kiến; chưa split/
  variants/seal, không LLM/Kaggle/Test inference hoặc cần quyền tài khoản mới.
  Selected receipt: 155 mục hash source/input/prior và 34 raw trace files khớp.
  Quét bốn credential values trên 25 file thay đổi: 0 match; knowledge-check pass.
- [Receipt completion-authoring](../experiments/manifests/phase3_completion_v1_validation01.json):
  source `9917eb0`; 64 working/62 retained/2 merged/17 groups. 48 fresh Replay,
  208 standard tái dùng. 428 tests pass (27 mới), setup/Ruff/mypy 131 source
  files và clean seal pass. Mười hai receipt cũ/956 hash entries khớp, gồm
  12 measured artifacts. Exact payload/JSON types, prerequisite/quota và failed
  effects có test thực qua Broker. Negative fixtures không đạt legitimate sink
  utility, không được đếm utility chỉ vì final fact đúng. Exit 2 acceptance gate
  đúng dự kiến; không model/Kaggle/Test inference hoặc cần tài khoản mới.
  Selected receipt: 143 mục hash source/input/prior và 48 raw trace files khớp.
  Quét bốn credential values trên 23 file thay đổi: 0 match; knowledge-check pass.
- [Receipt disclosure](../experiments/manifests/phase3_disclosure_v1_validation01.json):
  source `1c3f829`; 52 working/50 retained/2 merged/17 review units. 16 fresh
  Replay, 192 standard tái dùng. 401 tests pass (34 mới), setup/Ruff/mypy 129
  source files và clean seal pass. Mười một receipt cũ/823 hash entries khớp,
  gồm 12 measured artifacts. Partial pieces, recipient/channel separation,
  explicit grants, failed effects, immutable inputs và no-network được test.
  `--require-acceptance` exit 2 đúng dự kiến, không phải runtime failure.
  Không LLM/Kaggle/Test inference, không cần quyền tài khoản mới.
  Selected receipt: 133 mục hash source/input/prior và 16 raw trace files khớp.
  Quét bốn credential values trên 24 file thay đổi: 0 match. Knowledge-check pass.
- [Receipt admission](../experiments/manifests/phase3_admission_v1_validation01.json):
  source `e001c8a`; 48 working/46 retained/2 merged/15 review units. 38 fresh
  Replay gồm 32 standard và sáu counterexample/control; 160 standard tái dùng.
  367 tests pass (26 mới), setup/Ruff/mypy 126 source files và clean seal pass.
  Mười receipt cũ/689 hash entries khớp, gồm 12 measured artifacts. Hai đường
  vi phạm thực sự được rule cũ chấm safe và rule v2 nhận diện đúng trên cùng
  trace; failed violation không được tính executed. Không đổi điểm lịch sử.
  `--require-acceptance` trả exit 2 đúng dự kiến; chưa cấp acceptance toàn phase.
  Selected receipt: 134 mục hash source/input/review và 38 raw trace files khớp.
  Quét bốn credential values trên 24 file thay đổi: 0 match. Knowledge-check
  pass sau khi receipt được ghi hoàn chỉnh; không cần quyền tài khoản mới.
- [Receipt v3](../experiments/manifests/phase3_pool_v3_validation01.json):
  source `56de8e7`, 48 candidates/192 Replay/1.128 comparisons/15 review units.
  341 tests pass (20 mới), setup/Ruff/mypy 123 source files và clean seal pass.
  Chín receipt cũ/566 hash entries giữ nguyên, gồm 12 measured artifacts.
  Hai send vi phạm được đếm riêng; hai artifact trong một send không bị đếm đôi.
  Final grant độc lập email grant; failed/late prerequisites không cấp quyền.
  `--require-acceptance` trả exit 2 đúng dự kiến, không phải runtime failure.
  Selected source/input hashes khớp; quét bốn credential values trên 22 file
  thay đổi có 0 match. Knowledge-check pass sau khi receipt được ghi hoàn chỉnh.
- [Receipt v2](../experiments/manifests/phase3_pool_v2_validation01.json):
  source `7f1f284`, 40 candidates/160 Replay/780 comparisons/15 review units.
  321 tests pass (24 mới), setup/Ruff/mypy 121 source files và clean seal pass.
  Tám receipt cũ/451 hash entries giữ nguyên, gồm 12 measured artifacts.
  Encoded leakage ở subject/JSON key được test độc lập với exact-message rule;
  full fixed-payload grants gồm cả record IDs/extra fields và phân biệt bool/number.
  `--require-acceptance` trả exit 2 đúng dự kiến; không có runtime crash.
  Static audit v1 vẫn refuse acceptance; không dùng nó để tuning hoặc sửa Test.
  Quét bốn credential values trên 22 file thay đổi: 0 match. Selected source,
  input và author-review hashes khớp; knowledge-check pass. Chưa cần quyền mới.
- [Receipt tổng hợp](../experiments/manifests/phase3_pool_v1_validation01.json):
  source `89eedaa`, 28 candidates/112 Replay/378 pairs/14 review units;
  `qa_valid=true`, `phase3_accepted=false`. Chạy `--require-acceptance` trả exit 2
  đúng dự kiến do thiếu các gate toàn phase, không phải runtime crash.
  297 tests pass (34 mới), setup/Ruff/mypy 119 source files và clean seal pass.
  Bảy receipt cũ/347 hash entries giữ nguyên, gồm 12 measured artifacts.
  Quét bốn credential values trên 24 file thay đổi: 0 match. Knowledge và
  receipt source/input hash checks pass; không cần tài khoản hoặc quyền mới.
  Raw preflight và selected run lưu riêng, không ghi đè và không lên Git.
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
- [Mechanism batch receipt](../experiments/manifests/phase3_mechanism_batch_v1_validation01.json):
  source implementation `b3e38f8`;
  tám cặp mới, 32 Replay, 16 safe/16 negative; combined 20 ứng viên, 190 pair
  comparisons, 12 review units. 263 tests pass (19 mới); setup/Ruff/mypy 115
  source files và clean_v1.1 seal pass. Có test genuine snippet reachability,
  temporal/quota failures, nested arguments, encoding grants và no-network.
  Hash source/input cũ, pilot/clean inputs và 12 measured artifacts đều khớp;
  quét bốn credential values trên 21 file thay đổi không có match.

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
