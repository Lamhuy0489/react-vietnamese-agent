# Bằng chứng Phase 2

Cập nhật: 2026-09-05. Phase 2 đã accepted.

## Clean benchmark

- 250 task: 150 Dev, 100 held-out Test.
- Quota: 40 single-source, 40 parameter, 50 multi-step, 40 DB+document,
  25 ambiguous, 30 recovery, 25 no-tool.
- 250/250 schema-valid, ground truth đầy đủ và oracle chạy qua Tool Broker.
- 50 documents, 25 cached pages, 8 bảng SQLite; toàn bộ synthetic/offline.
- 0 exact duplicate, 0 accent-insensitive duplicate, 0 semantic duplicate.
- Split seed 2026; 0 task/group/semantic overlap.
- Dataset hash: `2a98633481ac82ae77dbbbe96877d67a3353894ce869e54947e0cf5335371c62`.

## Review waiver

User cho phép bỏ review vì Huy và Minh dùng chung máy. Repository không tạo tên
reviewer giả và không nói user đã kiểm từng task. 250 record dùng automated QA
gate; hạn chế thiếu independent human review ghi trong data card.

## Kaggle Dev pilot

- Dataset private v2: `huylmhuhu/react-vietnamese-agent-phase2-dev-bundle`.
- Kernel private v2: `huylmhuhu/react-vietnamese-agent-phase-2-clean-dev-pilot`.
- Qwen2.5-3B-Instruct v1, NVIDIA T4, internet tắt.
- Bundle: public Dev only; 0 Test, 0 private GT.
- 21/21 terminal, 0 crash, 334 trace hợp lệ, 7/21 strict success.
- Raw artifact local bị ignore: `results/phase2/kaggle_v2`.
- Manifest tracked: `experiments/manifests/phase2_kaggle_v2.json`.

Low score được giữ trung thực như baseline A0, không dùng để sửa Test.
