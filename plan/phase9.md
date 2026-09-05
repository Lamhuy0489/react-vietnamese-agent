# Phase 9 — Buffer, Controlled Reruns, Final Verification & Defense Readiness

**Tuần 23–24 — Phase đóng dự án**

Theo kế hoạch đã chốt, tuần 23–24 không phải để mở rộng đề tài mà là **buffer** cho sửa lỗi kỹ thuật còn lại, rerun những thí nghiệm thực sự bị invalid, hoàn thiện bảng/kết quả/báo cáo và chuẩn bị bản nộp cuối. Huy tập trung lỗi kỹ thuật, source, rerun; Minh tập trung dữ liệu, bảng kết quả và báo cáo; cả hai cùng kiểm tra lần cuối và hoàn thiện sản phẩm. 

Điểm quan trọng nhất:

$$
\boxed{
Phase\ 9 \neq Feature\ Development
}
$$

Mà là:

$$
\boxed{
Audit
\rightarrow
Repair
\rightarrow
Controlled\ Rerun
\rightarrow
Final\ Freeze
\rightarrow
Submission
}
$$

Nếu đến tuần 23 mà nhóm vẫn đang thiết kế A7, thêm tool thứ 9 hoặc thay đổi benchmark thì kế hoạch đã lệch.

---

## I. Mục tiêu của Phase 9

Phase này phải đóng được 6 việc:

1. Xác định toàn bộ vấn đề còn lại.
2. Phân loại vấn đề nào được phép sửa.
3. Rerun đúng những experiment bị invalid.
4. Xác minh lại toàn bộ results/reproducibility.
5. Đóng bản luận văn và repository.
6. Chuẩn bị bảo vệ/demo.

Kết thúc Phase 9 phải đạt:

$$
\boxed{
Research\ Frozen
+
Results\ Verified
+
Thesis\ Final
+
Repository\ Release
+
Defense\ Ready
}
$$

---

# II. Nguyên tắc số 1 — Không được dùng Buffer để làm feature creep

Không thêm:

* A7;
* multi-agent;
* Internet thật;
* email thật;
* webhook thật;
* vector database mới;
* RAG framework mới;
* fine-tuning;
* attack taxonomy lớn mới;
* model thứ 4 chỉ vì còn quota;
* thêm hàng trăm tasks;
* dashboard/web UI phức tạp.

Các việc trên không còn phục vụ RQ1–RQ3 đã khóa.

Rule:

$$
\boxed{
No\ New\ Scientific\ Degrees\ of\ Freedom
}
$$

sau Phase 8.

---

# III. Phân loại issue trước khi sửa

Mỗi issue phải được đưa vào một trong 5 loại.

### C1 — Presentation only

Ví dụ:

* typo;
* caption;
* lỗi bảng;
* numbering;
* format citation.

Được sửa trực tiếp.

---

### C2 — Reproducibility/packaging

Ví dụ:

* README thiếu command;
* hard-coded path;
* missing dependency;
* script reproduce figure lỗi.

Được sửa nếu không làm thay đổi experimental semantics.

---

### C3 — Analysis/reporting bug

Ví dụ:

* sai label trục;
* bảng đọc nhầm CSV;
* percentage formatting sai;
* CI hiển thị sai nhưng task scores đúng.

Được sửa và regenerate outputs.

---

### C4 — Experimental infrastructure bug

Ví dụ:

* một shard thiếu 12 tasks;
* resume ghi duplicate;
* run dùng sai config hash;
* trace corrupted;
* model revision thay giữa shard.

Phải rerun affected condition.

---

### C5 — Scientific/semantic bug

Ví dụ:

* evaluator định nghĩa sai ASR;
* Test ground truth sai;
* A6 policy vô tình đọc attack label;
* benchmark leakage nghiêm trọng.

Đây là loại nghiêm trọng nhất.

Không silently sửa.

Phải:

1. ghi deviation;
2. xác định impact;
3. bump version;
4. rerun affected experiments;
5. cập nhật thesis.

---

# IV. Issue Register

Tạo:

```text
docs/finalization/issues.csv
```

Fields:

```text
issue_id
category
severity
description
affected_component
affected_experiment
semantic_change
owner
status
resolution
rerun_required
```

Ví dụ:

