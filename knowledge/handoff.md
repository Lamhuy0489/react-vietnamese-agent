# Bàn giao phiên làm việc

Cập nhật: 2026-09-07. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

**Phase 4 đã nghiệm thu; Phase 1–4 accepted theo phạm vi/waiver hiện hành.**
Source `be7f8b5`, [closure receipt](../experiments/manifests/phase4_closure_v1_validation01.json),
[báo cáo 12 DoD](../docs/architecture/phase4_report.md).
Host catalog v2, search/DB collection joins, nguồn phụ, deep Dev parity và
overhead study đã kiểm chứng. Không bật defense trong A0. Test vẫn khóa.

## Bước tiếp theo

1. Kiểm tra Git/remote và [phase status](../docs/project/phase_status.md).
   Chạy chất lượng theo [runbook](runbook.md), không tái dựng dữ liệu đã khóa.
2. **Chờ owner cho phép Phase 5**; khi được mở, đọc contract/invariants và
   [phase5](../plan/phase5.md), chốt interfaces/config A1–A6 trước triển khai.
   Không tự coi “làm tiếp Phase 4” là cho phép security enforcement.
3. Source/runtime/data đã hash phải giữ nguyên; thay đổi sau freeze cần version
   mới, phạm vi rerun rõ. Không gỡ seal, không tune trên Test, không chạy authoring
   construction tests đã loại sau seal.
4. Không cần thêm tài khoản/graph database/Kaggle cho mốc vừa hoàn thành.
   Meta access vẫn thiếu cho Llama pilot riêng, không chặn nghiệm thu Phase 4.

## Bằng chứng

- **244 tests pass**, 20 tests closure mới; setup/Ruff/mypy **160 files** và
  knowledge-check pass. Receipt có quality log hashes.
- 45 fresh paired Dev conditions/90 Replay: 21 clean Dev + 24 deep attack/benign,
  đủ tám tool. 152 deep source snapshots, 12 search envelopes, 120 sink fields.
  Source ancestors đến final và S2/UNTRUSTED đến sink fields; exact raw A0 parity.
- 440 smoke Replay đo overhead + hai stress; 532 lượt selected ngoài tests.
  Median added 5,539 ms, p95 11,749 ms; smoke traced peak 527.301 bytes.
  Cả hai guard đặt trước pass. Stress 64 KiB/eight-read: traced peak 21.603.744
  bytes, 4.111.390 log bytes. Timing có tracer không so với untraced timing.
- 153 source/1.625 raw hashes đã đối chiếu, 497 prior hash entries giữ nguyên.
  Stable Dev summary khớp preflight; clean source commit trước selected run.
- Test chỉ hash, không parse payload/GT; clean Dev QA references không đưa
  vào runtime/catalog/prompts. Không model/Kaggle run, không điểm utility/ASR mới.
- [Runtime v1 receipt](../experiments/manifests/phase4_runtime_v1_validation01.json):
  source `a65bc53`, 65 pairs/130 Replay; [primitive receipt](../experiments/manifests/phase4_primitives_v1_validation01.json):
  source `a4e9a87`, 1.650 checks trên Dev. Đây là các mốc lịch sử đã bảo toàn.
- Điểm pilot cũ không đổi: Gemma 6/21, Qwen7B 3/21 Dev. Không diễn giải
  nghiệm thu Phase 4 thành cải thiện chất lượng model hay chống tấn công.

## Giới hạn

Nhãn search/DB là collection joins bảo thủ; provenance theo context, không
token/row-level causal attribution. Source-native labels khác rendered results
phụ thuộc action. Có log/context duplication, chưa content_ref/dedup hoặc bảo đảm
hiệu suất tùy ý theo độ dài. CPU Replay overhead không suy ra GPU/LLM latency.
Raw authoritative; audit-normalized views ngoài prompt, không autocorrect/dịch.
Review assistant theo owner waiver, không independent human review.
Không lưu credentials, private GT, Test payload hoặc CoT trong knowledge.
