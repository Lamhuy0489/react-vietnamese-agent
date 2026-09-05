# Phase 8 — Reproducibility, Final Analysis, Thesis Writing & Release Packaging

**Tuần 21–22**

Đây là phase chính thức cuối cùng trước **Buffer tuần 23–24**. Trong bản kế hoạch đã chốt, tuần 21–22 dành cho **phân tích kết quả, kiểm tra khả năng chạy lại và viết báo cáo**, với đầu ra là bản thảo báo cáo/luận văn. Phân công cũng đã khóa: Huy viết kiến trúc hệ thống, A0–A6 và kết quả an toàn; Minh viết dữ liệu, phương pháp đánh giá, capability và robustness; hai người cùng viết mở đầu, kết luận, giới hạn và chỉnh sửa bản cuối. 

Nếu Phase 7 trả lời câu hỏi:

$$
\text{“Kết quả nghiên cứu là gì?”}
$$

thì Phase 8 phải trả lời đồng thời ba câu:

$$
\boxed{\text{Chúng ta kết luận được gì?}}
$$

$$
\boxed{\text{Bằng chứng cho từng kết luận nằm ở đâu?}}
$$

$$
\boxed{\text{Người khác có thể chạy lại như thế nào?}}
$$

---

# I. Mục tiêu tổng thể của Phase 8

Phase 8 không còn là phase phát triển hệ thống.

Ta chuyển từ:

$$
Code + Data + Experiments
$$

sang:

$$
\boxed{
Evidence
+
Reproducibility
+
Scientific\ Narrative
}
$$

Đầu vào của Phase 8 phải là các sản phẩm đã frozen từ Phase 0–7:

* source code;
* A0–A6;
* model manifests;
* benchmark manifests;
* final Test results;
* task-level scores;
* statistics;
* human annotations;
* figures;
* error-analysis records;
* experiment deviations.

Đầu ra phải gồm:

1. **Reproducibility package hoàn chỉnh**.
2. **Final result package đã khóa**.
3. **Bản thảo luận văn đầy đủ**.
4. **Toàn bộ bảng/biểu đồ có thể regenerate bằng code**.
5. **Evidence mapping từ RQ → metric → table → raw result**.
6. **README đủ để người khác hiểu và chạy lại**.
7. Demo tối thiểu nếu cần cho buổi bảo vệ.

Điều này đúng với kết quả dự kiến trong bản Word: mã nguồn, cấu hình, dữ liệu và execution traces phải được quản lý phiên bản để có thể chạy lại; báo cáo cuối phải phân tích trade-off giữa khả năng hoàn thành tác vụ và an toàn. 

---

# II. Nguyên tắc lớn nhất: Phase 8 không được biến thành “Phase sửa kết quả”

Sau khi Phase 7 đã chạy final Test:

$$
Results_{final}
$$

phải được coi là evidence.

Không làm:

```text
viết báo cáo
→ thấy ASR A6 chưa đẹp
→ sửa rule
→ rerun
→ thay số
```

Nếu làm như vậy:

$$
Test
\rightarrow
System\ Modification
$$

và held-out property bị phá.

Phase 8 chỉ được sửa:

* typo;
* format;
* plotting;
* documentation;
* packaging;
* bug không ảnh hưởng experimental semantics.

Nếu phát hiện **bug thực nghiệm có ảnh hưởng semantics**, không tự sửa âm thầm.

Phải đưa sang:

$$
\boxed{Buffer\ Phase}
$$

với deviation record và rerun affected experiments theo protocol.

---

# III. Phase 8 nên chia thành bốn workstream

Tôi khuyên tổ chức:

$$
P_8=
\{
W_1,W_2,W_3,W_4
\}
$$

trong đó:

### W1 — Result Freeze & Evidence Audit

Khóa kết quả và xác minh mọi con số.

### W2 — Reproducibility Package

Đảm bảo code/data/config có thể chạy lại.

### W3 — Thesis Writing

Biến evidence thành luận văn.

### W4 — Release/Demo Packaging

Chuẩn bị repository, demo và tài liệu cuối.

---

# IV. Workstream 1 — Final Result Freeze

Trước khi viết phần Results, phải tạo một snapshot kết quả chính thức.

Tạo:

```text
results/final_release/
```

Không viết báo cáo từ các file:

```text
results/tmp/
results/old/
results/test2/
results/final_new/
```

vì rất dễ lấy nhầm số.

---

# V. Final Result Manifest

Tạo:

```text
results/final_release/final_results_manifest.json
```

Ví dụ:

```json
{
  "release_id": "results-v1.0",

  "git_commit": "...",

  "evaluator_version": "evaluation-v1.0",

  "experiments": {
    "E1": {
      "status": "complete",
      "manifest_hash": "..."
    },
    "E2": {
      "status": "complete",
      "manifest_hash": "..."
    },
    "E3": {
      "status": "complete",
      "manifest_hash": "..."
    }
  },

  "datasets": {
    "clean": "...",
    "adversarial": "...",
    "benign": "...",
    "robustness": "..."
  },

  "generated_at": "...",

  "frozen": true
}
```

Sau đó:

$$
SHA256(manifest)
$$

và Git tag.

Ví dụ:

```text
results-v1.0
```

---

# VI. Single Source of Truth cho số liệu

Quy định:

$$
TaskScores
\rightarrow
Aggregates
\rightarrow
Tables
\rightarrow
Figures
\rightarrow
Thesis.
$$

Không có:

```text
Excel chỉnh tay
→ thesis
```

Không có:

```text
copy số từ notebook cũ
→ table Word
```

Nguồn chuẩn:

```text
results/final_release/task_scores/
```

Tất cả bảng phải regenerate từ đây.

---

# VII. Evidence chain

Một số trong luận văn phải truy được:

$$
Claim
\rightarrow
Table
\rightarrow
CSV
\rightarrow
TaskScore
\rightarrow
Trace.
$$

Ví dụ luận văn viết:

> “A6 giảm ASR so với A0...”

Phải truy được:

```text
Chapter 5
    ↓
Table 5.3
    ↓
RQ2_security.csv
    ↓
task_scores_E2.jsonl
    ↓
runs/E2/*
```

Đây là reproducibility ở cấp **research evidence**, không chỉ code chạy được.

---

# VIII. Claim–Evidence Matrix

Đây là file tôi rất khuyên tạo:

```text
docs/claim_evidence_matrix.md
```

Ví dụ:

| Claim ID | RQ  | Claim                                 | Evidence    | Statistics  | Thesis location |
| -------- | --- | ------------------------------------- | ----------- | ----------- | --------------- |
| C1       | RQ1 | Models differ in TSR                  | Table RQ1-1 | Wilson CI   | Sec. 5.1        |
| C2       | RQ2 | A6 reduces ASR vs A0                  | Table RQ2-1 | McNemar     | Sec. 5.2        |
| C3       | RQ2 | A6 reduces A5 overblocking            | Table RQ2-3 | paired diff | Sec. 5.2.4      |
| C4       | RQ3 | zero-width causes largest degradation | Table RQ3-1 | paired test | Sec. 5.3        |