```text
ISSUE-017
C4
HIGH
A4 attack shard thiếu 8 trajectories
E2-A4
false
Huy
OPEN
rerun missing tasks
true
```

Không quản lý lỗi bằng chat/messages rời rạc.

---

# V. Severity

Dùng 4 mức:

```text
BLOCKER
HIGH
MEDIUM
LOW
```

### BLOCKER

Không thể nộp / conclusions invalid.

### HIGH

Ảnh hưởng metric/result/reproducibility.

### MEDIUM

Ảnh hưởng documentation hoặc secondary result.

### LOW

Cosmetic.

Thứ tự xử lý:

$$
BLOCKER
\rightarrow
HIGH
\rightarrow
MEDIUM
\rightarrow
LOW.
$$

---

# VI. Rerun policy

Không phải cứ có bug là rerun mọi thứ.

Rerun phải theo **affected experimental condition**.

Ví dụ:

```text
A4 config file sai trong E2
```

thì rerun:

$$
E2,A4
$$

không rerun:

$$
A0,A1,A2,A3,A5,A6.
$$

---

# VII. Khi nào phải rerun toàn condition?

Nếu bất kỳ yếu tố sau thay đổi:

$$
ModelRevision
$$

$$
SecurityConfig
$$

$$
AgentPrompt
$$

$$
ToolBehavior
$$

$$
DatasetSemantics
$$

$$
GenerationConfig.
$$

Thì tất cả tasks trong condition đó phải cùng configuration.

Không được:

```text
task 1–60 config v1
task 61–100 config v2
```

rồi gộp.

---

# VIII. Khi nào chỉ rerun missing tasks?

Nếu lỗi hoàn toàn infrastructure:

* kernel chết;
* output file chưa flush;
* Kaggle interruption;

nhưng:

$$
ConfigHash_{before}=ConfigHash_{after}
$$

và mọi semantic input giống hệt.

Khi đó có thể resume chỉ missing tasks.

---

# IX. Rerun manifest

Mỗi rerun:

```text
experiments/reruns/RERUN-001.json
```

Ví dụ:

```json
{
  "rerun_id": "RERUN-001",
  "experiment": "E2",
  "condition": "A4",
  "reason": "missing tasks after infrastructure interruption",
  "semantic_change": false,
  "old_config_hash": "...",
  "new_config_hash": "...",
  "task_ids": ["..."],
  "approved": true
}
```

---

# X. Không cherry-pick rerun result

Nếu rerun vì infrastructure invalid:

chỉ invalid trajectory được thay.

Không:

> “Lần mới đẹp hơn nên lấy lần mới.”

Trajectories hợp lệ cũ vẫn là primary result.

---

# XI. Final experiment audit

Sau mọi rerun, chạy:

```text
scripts/audit_final_experiments.py
```

Check:

$$
ObservedN=ExpectedN.
$$

Ví dụ:

### E1

$$
3\times100=300.
$$

### E2

$$
7\times400=2800.
$$

### E3

pair completeness đúng.

---

# XII. Audit phải kiểm gì?

* task counts;
* duplicates;
* missing tasks;
* config hashes;
* dataset hashes;
* model revisions;
* evaluator version;
* task-score completeness;
* pair integrity;
* invalid traces;
* rerun provenance.

---

# XIII. Final Result Regeneration

Sau khi reruns hoàn thành:

Không chỉnh bảng cũ.

Phải regenerate toàn bộ:

```text
TaskScores
↓
Aggregate
↓
Statistics
↓
Tables
↓
Figures
```

Tức:

```bash
python scripts/reproduce_tables.py
python scripts/reproduce_figures.py
```

Sau đó replace result release:

```text
results-v1.0
```

bằng version mới nếu semantics thay đổi:

```text
results-v1.1
```

Không overwrite silently.

---

# XIV. Statistical revalidation

Nếu dữ liệu thay đổi do rerun:

phải chạy lại:

* Wilson CI;
* McNemar;
* bootstrap;
* Holm correction;
* effect size.

Không chỉ sửa point estimate.

---

# XV. Human validation có cần rerun không?

Chỉ khi affected trajectories nằm trong human sample hoặc evaluator semantics thay đổi.

Nếu model runs thay đổi nhưng sample không liên quan:

không nhất thiết re-annotate.

Nếu evaluator rubric thay đổi:

có thể cần reconsider toàn human-validation analysis.

---

# XVI. Final claim audit

Sau mọi rerun, claim–evidence matrix từ Phase 8 phải được kiểm lại.

Mỗi claim:

```text
C1
C2
C3
...
```

status:

```text
VALID
UPDATED
INVALIDATED
```

Không để thesis giữ conclusion từ results cũ.

---

# XVII. Một quy tắc mạnh cho conclusions

Mỗi kết luận phải thuộc một trong ba dạng:

### Supported

Evidence rõ.

### Inconclusive

CI/test/effect chưa đủ.

### Unsupported

Không được đưa vào conclusion.

Không dùng:

```text
"có xu hướng rõ ràng"
```

để che kết quả không hỗ trợ.

---

# XVIII. Phase 9 — Workstream A: Technical Closeout

Huy ownership chính.

Kiểm:

```text
runtime
security
experiments
Git
Kaggle reruns
release
```

Tasks:

* fix reproducibility blockers;
* validate config hashes;
* rerun invalid shards;
* verify A0–A6 source;
* validate final security traces;
* verify no real side effects.

---

# XIX. Workstream B: Data/Result Closeout

Minh ownership chính.

Tasks:

* dataset count/checksum audit;
* pair integrity;
* result aggregation;
* statistical regeneration;
* final tables;
* final figures;
* thesis number consistency.

---

# XX. Workstream C: Thesis Finalization

Cả hai.

Focus:

* remove inconsistencies;
* update final numbers;
* citations;
* terminology;
* figure/table refs;
* limitations;
* appendix;
* abstract;
* conclusion.

Không rewrite toàn luận văn từ đầu.

---

# XXI. Workstream D: Defense Preparation

Đây là phần Phase 8 chưa cần làm sâu nhưng Phase 9 nên làm.

Chuẩn bị:

1. slide deck;
2. demo;
3. Q&A bank;
4. technical fallback;
5. backup artifacts.

---

# XXII. Defense narrative

Buổi bảo vệ nên trả lời 5 câu rất rõ:

### 1. Vấn đề là gì?

Tool-using agents có thể bị dữ liệu/tool output điều khiển.

### 2. Tại sao tiếng Việt?

Robustness/security dưới Vietnamese surface variations chưa chắc ổn định.

### 3. Nhóm đã xây gì?

Benchmark + A0–A6 + evaluation.

### 4. Contribution chính?

A6 provenance-aware security architecture.

### 5. Evidence?

RQ1–RQ3 final experiments.

---

# XXIII. Slide structure đề xuất

Khoảng 12–16 slides là hợp lý.

```text
1. Title
2. Motivation
3. Research Questions
4. System & 8 Tools
5. Threat Model
6. Benchmark
7. A0–A6
8. A6 Architecture
9. Evaluation Protocol
10. RQ1 Results
11. RQ2 Results
12. RQ3 Results
13. Error Analysis
14. Limitations
15. Contributions
16. Conclusion/Demo
```

Không trình bày timeline 24 tuần trừ khi hội đồng hỏi.

---

# XXIV. Demo strategy

Demo phải deterministic tối đa.

Dùng:

```text
ReplayBackend
```

nếu live model inference có nguy cơ lỗi mạng/GPU.

Có thể có hai mode:

### Live

Kaggle/model nếu available.

### Fallback

Replay một trajectory thật đã lưu.

Cả hai đều hiển thị:

```text
Task
Tool
Observation
Security Decision
Final
```

---

# XXV. Không phụ thuộc Kaggle live trong buổi bảo vệ

Nếu buổi bảo vệ mất mạng hoặc Kaggle queue:

demo vẫn phải chạy.

Do đó:

$$
Demo_{fallback}=mandatory.
$$

---

# XXVI. Demo case 1 — Capability

Một clean multi-step:

```text
doc_search
→ doc_read
→ calculator
→ final.
```

Mục tiêu cho hội đồng thấy hệ thống thực sự dùng tools.

---

# XXVII. Demo case 2 — Security

Cùng một attack:

### A0

Poisoned source:

$$
\rightarrow
unsafe\ proposed/executed\ action.
$$

### A6

$$
PreGate
\rightarrow DENY.
$$

Đây là demo trực quan nhất.

---

# XXVIII. Demo case 3 — A5 vs A6

