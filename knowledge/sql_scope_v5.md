# Bounded SQL row scope v5 — hiện hành

2026-09-14. Nối tiếp [resource scope v4](resource_scope_v4.md).
[Contract](../docs/architecture/phase5_sql_scope_v5_contract.md).

## Đã chốt bounded CPU QA

Parser thuần không chạy SQLite: SELECT explicit columns FROM one table WHERE
key = AWB/AUX literal hoặc IN finite literals. Ghi riêng projection/key/rows;
không cho wildcard, OR, nested query, function, alias, COLLATE, comment hoặc SQL
ngoài grammar. Host row inventory từ exact public catalog không là quyền đọc.
Quyền giữ tuple table/key/row/column theo affirmative raw-user clause; không gộp
Cartesian, không dùng tool content/GT hoặc tự đoán note từ “số ghế”.

Scope v5/runtime v10/pair adapter mới giữ nguyên v4/v9 và các source đã hash.
A0–A3 không enforce v5. Trong row-bound environment: bỏ WHERE, thêm row/column,
đổi bảng/key đều bị deny trước Broker. Legacy unfiltered SQL chỉ giữ hành vi cũ
khi không có row inventory. Document/page scope v4 vẫn được ghép.

Development: unit đầu48pass. Integration draft có 17 failures: bảng awb_notices
bị nhận nhầm row-like ID, chặn cả legitimate read. Đã phân biệt table role trong
raw clause với row identity; không thay benchmark. Sau sửa 78tests pass/40,50s;
thêm ambiguity/budget/Dev coverage và document/page regression. Full QA đã chốt
phía dưới; không chọn development draft làm acceptance.

Static selected Dev: 16/16 trigger được describe, 14/16 có scope ALLOW và 2/16
DENY (matched CAND_ROWLIST không nêu explicit column). Đây là coverage/authorization
parser, không phải model utility/ASR/FPR. Không loại pair, sửa instruction hoặc
ngầm cấp cột để tăng số pass. Giữ `dispatch_allowed=false`.

Source `3667529`: full **3.028pass/1 optional native-tqdm skip/847,08s**;
120focused/44,59s; setup/Ruff/mypy376/knowledge đạt. 531source/463raw/169data
hashes kiểm độc lập khớp. 30completed runtime/31successful tool results,
70synthetic guard sidecars; scope19ALLOW/15DENY theo thiết kế controls.
[Receipt](../experiments/manifests/phase5_sql_scope_v5_cpu01.json) SHA-256
`fe423d620aaefe424d11ad0936e84b046f6d84c4192dbb4bbd2178713d5258a8`.
[Báo cáo](../docs/evaluation/phase5_sql_scope_v5_report.md). Không suy các test counts
thành quality/ASR/FPR. Output đã đóng, không còn QA chạy.

## Bước tiếp theo

Full QA `results/phase5_sql_scope_v5_cpu01` đã chốt và audit; không ghi thêm/chạy trùng.
Tiếp Dev runner/input identity/checkpoints và exact offline package; giữ rõ
column-ambiguity, auxiliary label và broader semantic limits trong report.
Sau package acceptance mới chạy native Kaggle, không retry semantic hoặc mở
Phase6/7/Test. Không cần account mới, không GPU job hoặc model load local.