Không cần claim nào cũng “positive”.

Ví dụ:

```text
C7:
A6 vẫn fail trên một số paraphrased tool-output attacks.
```

cũng là một claim hợp lệ.

---

# IX. RQ Answer Sheet

Tạo:

```text
docs/rq_answers.md
```

Mỗi RQ phải có đúng bốn phần.

### RQ1

```text
Question
↓
Metrics
↓
Evidence
↓
Answer
```

Ví dụ structure:

```text
RQ1:
Tác nhân có khả năng hoàn thành tác vụ tiếng Việt ở mức nào?

Primary evidence:
- TSR
- ToolSelAcc
- ArgAcc
- SeqAcc
- ErrRecovery

Conclusion:
<chỉ điền từ final results>
```

Tương tự RQ2/RQ3.

---

# X. Không bắt đầu Results bằng văn xuôi

Quy trình viết đúng:

```text
final CSV
↓
table
↓
figure
↓
statistical result
↓
bullet findings
↓
prose
```

Không:

```text
viết conclusion trước
↓
tìm số để minh họa.
```

Điều này giảm confirmation bias.

---

# XI. Reproducibility package — ba cấp

Với điều kiện nhóm dùng laptop CPU local và Kaggle GPU, tôi khuyên hỗ trợ ba cấp reproduction.

## Level 1 — CPU Smoke Reproduction

Không cần GPU.

Người dùng clone repo rồi chạy:

```text
A0
+
Dummy/Replay backend
+
mock tools
+
small smoke dataset.
```

Mục tiêu:

$$
\text{verify system wiring}.
$$

---

## Level 2 — Evaluation Reproduction

Không cần inference GPU.

Dùng frozen traces:

$$
Traces
\rightarrow
Evaluator
\rightarrow
Tables
\rightarrow
Figures.
$$

Đây là cấp quan trọng nhất cho giảng viên/reviewer.

Người khác phải có thể regenerate các bảng chính mà không cần chạy hàng nghìn LLM calls.

---

## Level 3 — Full Inference Reproduction

Cần Kaggle/GPU.

$$
Frozen\ Dataset
+
Frozen\ Models
+
Frozen\ Config
\rightarrow
Final\ Runs.
$$

Đây là expensive reproduction.

README phải phân biệt ba cấp rõ.

---

# XII. Reproduction command design

Lý tưởng có các command tương đối rõ:

```bash
python scripts/verify_release.py
```

CPU smoke:

```bash
python scripts/run_smoke.py --backend replay
```

Evaluation reproduction:

```bash
python scripts/reproduce_tables.py \
    --release results-v1.0
```

Figures:

```bash
python scripts/reproduce_figures.py \
    --release results-v1.0
```

Full inference có thể dùng Kaggle-specific runner riêng.

---

# XIII. Một lệnh không nhất thiết phải chạy cả nghiên cứu

Không cố tạo:

```bash
python reproduce_everything.py
```

rồi mất hàng giờ/GPU.

Nên phân cấp:

```text
verify
evaluate
figures
full-inference
```

rõ ràng.

---

# XIV. Repository structure cuối cùng

Tôi đề xuất sau Phase 8 repo có cấu trúc gần:

```text
react-vietnamese-agent/
│
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── configs/
│   ├── agent/
│   ├── security/
│   ├── normalization/
│   ├── models/
│   └── experiments/
│
├── src/
│   └── react_agent/
│       ├── agent/
│       ├── tools/
│       ├── security/
│       ├── normalization/
│       ├── artifacts/
│       ├── provenance/
│       └── evaluation/
│
├── data/
│   ├── smoke/
│   ├── clean/
│   ├── adversarial/
│   └── robustness/
│
├── experiments/
│   ├── manifests/
│   └── final/
│
├── scripts/
│   ├── verify_release.py
│   ├── run_smoke.py
│   ├── run_experiment.py
│   ├── evaluate_run.py
│   ├── reproduce_tables.py
│   └── reproduce_figures.py
│
├── results/
│   └── final_release/
│
├── tests/
│
├── notebooks/
│   └── kaggle/
│
├── docs/
│   ├── architecture/
│   ├── benchmark/
│   ├── evaluation/
│   ├── reproducibility/
│   └── thesis_support/
│
└── thesis/
    ├── figures/
    ├── tables/
    └── source/
```

---

# XV. `README.md` cuối cần trả lời 10 câu

Một người mới mở repo phải biết ngay:

1. Đề tài nghiên cứu gì?
2. RQ1–RQ3 là gì?
3. A0–A6 là gì?
4. Có những dataset nào?
5. Có những tools nào?
6. Chạy smoke test như thế nào?
7. Reproduce metrics như thế nào?
8. Reproduce full inference như thế nào?
9. Kết quả final nằm ở đâu?
10. Những limitations nào cần biết?

Không biến README thành toàn bộ luận văn.

---

# XVI. README structure

Tôi đề xuất:

```text
# Project title

## Overview
## Research Questions
## Architecture
## Repository Layout
## Installation
## Quick Smoke Test
## Datasets
## Security Configurations A0–A6
## Reproducing Evaluation
## Reproducing Final Experiments
## Results
## Reproducibility
## Limitations
```

---

# XVII. Environment reproducibility

Cần khóa:

```text
Python version
package versions
CUDA-related environment nếu cần
Transformers version
PyTorch version
model revision
```

Không chỉ:

```text
transformers
torch
numpy
```

không version.

Ít nhất final manifest phải ghi dependency versions thực tế của runs.

---

# XVIII. Kaggle environment record

Vì inference chạy trên Kaggle, mỗi final run cần biết:

```text
Kaggle notebook/kernel version
accelerator class nếu có
Python
PyTorch
Transformers
bitsandbytes hoặc quantization library nếu dùng
model revision
```

Không cần đảm bảo hardware hoàn toàn giống về sau, nhưng phải record.

---

# XIX. Model reproducibility

Không chỉ lưu:

```text
Qwen ...
```

Phải lưu:

$$
ModelIdentity
=
(
repository,
revision,
tokenizer\ revision,
quantization,
generation\ config
).
$$

Nếu model revision không pin:

$$
Reproduction
$$

sau này có thể khác.

---

# XX. Dataset reproducibility

Mỗi final dataset:

```text
clean
attack
benign
robustness
```

phải có:

* version;
* item count;
* manifest;
* SHA256;
* schema version.

Ví dụ:

```text
clean_v1.0
```

Không:

```text
clean_final_final2.jsonl.
```

---

# XXI. Config reproducibility

A0–A6:

```text
A0.yaml
...
A6.yaml
```

mỗi file canonicalized và hash.

Tạo:

```text
configs/security/manifest.json
```

Chứa:

```json
{
  "A0": "...",
  "A1": "...",
  "A2": "...",
  "A3": "...",
  "A4": "...",
  "A5": "...",
  "A6": "..."
}
```

---

# XXII. Full Run Identity

Giữ invariant:

$$
R=
(
git\_commit,
h_{config},
h_{data},
model\_revision,
seed
).
$$

Nên mở rộng final version:

$$
R=
(
commit,
configHash,
datasetHash,
modelRevision,
tokenizerRevision,
generationHash,
evaluatorVersion,
seed
).
$$

Nếu hai run có identity khác:

không được coi là cùng experimental condition.

---

# XXIII. `verify_release.py`

Script này cực kỳ đáng làm.

Nó kiểm tra:

* file tồn tại;
* SHA256;
* configs đúng;
* dataset counts;
* model manifest;
* result counts;
* tables present;
* figures present;
* no missing traces;
* Git commit metadata;
* evaluator version.

Output:

```text
[PASS] Clean benchmark checksum
[PASS] Attack benchmark checksum
[PASS] A0–A6 config hashes
[PASS] E1 results
[PASS] E2 results
[PASS] E3 results
[PASS] Tables reproducible
...
```

Cuối:

```text
RELEASE VALID
```

---

# XXIV. Release Integrity Report

Tạo:

```text
docs/reproducibility/release_integrity_report.md
```

Ví dụ:

```text
Code commit       PASS
Data hashes       PASS
Config hashes     PASS
Result counts     PASS
Evaluation replay PASS
Figure replay     PASS
Mac CPU smoke     PASS
Windows CPU smoke PASS
Kaggle smoke      PASS
```

Điều này rất thuyết phục khi bảo vệ.

---

# XXV. Cross-machine test

Nhóm có hai máy khác nhau, đây là lợi thế để kiểm reproducibility.

Tôi khuyên:

### Huy

Fresh clone trên một máy.

### Minh

Fresh clone trên máy còn lại.

Mỗi người không dùng virtual environment cũ.

Chạy:

```text
install
→ verify
→ smoke
→ evaluation replay.
```

Nếu cả hai máy đều pass:

$$
ReproducibilityConfidence\uparrow.
$$

---

# XXVI. Không cần cả hai máy chạy full LLM inference

Full GPU reproduction để Kaggle.

Local test chỉ cần:

* imports;
* schemas;
* tools;
* Dummy/Replay;
* evaluator;
* tables/figures.

---

# XXVII. Fresh-clone rule

Không kiểm reproducibility bằng chính working folder đã dùng 5 tháng.

Phải:

```text
new directory
git clone
new venv
install
```

Mục đích bắt lỗi:

* file chưa commit;
* path hard-coded;
* local cache dependency;
* missing configs;
* missing data files.

---

# XXVIII. Kiểm tra hard-coded paths

Search repo cho các pattern như:

```text
C:\Users\...
/Users/huy/...
/kaggle/input/some-old-name
```

Không để core code phụ thuộc path cá nhân.

Path phải đến từ config/environment.

---

# XXIX. Kiểm tra secrets

Trước release:

* Kaggle token;
* GitHub PAT;
* API keys;
* `.env`;
* notebook output chứa secret.

Tất cả phải absent khỏi Git.

Dù benchmark không dùng dịch vụ thật, repository hygiene vẫn cần.

---

# XXX. Kiểm tra dữ liệu

Word yêu cầu toàn bộ dữ liệu nghiên cứu là synthetic, không dùng dữ liệu cá nhân thật. 

Phase 8 phải audit:

* names;
* emails;
* student IDs;
* phone values;
* webhook endpoints.

Nếu nhìn giống dữ liệu thật, phải đảm bảo rõ ràng là synthetic/test namespace.

---

# XXXI. Final data card

Tạo một data card cho benchmark:

```text
docs/benchmark/data_card.md
```

Nội dung:

### Dataset purpose

Đánh giá Vietnamese tool-using ReAct.

### Composition

```text
250 clean
70 canonical attacks
350 attack variants
350 benign variants
300 robustness cases
```

### Splits

Dev/Test.

### Generation

Synthetic.

### Variant types

5 Vietnamese transformations.

### Limitations

* simulated university domain;
* synthetic data;
* finite attack taxonomy;
* no real web;
* no real external actions.

---

# XXXII. Model card / system card mức đồ án

Không cần formal industry model card.

Nhưng nên có:

```text
docs/system/system_card.md
```

Ghi:

* ReAct architecture;
* tools;
* A0–A6;
* external mock sinks;
* threat model;
* no training;
* evaluation conditions;
* intended use;
* non-goals.

---

# XXXIII. Final architecture diagram

Phase 8 phải tạo một architecture figure rõ.

Nên thể hiện:

```text
User
 ↓
ReAct Agent
 ↓
Parser
 ↓
Pre-Gate
 ↓
Tool Broker
 ↓
Mock Tool
 ↓
Post-Gate
 ↓
Artifact Store / Provenance
 ↓
Agent
 ↓
Final-Gate
 ↓
User
```

Bên cạnh:

```text
Sensitivity
Trust
Guard Signals
Provenance
```

Không cần diagram quá phức tạp.

---

# XXXIV. A0–A6 comparison table trong thesis

Bảng nên cố định:

| Component               | A0 | A1 | A2 | A3 | A4 | A5 | A6 |
| ----------------------- | -: | -: | -: | -: | -: | -: | -: |
| Rule guard              |    |  ✓ |  ✓ |  ✓ |  ✓ |  ✓ |  ✓ |
| LLM guard               |    |    |  ✓ |  ✓ |  ✓ |  ✓ |  ✓ |
| Sensitivity             |    |    |    |  ✓ |  ✓ |  ✓ |  ✓ |
| Trust/taint             |    |    |    |    |  ✓ |  ✓ |  ✓ |
| Session combined policy |    |    |    |    |    |  ✓ |  ✓ |
| Artifact provenance     |    |    |    |    |    |    |  ✓ |
| Final gate              |    |    |    |    |    |    |  ✓ |

Đây nên là một trong những bảng methodology quan trọng nhất.

---

# XXXV. Cấu trúc luận văn đề xuất

Tôi khuyên 7 chương chính.

## Chương 1 — Introduction

* bối cảnh;
* vấn đề;
* motivation;
* research gap;
* mục tiêu;
* RQ1–RQ3;
* contributions;
* phạm vi.

---

## Chương 2 — Background & Related Work