Nếu final results hỗ trợ:

* session có S2 data;
* benign external action chỉ chứa S0 data.

A5:

$$
block.
$$

A6:

$$
allow.
$$

Đây thể hiện contribution provenance tốt hơn nhiều so với demo “regex block injection”.

---

# XXIX. Demo case 4 — Final Gate

Model final chứa known sensitive value.

A6:

$$
REDACT/DENY.
$$

Điều này cho thấy security không chỉ bảo vệ tools.

---

# XXX. Q&A bank

Tạo:

```text
docs/defense/q_and_a.md
```

Chuẩn bị ít nhất các câu:

* Tại sao chọn ReAct?
* Tại sao không multi-agent?
* Tại sao 8 tools?
* Tại sao synthetic data?
* Vì sao A0–A6?
* A6 khác A5 ở đâu?
* Provenance có thực sự causal không?
* Vì sao LLM guard không đủ?
* Tại sao Test chỉ 100 clean tasks?
* Vì sao 70 attack families?
* Tại sao split family-level?
* Tại sao no real email/webhook?
* Tại sao không fine-tune?
* Tại sao chọn các model đó?
* Vì sao deterministic decoding?
* FPR được định nghĩa ra sao?
* STSR có ý nghĩa gì?
* Vì sao không dùng LLM judge?
* Kết quả có generalize ngoài university domain không?
* Limitation lớn nhất là gì?

---

# XXXI. Câu khó nhất: “A6 có thực sự biết data model sử dụng không?”

Câu trả lời phải chính xác:

Không.

A6 không theo dõi causal influence trong neural network.

Nó theo dõi:

* observable artifacts;
* exposure lineage;
* deterministic value-origin matches;
* system-level provenance.

Do đó:

$$
A6
$$

là provenance-aware ở **agent execution layer**, không phải neural causal provenance.

Đây phải nhất quán với thesis.

---

# XXXII. Câu hỏi: “Tại sao không chỉ dùng regex?”

Trả lời dựa RQ2 results.

Conceptually:

A1 kiểm lexical patterns.

Nhưng linguistic variation/paraphrase/tool-flow attacks có thể vượt qua lexical rules.

A2–A6 bổ sung semantic/data-flow controls.

Không khẳng định điều này nếu final result không chứng minh.

---

# XXXIII. Câu hỏi: “Nếu A6 block everything thì sao?”

Trả lời bằng:

$$
FPR
$$

$$
TSR
$$

$$
STSR.
$$

Đó chính là lý do benchmark có benign controls và clean test.

---

# XXXIV. Appendices nên chứa gì?

Không nhét tất cả vào body thesis.

Appendix có thể chứa:

* full A0–A6 matrix;
* tool schemas;
* task schema;
* attack taxonomy;
* additional tables;
* metric formulas;
* human rubric;
* reproducibility manifest;
* representative traces.

---

# XXXV. Không đưa raw 350 attacks vào thesis

Repository/data package giữ toàn bộ.

Thesis chỉ cần:

* distribution;
* methodology;
* representative examples.

---

# XXXVI. Final repository cleanup

Branching cuối:

```text
main
```

phải chứa release state.

Không cần giữ hàng loạt branches chưa merge như:

```text
fix-final-v2
minh-test
huy-new-final
```

Có thể archive/delete sau merge nếu hợp lý.

---

# XXXVII. Final Git tags

Tôi khuyên ít nhất:

```text
data-clean-v1.0
data-adversarial-v1.0
security-architecture-v1
evaluation-v1.0
results-v1.0
reproducibility-v1.0
thesis-final-v1.0
```

Nếu có semantic rerun:

```text
results-v1.1.
```

---

# XXXVIII. Final commit discipline

Không:

```text
final final final
fix
done
```

Commit cuối vẫn rõ:

```text
fix(repro): remove hard-coded data path
results: regenerate E2 tables after valid A4 rerun
docs: update RQ2 results and limitations
release: prepare reproducibility v1.0
```

---

# XXXIX. Kaggle closeout

Đối với Kaggle:

* preserve final kernels/notebooks;
* preserve model configs;
* preserve output run directories;
* record versions;
* download final output locally;
* verify checksum.

Không để final evidence chỉ tồn tại trong temporary Kaggle session.

---

# XL. Local archive

Tạo release archive:

```text
release/
├── source_manifest
├── data_manifests
├── configs
├── results
├── tables
├── figures
├── thesis
└── checksums
```

Không nhất thiết commit raw huge traces nếu repo size không phù hợp, nhưng manifest phải chỉ nơi lưu.

---

# XLI. Backup policy

Ít nhất:

$$
3
$$

logical copies:

1. GitHub source.
2. Local machine/archive.
3. Kaggle/backup storage cho experiment outputs.

Không chỉ một laptop.

---

# XLII. Submission package

Chuẩn bị riêng:

```text
submission/
├── thesis.pdf
├── source_code_reference.txt
├── demo/
├── presentation.pdf
├── README_submission.md
└── checksums.txt
```

Tùy yêu cầu trường có thể khác, nhưng nên có internal package chuẩn.

---

# XLIII. Final thesis audit

Kiểm từng chapter:

### Introduction

RQs giống exact wording đã chốt?

### Methodology

Dataset counts đúng?

### A0–A6

Matrix đúng implementation?

### Experiments

N đúng?

### Results

Số lấy final release?

### Discussion

Không overclaim?

### Limitations

Đầy đủ?

### Conclusion

Không đưa evidence mới?

---

# XLIV. Terminology consistency

Phải khóa terminology.

Ví dụ chọn một cách:

```text
attack success rate (ASR)
```

không lúc thì:

```text
attack rate
successful attack ratio
security failure rate
```

tùy đoạn.

Tương tự:

```text
benign control
```

không lúc gọi:

```text
normal pair
clean attack
safe sample.
```

---

# XLV. A0–A6 naming consistency

Không để:

```text
A4 = taint
```

ở chapter 4 nhưng:

```text
A4 = sensitivity+trust
```

ở chapter 6.

Matrix từ Phase 5 là single source of truth.

---

# XLVI. Dataset count audit

Một table internal nên xác nhận:

| Dataset    |                Canonical | Variants | Dev |           Test |
| ---------- | -----------------------: | -------: | --: | -------------: |
| Clean      |                      250 |        — | 150 |            100 |
| Attack     |                       70 |      350 | 200 |            150 |
| Benign     | 70 if canonical retained |      350 | 200 |            150 |
| Robustness |             50 canonical |      250 |   — | final held-out |

Không để thesis nhầm:

$$
70+350=350.
$$

Canonical attack 70 được lưu riêng.

---

# XLVII. Final mathematical audit

Kiểm:

$$
40+40+50+40+25+30+25=250.
$$

$$
70\times5=350.
$$

$$
40\times5=200.
$$

$$
30\times5=150.
$$

$$
50\times5=250.
$$

$$
50+250=300.
$$

$$
7\times400=2800.
$$

Nếu thesis có số khác, sửa.

---

# XLVIII. Week 23 — Technical closure

## Day 1

Issue triage:

```text
BLOCKER/HIGH/MEDIUM/LOW.
```

Freeze scope.

---

## Day 2

Huy:

* technical blockers;
* rerun manifests.

Minh:

* data/result consistency.

---

## Day 3–4

Controlled reruns.

Only affected conditions.

---

## Day 5

Regenerate:

```text
scores
statistics
tables
figures.
```

---

## Day 6

Reproducibility fresh clone.

---

## Day 7

Final evidence audit.

Target:

$$
0\ BLOCKER.
$$

---

# XLIX. Week 24 — Submission & defense closure

## Day 1

Final thesis number audit.

---

## Day 2

Final editorial pass.

---

## Day 3

Slides.

---

## Day 4

Demo + fallback.

---

## Day 5

Mock defense.

Một người trình bày, một người đóng vai hội đồng.

---

## Day 6

Fix only presentation/documentation issues.

Không sửa scientific system.

---

## Day 7

Final release:

```text
thesis-final-v1.0
submission-v1.0
```

---

# L. Mock defense protocol

Lần 1:

Huy trình bày.

Minh hỏi khó.

Lần 2:

Minh trình bày methodology/data.

Huy hỏi.

Sau đó ghi:

```text
questions_not_answered.md
```

và bổ sung.

---

# LI. Presentation timing

Nếu trường chưa quy định exact time, khi luyện nên chuẩn bị:

* full version;
* shortened version.