* LLM agents;
* ReAct;
* tool use;
* prompt injection;
* indirect prompt injection;
* data-flow/security control;
* provenance;
* Vietnamese robustness;
* related evaluation benchmarks.

Đây là phần duy nhất có thể cần bổ sung literature review nhiều hơn trong Phase 8.

---

## Chương 3 — System & Threat Model

* simulated university setting;
* ReAct runtime;
* 8 mock tools;
* attacker capability;
* security boundaries;
* external sinks;
* A0 baseline.

---

## Chương 4 — Benchmark & Security Architecture

Có thể chia:

### 4.1 Clean benchmark

250 tasks.

### 4.2 Adversarial benchmark

70 canonical + variants + benign.

### 4.3 Vietnamese robustness set

50+250.

### 4.4 Artifact/data model

Sensitivity/trust/provenance.

### 4.5 A1–A6

component architecture.

### 4.6 A6 Pre/Post/Final Gate.

---

## Chương 5 — Evaluation Methodology

* RQ ↔ metrics;
* models;
* decoding;
* experimental matrices E1/E2/E3;
* TSR;
* ASR;
* FPR;
* PVR;
* STSR;
* robustness metrics;
* statistics;
* human validation;
* reproducibility.

---

## Chương 6 — Results & Discussion

Tổ chức theo RQ, không theo timeline implementation.

### 6.1 RQ1 — Capability

E1.

### 6.2 RQ2 — Security

E2.

### 6.3 RQ3 — Vietnamese Robustness

E3.

### 6.4 Error Analysis

### 6.5 Security–Utility Trade-off

---

## Chương 7 — Limitations & Conclusion

* limitations;
* threats to validity;
* future work;
* direct answer RQ1–RQ3;
* contribution summary.

---

# XXXVI. Không viết luận văn theo “tuần 1 tôi làm gì”

Đồ án không nên đọc như nhật ký:

```text
Tuần 1 chúng tôi...
Tuần 2 chúng tôi...
```

Timeline chỉ là quản lý dự án.

Scientific narrative phải theo:

$$
Problem
\rightarrow
Method
\rightarrow
Experiment
\rightarrow
Evidence
\rightarrow
Conclusion.
$$

---

# XXXVII. Introduction nên có logic nào?

Tôi khuyên:

$$
Tool\ Agent\ Utility
$$

↓

$$
Untrusted\ Tool\ Data\ Risk
$$

↓

$$
Vietnamese\ Robustness\ Gap
$$

↓

$$
Need\ Controlled\ Evaluation
$$

↓

$$
Research\ Questions
$$

↓

$$
Contributions.
$$

Không bắt đầu bằng lịch sử AI quá dài.

---

# XXXVIII. Contribution statement

Contribution không nên ghi:

> “Chúng tôi xây chatbot.”

Thay vào đó, nếu kết quả hỗ trợ, contribution có thể cấu trúc:

1. Một synthetic Vietnamese benchmark cho tool-using ReAct agents.
2. Một experimental comparison A0–A6.
3. Một provenance-aware A6 architecture với Pre/Post/Final enforcement.
4. Một paired robustness evaluation trên năm biến thể tiếng Việt.
5. Một reproducible experimental package.

Phải đảm bảo wording không vượt quá evidence.

---

# XXXIX. Methodology phải được viết trước Results

Methodology mô tả protocol đã khóa.

Không viết:

> “Chúng tôi sử dụng metric X vì X cho kết quả tốt.”

Phải viết metric độc lập với kết quả.

---

# XL. Results và Discussion phải tách logic

### Results

Nói:

$$
What\ happened?
$$

Ví dụ:

* metric;
* CI;
* comparison;
* p-value;
* observed patterns.

### Discussion

Nói:

$$
Why\ might\ this\ matter?
$$

và:

$$
What\ does\ it\ imply?
$$

Không trộn speculation vào bảng kết quả.

---

# XLI. Template phân tích mỗi RQ

Tôi đề xuất dùng cùng cấu trúc.

### 1. Restate RQ

### 2. Primary metric/table

### 3. Main quantitative finding

### 4. Statistical evidence

### 5. Category/variant breakdown

### 6. Error analysis

### 7. Direct answer

Ví dụ:

```text
RQ2 Answer:
Under the evaluated conditions, ...
```

Không để reader tự suy ra.

---

# XLII. RQ1 Writing Logic

Bắt đầu:

$$
TSR_{M1},TSR_{M2},TSR_{M3}.
$$

Sau đó:

* ToolSelAcc;
* ArgAcc;
* SeqAcc;
* ErrRecovery.

Tiếp:

* category differences;
* failure modes.

Kết luận:

> model nào mạnh ở đâu?

Không chỉ:

> model nào có overall score cao nhất?

---

# XLIII. RQ2 Writing Logic

Bắt đầu:

$$
A0\rightarrow A6.
$$

Primary:

$$
ASR,\quad FPR,\quad STSR.
$$

Sau đó:

$$
PVR_{proposed}
$$

vs:

$$
PVR_{executed}.
$$

Đây là một story rất hay:

Nếu A6 vẫn có unsafe proposals nhưng:

$$
PVR_{executed}\ll PVR_{proposed}
$$

thì runtime enforcement đang hoạt động.

---

# XLIV. A5 vs A6 discussion

Đây có thể là core contribution.

Tập trung:

$$
ASR(A5)\ vs\ ASR(A6)
$$

và:

$$
FPR(A5)\ vs\ FPR(A6).
$$

Nếu A6 giữ security nhưng giảm FPR:

đó là evidence cho lợi ích của fine-grained provenance.

Nếu không:

phải nói trung thực rằng provenance tăng complexity nhưng chưa cải thiện utility đáng kể trong benchmark này.

Không force narrative.

---

# XLV. RQ3 Writing Logic

Nên phân biệt:

$$
Capability\ robustness
$$

và:

$$
Security\ robustness.
$$

Không gộp thành một điểm.

Ví dụ:

```text
No-diacritic:
 capability ...
 security ...

Zero-width:
 capability ...
 security ...
```

Điều này cho thấy transformation nào ảnh hưởng loại failure nào.

---

# XLVI. Statistical wording

Không viết:

> “A6 chắc chắn tốt hơn.”

Nên viết:

> “Trong bộ đánh giá này, A6 đạt ... so với ..., với chênh lệch ... percentage points và ...”

Sau đó CI/test.

Tránh suy rộng quá phạm vi benchmark.

---

# XLVII. Không nhầm “không significant” với “không khác biệt”

Nếu:

$$
p>0.05
$$

không có nghĩa:

$$
Effect=0.
$$

Viết:

> “Không có đủ bằng chứng thống kê để kết luận sự khác biệt trong sample này.”

và báo effect size + CI.

---

# XLVIII. Threats to Validity

Đây là phần bắt buộc phải viết tốt.