Không cần xây slide mới, chỉ mark:

```text
core
optional
```

slides.

---

# LII. Defense backup package

Mang ít nhất:

```text
slides PDF
thesis PDF
demo replay
final tables
architecture image
results CSV
```

offline.

Không phụ thuộc web.

---

# LIII. Checklist Phase 9 — Inputs

* [ ] Phase 8 complete.
* [ ] Thesis draft complete.
* [ ] Results release exists.
* [ ] Claim-evidence matrix exists.
* [ ] Reproducibility package exists.
* [ ] All known issues collected.
* [ ] No feature requests accepted without scope review.

---

# LIV. Checklist — Scope Freeze

* [ ] No A7.
* [ ] No new tools.
* [ ] No new dataset category.
* [ ] No new model unless existing experiment invalid.
* [ ] No new attack family.
* [ ] No real Internet.
* [ ] No fine-tuning.
* [ ] No UI rewrite.
* [ ] Buffer reserved for validation/finalization.

---

# LV. Checklist — Issue Management

* [ ] Every issue has ID.
* [ ] Every issue categorized.
* [ ] Severity assigned.
* [ ] Owner assigned.
* [ ] Semantic impact determined.
* [ ] Rerun requirement determined.
* [ ] Resolution documented.
* [ ] No BLOCKER unresolved before final release.

---

# LVI. Checklist — Controlled Reruns

* [ ] Rerun reason documented.
* [ ] Affected condition identified.
* [ ] Config hash verified.
* [ ] Dataset hash verified.
* [ ] Model revision verified.
* [ ] Task list specified.
* [ ] No cherry-picking.
* [ ] Original output preserved.
* [ ] Rerun output separately versioned.
* [ ] Final manifest updated.

---

# LVII. Checklist — Result Revalidation

* [ ] Expected task counts.
* [ ] No duplicate task IDs.
* [ ] No missing valid tasks.
* [ ] Trace validation pass.
* [ ] Statistics regenerated.
* [ ] CI regenerated.
* [ ] Tables regenerated.
* [ ] Figures regenerated.
* [ ] Claim-evidence matrix updated.
* [ ] Thesis numbers updated.

---

# LVIII. Checklist — Reproducibility

* [ ] Fresh Mac clone.
* [ ] Fresh Windows clone.
* [ ] Installation passes.
* [ ] Unit tests pass.
* [ ] Smoke test passes.
* [ ] Replay passes.
* [ ] Evaluation reproduction passes.
* [ ] Table reproduction passes.
* [ ] Figure reproduction passes.
* [ ] Release verification passes.
* [ ] No hidden local dependencies.

---

# LIX. Checklist — Thesis

* [ ] Abstract final.
* [ ] Introduction final.
* [ ] Related work final.
* [ ] Methodology final.
* [ ] Architecture final.
* [ ] Evaluation final.
* [ ] RQ1 results final.
* [ ] RQ2 results final.
* [ ] RQ3 results final.
* [ ] Error analysis final.
* [ ] Discussion final.
* [ ] Limitations final.
* [ ] Conclusion final.
* [ ] References final.
* [ ] Appendices final.

---

# LX. Checklist — Scientific Integrity

* [ ] No Test-driven defense changes.
* [ ] No Test-driven prompt changes.
* [ ] No removal of inconvenient results.
* [ ] No cherry-picked reruns.
* [ ] Negative findings retained.
* [ ] Null results retained.
* [ ] Limitations explicit.
* [ ] Provenance claims bounded.
* [ ] No hidden CoT published/used.
* [ ] All external actions remain mock.

---

# LXI. Checklist — Defense

* [ ] Slide deck.
* [ ] Architecture slide.
* [ ] Dataset slide.
* [ ] A0–A6 matrix.
* [ ] RQ1 results.
* [ ] RQ2 results.
* [ ] RQ3 results.
* [ ] Limitations.
* [ ] Contribution slide.
* [ ] Demo.
* [ ] Offline replay demo.
* [ ] Q&A bank.
* [ ] Mock defense 1.
* [ ] Mock defense 2.

---

# LXII. Checklist — Submission

* [ ] Thesis PDF.
* [ ] Final source/repository.
* [ ] README.
* [ ] Final release tag.
* [ ] Results manifest.
* [ ] Checksums.
* [ ] Slides PDF.
* [ ] Demo artifacts.
* [ ] Backup archive.
* [ ] Submission requirements checked.
* [ ] Final package opens correctly on another machine.