Tôi khuyên chia bốn nhóm.

## Construct validity

Metrics có thật sự đo capability/security không?

Ví dụ:

* task success approximation;
* value-origin provenance không phải causal provenance nội bộ model.

---

## Internal validity

Khác biệt A0–A6 có thực sự do defense?

Giảm threat bằng:

* same runtime;
* same model;
* same tasks;
* frozen configs;
* paired evaluation.

---

## External validity

Benchmark university synthetic có generalize không?

Giới hạn:

* one domain;
* synthetic data;
* 8 tools;
* single agent;
* no Internet.

---

## Conclusion validity

* finite Test size;
* statistical uncertainty;
* correlated variants;
* human annotation error.

---

# XLIX. Limitations quan trọng nên thừa nhận

Ít nhất:

1. Synthetic environment.
2. Một miền university assistant.
3. Chỉ single ReAct agent.
4. Finite attack taxonomy.
5. Mock external sinks.
6. No direct Internet.
7. No fine-tuning.
8. Selected open/current LLM backbones only.
9. Conservative provenance approximation.
10. Vietnamese transformations chỉ đại diện một số dạng variation.

Những giới hạn này phù hợp với phạm vi đã ghi trong Word. 

---

# L. Không gọi provenance là “perfect provenance”

Đây là một điểm học thuật quan trọng.

Nếu A6 dùng context/value-origin tracking:

không được viết:

> “A6 xác định chính xác dữ liệu nào model sử dụng.”

Nên viết:

> “A6 maintains observable artifact lineage and conservative/value-origin provenance over the agent execution layer.”

Vì không theo dõi causality bên trong hidden neural computation.

---

# LI. Reproducibility section trong thesis

Nên ghi:

$$
R=
(
GitCommit,
DataHash,
ConfigHash,
ModelRevision,
Seed
).
$$

Và giải thích:

* source versioned;
* datasets immutable;
* configs hash;
* model revisions pinned;
* traces preserved;
* table generation scripted.

Đây là một điểm mạnh của đồ án.

---

# LII. Figure/Table provenance

Mỗi figure nên có metadata file hoặc script.

Ví dụ:

```text
figures/rq2_tradeoff.png
```

sinh bởi:

```text
scripts/figures/plot_rq2_tradeoff.py
```

từ:

```text
tables/RQ2_security.csv.
```

Không chỉnh figure bằng Photoshop/PowerPoint sau generation.

---

# LIII. Table schema

Mỗi table nên có:

* denominator;
* point estimate;
* CI nếu primary;
* direction ↑/↓;
* footnote khi metric not applicable.

Ví dụ:

```text
ASR ↓
```

không chỉ:

```text
ASR.
```

---

# LIV. Rounding policy

Khóa trước:

Ví dụ:

* percentages: 1 decimal;
* confidence intervals: 1 decimal percentage point;
* p-values: 3 decimals;
* \(p<0.001\) nếu rất nhỏ.

Không bảng này 3 decimals, bảng kia 0 decimals tùy ý.

---

# LV. Thesis consistency checker

Có thể viết simple script:

```text
scripts/check_report_consistency.py
```

Nó kiểm:

* table CSV count;
* RQ IDs;
* metric names;
* expected figure files;
* result manifest hashes.

Không cần parse Word/PDF phức tạp.

---

# LVI. Cross-check số liệu bằng hai người

Huy chịu trách nhiệm RQ2, nhưng Minh phải independently verify một số key metrics.

Minh chịu trách nhiệm RQ1/RQ3, nhưng Huy verify.

Ví dụ:

### Minh kiểm RQ2

Tự tính:

$$
ASR(A6)=
\frac{\sum attack\_success}{150}.
$$

### Huy kiểm RQ1

Tự tính:

$$
TSR(M_2)=
\frac{\sum task\_success}{100}.
$$

Nếu kết quả lệch:

không viết tiếp cho đến khi giải quyết.

---

# LVII. Report number audit

Tạo file:

```text
docs/thesis_support/number_audit.csv
```

Columns:

```text
metric_id
experiment
source_file
expected_value
verified_by
status
```

Ví dụ:

```text
RQ2_ASR_A6
E2
RQ2_security.csv
0.xxx
Minh
PASS
```

---

# LVIII. Huy — phần viết chính

Theo phân công Word, Huy phụ trách phần kiến trúc hệ thống, các mức bảo vệ và kết quả an toàn. 

Tôi cụ thể hóa:

### Huy viết draft chính

* System architecture.
* ReAct runtime.
* Tool broker.
* A0 baseline.
* A1–A6.
* Threat model.
* PreGate.
* PostGate.
* FinalGate.
* Policy reasoning ở cấp observable system.
* RQ2 experimental setup.
* RQ2 results.
* Security error analysis.
* Security–utility trade-off.

---

# LIX. Minh — phần viết chính

Theo Word, Minh phụ trách dữ liệu, phương pháp đánh giá, capability và robustness. 

Cụ thể:

* Synthetic environment.
* Clean benchmark.
* Attack/benign benchmark.
* Vietnamese variants.
* Dataset QA.
* Evaluation framework.
* Metrics.
* Statistical protocol.
* RQ1 setup/results.
* RQ3 setup/results.
* Human validation.
* Capability/robustness error analysis.

---

# LX. Phần hai người cùng viết

Cả hai:

* Abstract.
* Introduction.
* Problem statement.
* Contributions.
* Related Work synthesis.
* Discussion.
* Limitations.
* Threats to validity.
* Conclusion.
* Future work.
* Final editing.

Không để hai người mỗi người viết nửa Introduction rồi ghép.

Một người tạo first integrated draft, người kia review.

---

# LXI. Cross-review protocol

Huy review phần Minh về:

* data counts;
* benchmark design;
* metric interpretation.

Minh review phần Huy về:

* A0–A6 semantics;
* security claims;
* provenance wording.

Sau đó reverse check:

$$
Author\neq FinalReviewer.
$$

---

# LXII. Một quy tắc viết rất quan trọng

Không dùng code implementation detail quá mức trong luận văn.

Ví dụ không cần:

```text
class ArtifactStore:
```

trừ khi cần pseudo-code.

Luận văn mô tả:

$$
concept
\rightarrow
algorithm
\rightarrow
invariant.
$$

Code details ở repository.

---

# LXIII. Pseudocode nên có

Tôi khuyên 3 algorithm boxes.

### Algorithm 1 — ReAct Execution Loop

### Algorithm 2 — A6 Pre/Post/Final Security Flow

### Algorithm 3 — Evaluation/Scoring

Không cần pseudocode cho từng function nhỏ.

---

# LXIV. A6 algorithm representation

Ví dụ logic khái quát:

```text
Receive proposed action
      ↓
Resolve destination/payload artifacts
      ↓
Inspect sensitivity
      ↓
Inspect trust
      ↓
Resolve provenance
      ↓
Check user authorization
      ↓
Allow / Deny
```

Sau tool:

```text
ToolResult
→ artifact
→ labels
→ provenance
→ guard signals
→ context.
```

Final:

```text
Model final
→ inspect sensitive origins
→ allow / redact / deny.
```

---

# LXV. Demo packaging

Bản Word chính thức tập trung vào report/reproducibility, không bắt buộc một application UI. Vì vậy demo nên giữ **tối giản**, không xây web app mới ở Phase 8.

Có thể tạo:

```bash
python scripts/demo.py \
   --config A6 \
   --scenario demo_attack_01
```

Output terminal:

```text
USER
↓
TOOL CALL
↓
TOOL RESULT
↓
SECURITY DECISION
↓
FINAL
```

Đây đã đủ để bảo vệ đồ án.

---

# LXVI. Demo scenarios

Chỉ cần 3–4 scenarios.

### Demo 1 — Clean multi-step

A0/A6 đều hoàn thành.

### Demo 2 — Indirect injection

A0 có thể execute mock violation; A6 block.

### Demo 3 — Benign external action

A6 allow đúng.

### Demo 4 — Final answer leakage

A6 redact/deny.

Không demo bằng Test benchmark case nếu bạn muốn giữ Test package ít exposed; có thể dùng dedicated Dev/demo cases.

---

# LXVII. Demo không được dùng Internet thật

Vẫn giữ:

$$
send\_email\_mock
$$

$$
post\_webhook\_mock.
$$

Không vì bảo vệ mà đổi sang email thật/webhook thật.

Word đã quy định mọi external action chỉ mô phỏng. 

---

# LXVIII. Week 21 — Result freeze + first thesis draft

## Ngày 1 — Final Evidence Freeze

Hai người:

* verify Phase 7 result counts;
* hash final results;
* create final manifest;
* freeze table/figure inputs;
* create claim-evidence matrix.

Không viết Results trước bước này.

---

## Ngày 2 — Reproducibility infrastructure

Tạo:

```text
verify_release.py
reproduce_tables.py
reproduce_figures.py
```

Fresh clone CPU smoke.

---

## Ngày 3 — Structure luận văn

Chốt:

* chapters;
* section numbers;
* figure IDs;
* table IDs;
* RQ mapping.

Tạo document skeleton.

---

## Ngày 4–5 — Parallel writing

Huy:

* architecture;
* threat model;
* A0–A6;
* RQ2 methods/results.

Minh:

* benchmark;
* evaluation;
* RQ1/RQ3 methods/results.

---

## Ngày 6 — Tables & figures

Generate final:

* RQ1 tables;
* RQ2 tables;
* RQ3 tables;
* figures.

Chèn từ final release only.

---

## Ngày 7 — First integrated draft

Merge.

Mục tiêu:

$$
100\%
$$

chapters có nội dung, dù wording chưa hoàn hảo.

Không để:

```text
TODO RESULTS
TODO LIMITATIONS
```

ở cuối Week 21.

---

# LXIX. Week 22 — Reproducibility audit + editorial convergence

## Ngày 1 — Cross review

Huy review Minh.

Minh review Huy.

Focus:

* technical correctness;
* claims;
* numbers;
* terminology.

---

## Ngày 2 — RQ audit

Với từng RQ kiểm:

```text
RQ
→ metric
→ experiment
→ table
→ finding
→ answer.
```

Nếu một RQ không có direct answer, phải sửa structure.

---

## Ngày 3 — Reproducibility fresh clone

Huy và Minh chạy independent fresh clone.

Check:

* install;
* smoke;
* evaluation replay;
* table recreation.

---

## Ngày 4 — Limitations / threats / discussion

Viết kỹ:

* not only strengths;
* failure cases;
* trade-offs;
* external validity.

---

## Ngày 5 — Number audit

Mỗi final numerical claim cross-check.

Không chỉ table.

Cả văn xuôi:

> “A6 giảm X percentage points…”

phải kiểm lại bằng script/source.

---

## Ngày 6 — Final draft v1

Format:

* captions;
* cross references;
* equations;
* terminology;
* bibliography;
* appendices.

---

## Ngày 7 — Phase 8 Freeze

Tag:

```text
thesis-draft-v1
```

và:

```text
reproducibility-release-v1
```

Sau đó chuyển sang Buffer.

---

# LXX. Checklist Phase 8 — Inputs

* [ ] E1 complete.
* [ ] E2 complete.
* [ ] E3 complete.
* [ ] Human validation complete.
* [ ] Statistical tests complete.
* [ ] Error analysis complete.
* [ ] Final task scores frozen.
* [ ] No missing final experiment runs.
* [ ] Experiment deviation log complete.
* [ ] Phase 7 manifest valid.

---

# LXXI. Checklist — Result Freeze

* [ ] `final_results_manifest.json`.
* [ ] Git commit recorded.
* [ ] Result hash generated.
* [ ] E1 manifest hash.
* [ ] E2 manifest hash.
* [ ] E3 manifest hash.
* [ ] Evaluator version recorded.
* [ ] Table inputs frozen.
* [ ] Figure inputs frozen.
* [ ] No temp results mixed into final.
* [ ] Result release tagged.

---

# LXXII. Checklist — Evidence Audit

* [ ] RQ1 has primary evidence.
* [ ] RQ2 has primary evidence.
* [ ] RQ3 has primary evidence.
* [ ] Every primary claim references a final result.
* [ ] Every final result references task scores.
* [ ] Task scores trace back to runs.
* [ ] Run manifest traceable.
* [ ] Claim–evidence matrix complete.
* [ ] Negative/null findings included.
* [ ] No unsupported causal claims.

---

# LXXIII. Checklist — Reproducibility Code

* [ ] Fresh install works.
* [ ] CPU smoke works.
* [ ] Replay backend works.
* [ ] Evaluation replay works.
* [ ] Tables regenerate.
* [ ] Figures regenerate.
* [ ] `verify_release.py` exists.
* [ ] Checksum verification works.
* [ ] Missing file produces clear failure.
* [ ] Hard-coded local paths removed.
* [ ] All scripts use config paths.

---

# LXXIV. Checklist — Repository Hygiene

* [ ] README finalized.
* [ ] `.gitignore` complete.
* [ ] No credentials.
* [ ] No tokens.
* [ ] No private `.env`.
* [ ] No large irrelevant caches.
* [ ] No notebook secrets.
* [ ] No real personal data.
* [ ] Temporary result folders excluded.
* [ ] File naming consistent.
* [ ] Dead code identified/removed where safe.
* [ ] No critical uncommitted local files.

---

# LXXV. Checklist — Environment

* [ ] Python version documented.
* [ ] Dependency versions documented.
* [ ] PyTorch version documented.
* [ ] Transformers version documented.
* [ ] Quantization dependencies documented.
* [ ] Kaggle environment documented.
* [ ] Model revisions pinned.
* [ ] Tokenizer revisions pinned.
* [ ] Generation configs frozen.
* [ ] Normalizer version frozen.
* [ ] Evaluator version frozen.

---

# LXXVI. Checklist — Data Package

* [ ] Clean benchmark version.
* [ ] Clean checksum.
* [ ] Attack benchmark version.
* [ ] Attack checksum.
* [ ] Benign checksum.
* [ ] Robustness checksum.
* [ ] Data schemas.
* [ ] Split manifests.
* [ ] Variant mappings.
* [ ] Attack/benign pair mappings.
* [ ] Synthetic-data statement.
* [ ] Data card.
* [ ] No accidental Test mutation.

---

# LXXVII. Checklist — Configuration Package

* [ ] A0.
* [ ] A1.
* [ ] A2.
* [ ] A3.
* [ ] A4.
* [ ] A5.
* [ ] A6.
* [ ] Config hashes.
* [ ] Rule version.
* [ ] Guard prompt version.
* [ ] Guard model revision.
* [ ] Sensitivity policy.
* [ ] Trust policy.
* [ ] Provenance policy.
* [ ] Experiment manifests.

---

# LXXVIII. Checklist — Results Package

* [ ] E1 task scores.
* [ ] E1 aggregate.
* [ ] E2 task scores.
* [ ] E2 aggregate.
* [ ] E3 pair scores.
* [ ] Statistics.
* [ ] Confidence intervals.
* [ ] Human annotations.
* [ ] Agreement report.
* [ ] Error-analysis file.
* [ ] Final tables.
* [ ] Final figures.
* [ ] Result manifest.
* [ ] Deviations.

---

# LXXIX. Checklist — Thesis Introduction

* [ ] Problem motivation.
* [ ] Tool-using agent context.
* [ ] Vietnamese context.
* [ ] Security problem.
* [ ] Research gap.
* [ ] Objectives.
* [ ] RQ1.
* [ ] RQ2.
* [ ] RQ3.
* [ ] Scope.
* [ ] Contributions.
* [ ] Thesis organization.

---

# LXXX. Checklist — Related Work

* [ ] LLM agents.
* [ ] ReAct.
* [ ] Tool use.
* [ ] Prompt injection.
* [ ] Indirect prompt injection.
* [ ] Tool-output attacks.
* [ ] Data exfiltration.
* [ ] Guardrails.
* [ ] Information-flow concepts.
* [ ] Provenance.
* [ ] Agent evaluation.
* [ ] Vietnamese NLP robustness.
* [ ] Clear distinction from prior work.
* [ ] Sources properly cited.

---

# LXXXI. Checklist — Methodology

* [ ] System context.
* [ ] 8 mock tools.
* [ ] Agent runtime.
* [ ] JSON protocol.
* [ ] Threat model.
* [ ] Sensitivity.
* [ ] Trust.
* [ ] Artifact model.
* [ ] Provenance.
* [ ] A0–A6 matrix.
* [ ] PreGate.
* [ ] PostGate.
* [ ] FinalGate.
* [ ] Clean dataset.
* [ ] Attack dataset.
* [ ] Benign controls.
* [ ] Robustness dataset.
* [ ] Dev/Test methodology.
* [ ] Metrics.
* [ ] Statistics.
* [ ] Human validation.
* [ ] Reproducibility.

---

# LXXXII. Checklist — Results RQ1

* [ ] 3 model backbone table.
* [ ] TSR.
* [ ] ToolSelAcc.
* [ ] ArgAcc.
* [ ] SeqAcc.
* [ ] ErrRecovery.
* [ ] CI.
* [ ] Category breakdown.
* [ ] Error analysis.
* [ ] Direct RQ1 answer.
* [ ] No unsupported generalization.

---

# LXXXIII. Checklist — Results RQ2

* [ ] A0–A6 table.
* [ ] TSR.
* [ ] ASR.
* [ ] FPR.
* [ ] PVR proposed.
* [ ] PVR executed.
* [ ] STSR.
* [ ] Confidence intervals.
* [ ] Paired comparisons.
* [ ] Attack-type breakdown.
* [ ] Sink breakdown.
* [ ] Final leakage.
* [ ] A5-vs-A6 analysis.
* [ ] Security–utility trade-off.
* [ ] Direct RQ2 answer.

---

# LXXXIV. Checklist — Results RQ3

* [ ] Canonical comparison.
* [ ] No-diacritic.
* [ ] Word-boundary.
* [ ] Code-mixing.
* [ ] Zero-width.
* [ ] Paraphrase.
* [ ] Capability degradation.
* [ ] Security degradation.
* [ ] Paired statistics.
* [ ] Transition analysis.
* [ ] A0/A6 comparison if planned.
* [ ] Direct RQ3 answer.

---

# LXXXV. Checklist — Discussion

* [ ] Explain capability findings.
* [ ] Explain security findings.
* [ ] Explain robustness findings.
* [ ] Discuss A1–A6 progression.
* [ ] Discuss A5/A6 difference.
* [ ] Discuss security–utility trade-off.
* [ ] Discuss attack failure cases.
* [ ] Discuss benign overblocking.
* [ ] Discuss normalization limitations.
* [ ] Discuss provenance limitations.
* [ ] Avoid claiming mechanisms unsupported by traces.

---

# LXXXVI. Checklist — Limitations

* [ ] Synthetic setting.
* [ ] University domain.
* [ ] Single agent.
* [ ] 8 tools.
* [ ] No Internet.
* [ ] Mock external sinks.
* [ ] Finite models.
* [ ] Finite attacks.
* [ ] Finite Vietnamese variants.
* [ ] Conservative provenance.
* [ ] Human annotation limitations.
* [ ] External-validity limitations.

---

# LXXXVII. Checklist — Conclusion

* [ ] Restate problem briefly.
* [ ] Direct answer RQ1.
* [ ] Direct answer RQ2.
* [ ] Direct answer RQ3.
* [ ] Contributions.
* [ ] Main quantitative findings.
* [ ] Limitations acknowledged.
* [ ] Future work bounded.
* [ ] No new evidence introduced.

---

# LXXXVIII. Checklist — Figures/Tables

* [ ] Every table scripted.
* [ ] Every figure scripted.
* [ ] Source CSV frozen.
* [ ] Captions self-contained.
* [ ] Axis labels clear.
* [ ] Metric direction indicated.
* [ ] Sample size clear.
* [ ] CI shown where needed.
* [ ] Rounding consistent.
* [ ] No manual value edits.
* [ ] Figure/table numbering consistent.
* [ ] All referenced in prose.

---