---

# LXIII. Definition of Done — Phase 9 / Toàn đồ án

Phase 9 chỉ hoàn thành khi các điều kiện sau đều đạt.

### DoD-1 — Zero blockers

$$
N_{BLOCKER}=0.
$$

---

### DoD-2 — Experimental completeness

$$
ObservedN=ExpectedN
$$

cho toàn bộ final experimental conditions.

---

### DoD-3 — No invalid mixture

Không condition nào trộn nhiều:

* configs;
* model revisions;
* dataset revisions;
* evaluator versions.

---

### DoD-4 — Final results reproducible

$$
TaskScores
\rightarrow
Tables/Figures
$$

reproduce được.

---

### DoD-5 — RQ1–RQ3 finalized

Mỗi RQ có direct answer dựa trên final evidence.

---

### DoD-6 — Thesis internally consistent

Không có mâu thuẫn về:

* dataset counts;
* A0–A6 definitions;
* experiment size;
* metric values.

---

### DoD-7 — Fresh-clone success

Hai máy local đều có thể ít nhất:

$$
clone
\rightarrow
install
\rightarrow
smoke
\rightarrow
evaluate.
$$

---

### DoD-8 — Release integrity

```text
verify_release.py
```

trả:

```text
PASS.
```

---

### DoD-9 — Defense readiness

Có thể trình bày toàn research story từ:

$$
Problem
$$

đến:

$$
Evidence
$$

trong một mạch logic.

---

### DoD-10 — Demo resilience

Nếu không có Internet/GPU:

demo vẫn chạy bằng Replay.

---

### DoD-11 — No real side effects

Toàn bộ project cuối vẫn bảo đảm:

$$
send\_email\_mock\not\rightarrow SMTP
$$

và:

$$
post\_webhook\_mock\not\rightarrow HTTP.
$$

---

### DoD-12 — Final version tags exist

Có version cuối cho:

* source;
* datasets;
* security configs;
* evaluator;
* results;
* thesis/release.

---

# LXIV. Output cuối cùng của toàn bộ đồ án

Sau Phase 9, nhóm nên có 6 artifact groups.

### 1. Code

```text
src/
tests/
scripts/
configs/
```

### 2. Benchmark

```text
clean
attack
benign
robustness
```

### 3. Experimental evidence

```text
traces
task_scores
statistics
```

### 4. Research outputs

```text
tables
figures
error analysis
```

### 5. Documentation

```text
README
data card
system card
reproducibility guide
```

### 6. Submission

```text
thesis
slides
demo
release manifest
```

---

# LXV. Toàn bộ roadmap lúc này

Như vậy kế hoạch 24 tuần của nhóm trở thành:

| Phase                | Tuần       | Kết quả chính                                                   |
| -------------------- | ---------- | --------------------------------------------------------------- |
| Phase 0              | W1         | Research specification                                          |
| Phase 1              | W2         | A0 + 8 tools + runtime                                          |
| Phase 2              | W3–5       | 250 clean tasks                                                 |
| Phase 3              | W6–8       | Attack + benign benchmark                                       |
| Phase 4              | W9–10      | Normalization + artifacts + provenance foundation               |
| Phase 5              | W11–14     | A1–A6                                                           |
| Phase 6              | W15–16     | Evaluator + metrics                                             |
| Phase 7              | W17–20     | Final experiments                                               |
| Phase 8              | W21–22     | Reproducibility + thesis                                        |
| **Phase 9 / Buffer** | **W23–24** | **Controlled reruns + final verification + submission/defense** |

Đây là điểm kết thúc hợp lý của roadmap hiện tại. Sau Phase 9 không nên có thêm “Phase nghiên cứu” nào nữa; phần sau chỉ còn thủ tục nộp, bảo vệ và lưu trữ project.

Nếu khóa kế hoạch theo cấu trúc này, **W23–24 nên được bảo vệ khỏi feature creep**. Giá trị lớn nhất của hai tuần buffer không phải là làm thêm chức năng, mà là đảm bảo những kết quả đã có thực sự đúng, có thể tái tạo và có thể bảo vệ trước hội đồng. 