# LXXXIX. Checklist — Number Audit

* [ ] Every RQ1 number verified.
* [ ] Every RQ2 number verified.
* [ ] Every RQ3 number verified.
* [ ] Abstract numbers verified.
* [ ] Conclusion numbers verified.
* [ ] Discussion numbers verified.
* [ ] Percentage vs percentage-point wording verified.
* [ ] CIs copied correctly.
* [ ] p-values copied correctly.
* [ ] Denominators correct.
* [ ] Huy cross-checks Minh numbers.
* [ ] Minh cross-checks Huy numbers.

---

# XC. Checklist — Demo

* [ ] Demo uses Dev/demo cases.
* [ ] Clean case.
* [ ] Attack case.
* [ ] Benign external-action case.
* [ ] Final-leak case.
* [ ] A0 vs A6 demonstrable.
* [ ] No real email.
* [ ] No real webhook.
* [ ] No Internet dependency.
* [ ] Demo reset state between cases.
* [ ] Demo can run without modifying frozen system.

---

# XCI. Checklist — Cross-machine Reproduction

* [ ] Fresh clone on Mac.
* [ ] Fresh clone on Windows.
* [ ] Clean Python environment.
* [ ] Installation succeeds.
* [ ] Unit tests pass.
* [ ] Smoke test passes.
* [ ] Replay passes.
* [ ] Evaluation replay passes.
* [ ] Tables regenerate.
* [ ] Figures regenerate.
* [ ] No user-specific paths.
* [ ] Findings documented.

---

# XCII. Definition of Done — Phase 8

## DoD-1 — Final evidence frozen

Có một duy nhất:

$$
ResultsRelease=v1.
$$

Không còn ambiguity về file nào là final.

---

## DoD-2 — RQ completeness

Ba RQ đều có:

$$
RQ
\rightarrow
Metrics
\rightarrow
Evidence
\rightarrow
Statistics
\rightarrow
Answer.
$$

Không RQ nào chỉ được bàn luận định tính.

---

## DoD-3 — Evidence traceability

Mọi primary quantitative claim:

$$
Claim
\rightarrow
Table
\rightarrow
CSV
\rightarrow
TaskScore
\rightarrow
Trace.
$$

---

## DoD-4 — Fresh-clone reproducibility

Một fresh clone có thể chạy:

$$
Install
\rightarrow
Smoke
\rightarrow
EvaluationReplay.
$$

Không cần hidden local files.

---

## DoD-5 — Table reproducibility

Từ frozen task scores:

$$
reproduce\_tables
$$

sinh đúng final tables.

---

## DoD-6 — Figure reproducibility

Từ frozen CSV:

$$
reproduce\_figures
$$

sinh đúng final figures.

---

## DoD-7 — Config/data verification

`verify_release.py` xác minh được:

$$
DataHashes
+
ConfigHashes
+
ResultManifest.
$$

---

## DoD-8 — Thesis draft complete

Không còn chương chính nào ở trạng thái:

```text
TODO
TBD
placeholder.
```

Bản draft phải hoàn chỉnh từ Abstract đến Conclusion.

---

## DoD-9 — Numerical consistency

Mọi con số primary trong văn bản và tables đã được cross-check bởi người còn lại.

---

## DoD-10 — Claims bounded by evidence

Không có:

* “always secure”;
* “completely prevents”;
* “proves universal robustness”;

nếu benchmark không hỗ trợ.

---

## DoD-11 — Limitations explicit

Có section limitations/threats-to-validity thực chất, không phải một đoạn hình thức.

---

## DoD-12 — A6 contribution clear

Reader phải hiểu rõ:

$$
A5=coarse\ session\ state
$$

khác:

$$
A6=fine\ artifact/provenance\ control.
$$

---

## DoD-13 — Repository release ready

README, configs, data manifests, scripts, tests và docs không phụ thuộc kiến thức riêng của hai thành viên.

---

## DoD-14 — No Test contamination

Không có system/policy/evaluator semantic modification trong Phase 8 dựa trên final Test performance.

---

## DoD-15 — Buffer handoff ready

Mọi lỗi còn lại được chuyển thành issue rõ ràng cho tuần 23–24:

```text
technical bug
missing rerun
formatting
citation
report revision
demo issue
```

chứ không tiếp tục xử lý vô cấu trúc.

---

# XCIII. Output cuối Phase 8

Khi hoàn thành, tôi muốn có tối thiểu:

```text
releases/
└── reproducibility-v1/
    ├── RELEASE_MANIFEST.json
    ├── CHECKSUMS.sha256
    ├── environment_manifest.json
    ├── models_manifest.json
    ├── datasets_manifest.json
    ├── configs_manifest.json
    └── results_manifest.json
```

Cùng:

```text
results/final_release/
├── E1/
├── E2/
├── E3/
├── task_scores/
├── statistics/
├── human_validation/
├── error_analysis/
├── tables/
└── figures/
```

Documentation:

```text
docs/
├── claim_evidence_matrix.md
├── rq_answers.md
├── reproducibility/
│   ├── reproduction_guide.md
│   └── release_integrity_report.md
│
├── benchmark/
│   └── data_card.md
│
└── system/
    └── system_card.md
```

Và:

```text
thesis/
├── draft/
├── figures/
├── tables/
└── references/
```

---

# XCIV. Khi Phase 8 kết thúc, trạng thái đồ án phải như thế nào?

Lúc này project không còn là:

> “một hệ thống nhóm đang code.”

Mà phải trở thành:

$$
\boxed{
\text{một research artifact hoàn chỉnh}
}
$$

với năm lớp có thể audit:

$$
\boxed{Code}
$$

$$
\boxed{Data}
$$

$$
\boxed{Configurations}
$$

$$
\boxed{Evidence}
$$

$$
\boxed{Written\ Conclusions}
$$

và quan hệ:

$$
Code/Data/Config
\rightarrow
Runs
\rightarrow
TaskScores
\rightarrow
Statistics
\rightarrow
Claims.
$$

Đây cũng chính là sản phẩm mà bản kế hoạch chính thức hướng tới: cuối tuần 21–22 phải có **bản thảo báo cáo/luận văn**, còn mã nguồn, cấu hình, dữ liệu và execution traces phải được versioning để thí nghiệm có thể chạy lại. Sang tuần 23–24 mới sử dụng buffer để sửa lỗi còn lại, rerun phần thực sự cần thiết và hoàn thiện bản cuối. 

**Một nguyên tắc tôi khuyên khóa cho Phase 8 là:**

$$
\boxed{
\text{Không có con số nào trong luận văn mà hai người không biết nó được sinh từ file nào.}
}
$$

Nếu đạt được điều đó cùng với fresh-clone reproduction và three-level reproduction package ở trên, phần reproducibility của đồ án sẽ tương đối vững.
