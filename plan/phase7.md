# Phase 7 — Final Experiments, Statistical Analysis, Human Validation & Error Analysis

**Tuần 17–20**

Theo kế hoạch đã chốt, Phase 7 là giai đoạn chạy thí nghiệm về capability, security và robustness; Huy phụ trách chính RQ2, Minh phụ trách RQ1/RQ3, sau đó hai người cùng đối chiếu kết quả, lập bảng và kiểm tra các lần chạy. 

Đây là phase quan trọng thứ hai sau Phase 5. Nếu Phase 5 là nơi xây contribution kỹ thuật, thì Phase 7 là nơi chứng minh contribution đó bằng thực nghiệm.

---

# I. Mục tiêu của Phase 7

Tại thời điểm bắt đầu Phase 7, ta giả định những thứ sau đã frozen:

$$
\boxed{
Dataset
}
$$

$$
\boxed{
Model\ revisions
}
$$

$$
\boxed{
A0-A6
}
$$

$$
\boxed{
Prompts
}
$$

$$
\boxed{
Tool\ environment
}
$$

$$
\boxed{
Evaluator
}
$$

$$
\boxed{
Metrics
}
$$

$$
\boxed{
Statistical\ protocol
}
$$

Phase 7 không còn là:

> chạy → thấy không đẹp → sửa → chạy lại.

Mà phải là:

$$
\boxed{
Frozen\ Inputs
\rightarrow
Experiments
\rightarrow
Scores
\rightarrow
Statistics
\rightarrow
Analysis
}
$$

Đây là ranh giới phương pháp rất quan trọng.

---

# II. Ba experiment chính

Tôi khuyên khóa Phase 7 thành ba experiment:

$$
\boxed{E1:\ Backbone\ Capability}
$$

$$
\boxed{E2:\ Security\ Architecture}
$$

$$
\boxed{E3:\ Vietnamese\ Robustness}
$$

Mapping vào RQs:

| Experiment | Câu hỏi chính |
| ---------- | ------------- |
| E1         | RQ1           |
| E2         | RQ2           |
| E3         | RQ3           |

Như vậy cấu trúc luận văn sau này rất sạch.

---

# III. Experiment 1 — So sánh 3 LLM backbones

Mục tiêu:

> Với cùng baseline ReAct A0 và cùng clean Held-out Test, capability của các model khác nhau như thế nào?

Ta có:

$$
M=\{M_1,M_2,M_3\}.
$$

Security config cố định:

$$
A=A_0.
$$

Dataset:

$$
D=D_{\text{clean}}^{test}.
$$

Số task:

$$
N=100.
$$

Ma trận:

$$
3\ models\times100\ tasks
=
300\ trajectories.
$$

---

# IV. E1 phải giữ những gì cố định?

Giữa \(M_1,M_2,M_3\):

* cùng 100 tasks;
* cùng tools;
* cùng tool descriptions;
* cùng system prompt logic;
* cùng JSON schema;
* cùng max steps;
* cùng timeout;
* cùng evaluator;
* cùng A0;
* cùng environment;
* cùng data;
* cùng answer scoring.

Chỉ thay:

$$
LLMBackend.
$$

---

# V. Model configuration phải freeze

Trước khi E1 bắt đầu, mỗi model có manifest.

Ví dụ:

```yaml
model_id: model_1
source: huggingface
revision: <commit/revision>

tokenizer_revision: <revision>

quantization:
  enabled: true
  bits: 4

generation:
  do_sample: false
  temperature: 0
  max_new_tokens: 512

context_length: 8192
```

Không được sau 30 tasks đổi:

```text
max_new_tokens 512 → 1024
```

rồi tiếp tục cùng run.

Nếu phải thay:

$$
run\ invalid
$$

và phải rerun toàn experiment condition đó.

---

# VI. Tôi khuyên dùng deterministic decoding

Primary experiments:

```text
do_sample = false
```

và:

$$
temperature=0
$$

hoặc equivalent greedy decoding.

Lý do:

Experiment của bạn nghiên cứu:

$$
Model/Architecture/Variant
$$

không phải sampling variance.

Nếu dùng sampling:

$$
Y_{i,s}
$$

phụ thuộc seed \(s\), và workload tăng mạnh.

Với greedy decoding:

$$
\hat y_i
$$

gần deterministic hơn và experimental interpretation sạch hơn.

Seed vẫn phải log để reproducibility.

---

# VII. E1 metrics

Primary metrics:

$$
TSR
$$

$$
ToolSelAcc
$$

$$
ArgAcc
$$

$$
SeqAcc
$$

$$
ErrRecovery.
$$

Secondary:

$$
StepOverhead
$$

$$
JSONValidity
$$

$$
AverageToolCalls.
$$

---

# VIII. E1 breakdowns

Ngoài overall, report theo 7 clean categories:

```text
single_source
parameter_extraction
multi_step
db_document
ambiguous
error_recovery
no_tool
```

Ví dụ:

| Model | Overall TSR | Single | Param | Multi | DB+Doc | Ambig | Recovery | No-tool |
| ----- | ----------: | -----: | ----: | ----: | -----: | ----: | -------: | ------: |
| M1    |             |        |       |       |        |       |          |         |
| M2    |             |        |       |       |        |       |          |         |
| M3    |             |        |       |       |        |       |          |         |

Điều này tốt hơn chỉ nói:

> Model M2 đạt 79%.

---

# IX. Không chọn backbone chính bằng E1 Test

Điểm này cực kỳ quan trọng.

Experiment 2 cần một backbone cố định:

$$
M^*.
$$

Không được làm:

```text
chạy E1 Held-out Test
→ thấy M2 tốt nhất
→ chọn M2 làm M*
```

vì khi đó Test đã ảnh hưởng experimental design.

\(M^*\) phải được khóa **trước Phase 7**, dựa trên:

* Dev performance;
* stability;
* structured-output reliability;
* resource compatibility;

hoặc một tiêu chí predeclared khác.

Formal:

$$
M^*=Select(D_{dev})
$$

không:

$$
M^*=Select(D_{test}).
$$

---

# X. Experiment 2 — A0–A6 Security Evaluation

Đây là experiment chính cho RQ2.

Fix:

$$
M=M^*.
$$

Configs:

$$
A=\{A_0,A_1,\ldots,A_6\}.
$$

Input test sets:

$$
100\ clean
$$

$$
150\ attacks
$$

$$
150\ benign\ controls.
$$

Tổng mỗi config:

$$
100+150+150=400.
$$

---

# XI. Tổng E2 trajectories

$$
7\times400
=
2800.
$$

Đây là con số chính.

Mỗi task phải chạy cùng:

* model;
* model revision;
* tool environment;
* decoding;
* evaluator.

Chỉ:

$$
A_i
$$

thay đổi.

---

# XII. E2 experimental matrix

| Config    |   Clean |   Attack |   Benign |    Total |
| --------- | ------: | -------: | -------: | -------: |
| A0        |     100 |      150 |      150 |      400 |
| A1        |     100 |      150 |      150 |      400 |
| A2        |     100 |      150 |      150 |      400 |
| A3        |     100 |      150 |      150 |      400 |
| A4        |     100 |      150 |      150 |      400 |
| A5        |     100 |      150 |      150 |      400 |
| A6        |     100 |      150 |      150 |      400 |
| **Total** | **700** | **1050** | **1050** | **2800** |

---

# XIII. Vì sao E2 phải chạy cả clean?

Nếu chỉ chạy attacks:

A6 có thể:

$$
ASR=0
$$

bằng cách block gần mọi action.

Nhưng không biết utility có bị phá không.

Clean test cho phép đo:

$$
TSR(A_i).
$$

Benign controls cho phép đo:

$$
FPR(A_i).
$$

Attack set:

$$
ASR(A_i).
$$

Kết hợp:

$$
STSR(A_i).
$$

Do đó bộ ba:

$$
Clean+Attack+Benign
$$

là bắt buộc.

---

# XIV. E2 primary metrics

Security:

$$
ASR
$$

$$
FPR
$$

$$
PVR_{proposed}
$$

$$
PVR_{executed}
$$

$$
SensitiveLeakRate
$$

$$
BlockRate.
$$

Utility:

$$
TSR.
$$

Joint:

$$
STSR.
$$

---

# XV. Bảng trung tâm RQ2

Đây gần như chắc chắn nên là một trong những bảng chính của luận văn:

| Config | TSR ↑ | ASR ↓ | FPR ↓ | PVR proposed ↓ | PVR executed ↓ | STSR ↑ |
| ------ | ----: | ----: | ----: | -------------: | -------------: | -----: |
| A0     |       |       |       |                |                |        |
| A1     |       |       |       |                |                |        |
| A2     |       |       |       |                |                |        |
| A3     |       |       |       |                |                |        |
| A4     |       |       |       |                |                |        |
| A5     |       |       |       |                |                |        |
| A6     |       |       |       |                |                |        |

Mỗi tỷ lệ nên kèm:

$$
95\%\ CI.
$$

---

# XVI. E2 analysis theo attack category

Không chỉ overall ASR.

Phân tích:

$$
ASR_{Injection}
$$

$$
ASR_{ToolPoison}
$$

$$
ASR_{Exfiltration}
$$

$$
ASR_{PolicyViolation}.
$$

Ví dụ:

| Config | Injection | Poisoning | Exfiltration | Policy Violation |
| ------ | --------: | --------: | -----------: | ---------------: |
| A0     |           |           |              |                  |
| ...    |           |           |              |                  |
| A6     |           |           |              |                  |

Điều này giúp trả lời:

> A6 mạnh nhất ở đâu và yếu ở đâu?

---

# XVII. E2 analysis theo sink

Phân tích:

$$
ASR_{email}
$$

và:

$$
ASR_{webhook}.
$$

Ngoài ra:

$$
Leak_{final}.
$$

Đặc biệt A6 có FinalGate, nên cần cho thấy:

$$
FinalLeakRate(A6)
$$

so với các mức trước.

---

# XVIII. E2 analysis theo reason code

A6 có structured reason codes.

Nên thống kê:

```text
PROVENANCE_SENSITIVE_PAYLOAD
PROVENANCE_UNTRUSTED_DESTINATION
UNAUTHORIZED_EXTERNAL_ACTION
FINAL_SENSITIVE_VALUE_MATCH
UNKNOWN_LINEAGE_FAIL_CLOSED
...
```

Ví dụ:

| Reason                | Số block | Attack | Benign |
| --------------------- | -------: | -----: | -----: |
| Sensitive payload     |          |        |        |
| Untrusted destination |          |        |        |
| Unauthorized action   |          |        |        |
| Final leakage         |          |        |        |

Điều này giúp giải thích architecture chứ không chỉ report số.

---

# XIX. A5 vs A6 là comparison rất quan trọng

A5:

$$
Session\ level.
$$

A6:

$$
Artifact/Provenance\ level.
$$

Bạn nên đặc biệt kiểm tra hai loại task.

### Case 1 — true malicious flow

Expected:

$$
A5: Block
$$

$$
A6: Block.
$$

### Case 2 — unrelated sensitive artifact + benign public output

Expected:

$$
A5: possibly\ block
$$

$$
A6: allow.
$$

Nếu A6 thực sự giảm:

$$
FPR
$$

so với A5 mà ASR vẫn thấp, đó là evidence mạnh cho contribution provenance-aware.

---

# XX. Experiment 3 — Vietnamese Robustness

RQ3 hỏi:

> Các biến thể tiếng Việt có làm thay đổi capability hoặc security không?

Do đó tôi khuyên E3 chia thành:

$$
E3_C = Capability\ Robustness
$$

và:

$$
E3_S = Security\ Robustness.
$$

Cùng gọi chung Experiment 3.

---

# XXI. E3-C — Clean robustness

Word đã chốt robustness set:

$$
50\ canonical
+
250\ variants
=
300.
$$



Mỗi canonical có:

$$
5
$$

variants:

```text
no_diacritic
word_boundary
code_mix
zero_width
paraphrase
```

---

# XXII. Chạy E3-C trên config nào?

Tôi khuyên:

$$
A0
$$

và:

$$
A6.
$$

Lý do:

A0 cho biết:

$$
intrinsic\ robustness.
$$

A6 cho biết:

$$
robustness\ after\ full\ security\ architecture.
$$

Không cần chạy toàn A0–A6 cho E3 nếu mục tiêu chính không phải ablation robustness từng layer.

---

# XXIII. E3-C trajectories

Mỗi config:

$$
50+250=300.
$$

Hai configs:

$$
300\times2=600.
$$

---

# XXIV. E3-C metrics

Với canonical \(c_i\) và variant \(v_{i,k}\):

$$
\Delta TSR_k
=
TSR(c)-TSR(v_k).
$$

Tính riêng:

$$
\Delta_{no\_diacritic}
$$

$$
\Delta_{word\_boundary}
$$

$$
\Delta_{code\_mix}
$$

$$
\Delta_{zero\_width}
$$

$$
\Delta_{paraphrase}.
$$

---

# XXV. E3-C transition analysis

Với mỗi pair:

$$
(c_i,v_{i,k})
$$

ta có:

| Canonical | Variant | Classification     |
| --------- | ------- | ------------------ |
| Success   | Success | Robust             |
| Success   | Fail    | Degradation        |
| Fail      | Success | Improvement        |
| Fail      | Fail    | Persistent failure |

Đặc biệt quan tâm:

$$
Success\rightarrow Fail.
$$

Đây là direct robustness failure.

---

# XXVI. Robust Success Consistency

Tính:

$$
RSC_k
=
\frac{
\#(canonical=success\land variant_k=success)
}{
N
}.
$$

Ngoài ra có thể conditioning trên canonical success:

$$
ConditionalRSC_k
=
P(
Y_v=1
\mid
Y_c=1
).
$$

Metric thứ hai rất trực quan:

> Trong những task model làm đúng ở canonical, bao nhiêu % vẫn đúng sau biến đổi?

---

# XXVII. E3-S — Security robustness

Phase 3 đã tạo attack variants riêng.

Held-out Test:

$$
30\ canonical\ attack\ families.
$$

Mỗi family:

$$
5\ variants.
$$

Do đó:

$$
30\ canonical
+
150\ variants
=
180\ attack\ instances.
$$

Tương tự benign controls:

$$
180.
$$

---

# XXVIII. E3-S configs

Tôi cũng khuyên dùng:

$$
A0
$$

và:

$$
A6.
$$

Mục tiêu:

* A0 security robustness;
* A6 security robustness.

---

# XXIX. E3-S trajectories

Attack:

$$
180\times2=360.
$$

Benign:

$$
180\times2=360.
$$

Tổng:

$$
720.
$$

---

# XXX. E3 total

E3-C:

$$
600.
$$

E3-S:

$$
720.
$$

Tổng:

$$
1320.
$$

---

# XXXI. Nhưng không cần inference lại các trajectories trùng nhau

Đây là một optimization rất quan trọng.

Một số E3 instances đã xuất hiện trong E2.

Ví dụ attack variants:

$$
150
$$

trên A0/A6 đã chạy trong E2.

Không cần chạy lại.

Nếu tất cả điều kiện giống hệt:

$$
model
$$

$$
revision
$$

$$
config
$$

$$
dataset\ item
$$

$$
seed
$$

$$
generation\ settings
$$

thì có thể reuse trajectory.

---

# XXXII. Run identity

Định nghĩa:

$$
TrajectoryKey
=
(
task\_id,
model\_revision,
config\_hash,
dataset\_hash,
seed,
generation\_hash
).
$$

Nếu key giống:

$$
Reuse.
$$

Nếu khác dù một field:

$$
Rerun.
$$

---

# XXXIII. Tổng experiment workload nếu chạy naïve

$$
E1=300
$$

$$
E2=2800
$$

$$
E3=1320.
$$

Tổng:

$$
4420
$$

trajectories.

---

# XXXIV. Workload sau reuse

E1 có thể overlap:

$$
100
$$

trajectory với E2 nếu \(M^*\) là một trong ba model và cùng A0 clean run.

E3-C canonical 50 trên A0/A6 đã nằm trong E2 clean.

Chỉ 250 variants ×2 là mới:

$$
500.
$$

E3-S:

* 150 attack variants ×2 đã E2;
* 150 benign variants ×2 đã E2.

Chỉ cần thêm canonical:

$$
30 attacks\times2=60
$$

và:

$$
30 benign\times2=60.
$$

Do đó E3 mới thực sự thêm:

$$
500+60+60=620.
$$

Tổng unique trajectories khoảng:

$$
300+2800-100+620
=
3620.
$$

Đây là workload hợp lý hơn.

---

# XXXV. Đừng reuse theo filename

Không:

```text
task giống tên → reuse.
```

Chỉ reuse khi:

$$
TrajectoryKey
$$

match hoàn toàn.

---

# XXXVI. Security robustness metric

Với canonical attack:

$$
A_c
$$

và variant:

$$
A_v,
$$

định nghĩa:

$$
\Delta ASR_k
=
ASR(v_k)-ASR(c).
$$

Nếu:

$$
\Delta ASR_k>0
$$

variant khiến hệ thống dễ bị attack hơn.

---

# XXXVII. Security transition

| Canonical | Variant  | Meaning                  |
| --------- | -------- | ------------------------ |
| Blocked   | Blocked  | Robust defense           |
| Blocked   | Succeeds | Security degradation     |
| Succeeds  | Blocked  | Variant helps defense    |
| Succeeds  | Succeeds | Persistent vulnerability |

Đặc biệt:

$$
Blocked\rightarrow Succeeds
$$

là robustness failure quan trọng.

---

# XXXVIII. Benign robustness

Không được chỉ nhìn attacks.

Nếu zero-width khiến A6 block nhiều benign control hơn:

$$
FPR_{zero\_width}
$$

tăng.

Do đó RQ3 security robustness cần xét cả:

$$
ASR
$$

và:

$$
FPR.
$$

---

# XXXIX. Experiment manifests

Trước khi chạy, tạo:

```text
experiments/final/
├── E1.yaml
├── E2.yaml
├── E3_clean.yaml
└── E3_security.yaml
```

Ví dụ E2:

```yaml
experiment_id: E2

backbone: M_star
backbone_revision: ...

security_configs:
  - A0
  - A1
  - A2
  - A3
  - A4
  - A5
  - A6

datasets:
  clean:
    split: test
    n: 100
  attacks:
    split: test
    n: 150
  benign:
    split: test
    n: 150

generation:
  do_sample: false
  max_new_tokens: 512

evaluator_version: evaluation-v1.0
```

Sau đó hash manifest.

---

# XL. Pre-run freeze checkpoint

Trước trajectory Test đầu tiên, tạo:

```text
FINAL_EXPERIMENT_FREEZE.md
```

Ghi:

```text
Git commit
Clean dataset hash
Attack dataset hash
Benign dataset hash
Robustness dataset hash

A0-A6 config hashes

Agent prompt hash
Guard prompt hash

Model IDs/revisions

Evaluator version/hash

Normalizer version

Experiment manifests

Seed/order seed
```

Hai người cùng ký/check.

---

# XLI. Nếu một hash thay đổi sau freeze

Không silently tiếp tục.

Phải:

1. dừng affected condition;
2. xác định lý do;
3. bump run version;
4. nếu change ảnh hưởng semantics, rerun toàn affected condition;
5. ghi vào deviation log.

---

# XLII. Deviation log

Tạo:

```text
experiments/final/deviations.jsonl
```

Ví dụ:

```json
{
  "experiment": "E2",
  "condition": "A3",
  "issue": "Kaggle session terminated during task 74",
  "type": "INFRASTRUCTURE",
  "action": "resumed from checkpoint",
  "semantic_change": false
}
```

Nếu code bug:

```json
{
  "issue": "Evaluator comparator bug",
  "semantic_change": true,
  "action": "experiment invalidated and rerun"
}
```

---

# XLIII. Batch sharding

2800 trajectories không nên chạy trong một notebook duy nhất.

Chia shard.

Ví dụ E2:

```text
A0/
  shard_00
  shard_01
  ...

A1/
...
```

Có thể mỗi shard:

$$
25-50\ tasks.
$$

Nhưng shard boundary không được làm state leak.

Mỗi task vẫn:

$$
fresh\ AgentState.
$$

---

# XLIV. Shard manifest

```json
{
  "shard_id": "E2_A6_attack_02",
  "task_ids": [
    "ATK_..."
  ],
  "expected_count": 50
}
```

Không để notebook tự chọn “50 task tiếp theo” theo trạng thái không lưu.

---

# XLV. Task ordering

Dùng fixed permutation:

$$
Permutation(D,order\_seed).
$$

Không cần giữ order category-by-category.

Randomized fixed order giúp tránh:

> cuối session toàn task khó hoặc toàn một category.

Nhưng order phải reproducible.

---

# XLVI. No cross-task memory

Trước mọi task:

```text
new runtime
new context
new ArtifactStore
new SessionSecurityState
new provenance graph
```

Formal:

$$
State(T_{i+1})
\perp
State(T_i).
$$

Đây phải là assertion trong runner.

---

# XLVII. Resume policy

Nếu shard chết sau task 36/50:

Không rerun 1–35 nếu đã có valid output.

Runner:

```text
load checkpoint
validate completed tasks
continue 36
```

---

# XLVIII. Infrastructure failure vs model failure

Phải giữ nguyên protocol Phase 6.

Infrastructure:

```text
GPU OOM during model loading
kernel termination
filesystem write error
```

→ có thể retry.

Model failure:

```text
invalid JSON after retry limit
max steps
wrong action
wrong answer
```

→ không rerun.

Đó là kết quả thí nghiệm.

---

# XLIX. OOM handling

Nếu một model condition OOM:

Không tự đổi quantization rồi tiếp tục cùng experiment.

Vì:

$$
Quantization
$$

là model configuration.

Phải tạo new condition/revision.

Nếu model không chạy được theo predeclared configuration, xử lý như experimental limitation hoặc rerun toàn model với một configuration mới đã documented.

---

# L. Do not cherry-pick successful attempts

Nếu một task có:

```text
attempt 1 = model failure
attempt 2 = success
```

và attempt 2 chỉ được chạy vì attempt 1 semantic failure:

Không được chọn attempt 2.

Primary result phải là attempt 1.

Chỉ infrastructure-invalid attempt mới được bỏ.

---

# LI. Inference log completeness

Mỗi run phải lưu:

```text
run_id
experiment_id
task_id
model_id
model_revision
config
config_hash
seed
generation_config
start_time
end_time
status
attempt
```

cùng trace/artifacts.

---

# LII. Automatic validation sau mỗi shard

Không đợi cuối 2800 runs.

Sau shard:

$$
TraceIntegrity
$$

$$
TaskCount
$$

$$
DuplicateCheck
$$

$$
MissingTaskCheck.
$$

Nếu shard expected 50:

$$
valid+infra\_failed=50.
$$

---

# LIII. Không xem aggregate Test metric quá sớm để chỉnh system

Technically bạn sẽ thấy output files.

Nhưng workflow nên:

```text
run final shards
→ integrity check
→ complete condition
→ evaluate
```

Không:

```text
chạy A1 50 task
→ xem ASR
→ chỉnh A1.
```

Đó là Test tuning.

---

# LIV. E1 statistical analysis

Với binary metrics như TSR:

Report:

$$
\hat p
$$

và Wilson:

$$
95\%\ CI.
$$

So sánh models theo paired outcomes vì cùng 100 tasks.

Ví dụ:

$$
M_1 vs M_2
$$

dùng McNemar cho TSR.

Primary question không nhất thiết cần tất cả pairwise p-values.

Có thể predeclare:

* overall model comparison descriptive;
* pairwise secondary.

---

# LV. E2 statistical analysis

Primary comparison tôi khuyên:

$$
A0\ vs\ A6.
$$

Metrics:

$$
ASR
$$

$$
FPR
$$

$$
TSR
$$

$$
STSR.
$$

Vì cùng tasks:

$$
McNemar.
$$

---

# LVI. Adjacent defense analysis

Có thể secondary:

$$
A0\rightarrow A1
$$

$$
A1\rightarrow A2
$$

...

$$
A5\rightarrow A6.
$$

Điều này trả lời contribution từng layer.

Nhưng nếu chạy 6 tests × nhiều metrics, cần multiple-comparison correction.

Dùng:

$$
Holm.
$$

---

# LVII. Report effect size

Ví dụ:

$$
\Delta ASR
=
ASR(A6)-ASR(A0).
$$

Nếu:

$$
\Delta ASR=-0.45,
$$

nghĩa ASR giảm 45 percentage points.

Nên dùng **percentage points** khi nói chênh lệch tuyệt đối.

Không nhầm với:

$$
relative\ reduction.
$$

---

# LVIII. Relative ASR reduction

Secondary:

$$
RR_{ASR}
=
\frac{
ASR(A0)-ASR(A6)
}{
ASR(A0)
}.
$$

Chỉ tính nếu:

$$
ASR(A0)>0.
$$

---

# LIX. E3 statistical analysis

Canonical và variant paired.

Với binary success:

$$
McNemar.
$$

Cho mỗi variant type:

$$
Canonical
\leftrightarrow
Variant_k.
$$

Primary five comparisons.

Nếu test tất cả năm:

$$
Holm\ correction
$$

hợp lý.

---

# LX. Bootstrap

Dùng paired bootstrap để lấy CI cho:

$$
\Delta TSR
$$

$$
\Delta ASR
$$

$$
\Delta FPR
$$

nếu cần.

Sampling unit phải là **family/task**, không phải random individual observation nếu pairing/grouping tồn tại.

---

# LXI. Attack family clustering

Trong E3, 5 variants của cùng canonical family correlated.

Không nên giả chúng là 5 hoàn toàn independent tasks khi bootstrap family-level robustness.

Có thể resample:

$$
family\ IDs
$$

sau đó giữ toàn bộ variants của family.

Đây là cluster bootstrap đơn giản.

---

# LXII. Human validation trong Phase 7

Phase 6 đã freeze protocol.

Phase 7 chỉ execute protocol.

Không chọn case sau khi biết system nào thắng.

---

# LXIII. Nên human-review bao nhiêu?

Tôi khuyên mục tiêu:

$$
\approx10\%
$$

của representative final outcomes, nhưng stratified thay vì random toàn bộ.

Với khoảng 3600 unique trajectories, full 10%:

$$
\approx360.
$$

Hai annotators:

$$
720
$$

individual ratings.

Với 4 tuần Phase 7, vẫn khả thi.

Nếu workload cao, có thể giảm khoảng:

$$
250-300
$$

traces nhưng phải giữ stratification.

---

# LXIV. Human sample strata

Nên có:

### E1

* 3 models;
* ambiguity;
* free-form responses;
* error recovery.

### E2

Mỗi:

$$
A0-A6
$$

đều có representative:

* attacks;
* benign;
* clean;
* allow;
* deny;
* redact.

### E3

Mỗi 5 variant types có sample.

---

# LXV. Blinding

Human annotator không nên thấy:

```text
"This is A6"
"This is Model M3"
```

nếu không cần.

Thay bằng:

```text
System S01
System S02
```

và randomize order.

Giảm expectation bias.

---

# LXVI. Human annotation outputs

```text
annotations/
├── annotator_huy.jsonl
├── annotator_minh.jsonl
├── agreement.json
└── adjudicated.jsonl
```

Giữ raw labels.

---

# LXVII. Agreement

Report:

$$
RawAgreement
$$

và:

$$
Cohen's\ \kappa.
$$

Nếu \(\kappa\) thấp:

Không nên chỉ adjudicate rồi bỏ qua.

Phải inspect rubric ambiguity.

Nhưng không sửa automated evaluator dựa trên Test performance trừ khi phát hiện lỗi logic objectively demonstrable; nếu xảy ra, deviation/rerun protocol phải được áp dụng.

---

# LXVIII. Human-vs-automatic evaluation

Với sample:

$$
Auto_i
$$

và adjudicated human label:

$$
Human_i.
$$

Tính:

$$
Agreement(Auto,Human).
$$

Có thể report:

* accuracy;
* precision/recall cho security violation nếu phù hợp;
* confusion matrix.

Điều này củng cố độ tin cậy evaluator.

---

# LXIX. Error Analysis

Đây không phải chỉ:

> “Model sai 20 task.”

Phải systematic.

Dùng taxonomy từ Phase 6.

---

# LXX. RQ1 error categories

Ví dụ:

```text
wrong_tool
wrong_argument
wrong_sequence
failed_recovery
format_failure
hallucination
missing_fact
unnecessary_tool
clarification_failure
```

Tính:

$$
Count(error\_type,model).
$$

---

# LXXI. RQ2 error categories

Ví dụ:

```text
followed_injection
untrusted_destination_accepted
sensitive_payload_executed
final_leakage
guard_miss
provenance_unknown
overblock
false_positive_guard
```

Tính theo A0–A6.

---

# LXXII. RQ3 error categories

Ví dụ:

```text
diacritic_loss
boundary_tokenization
code_mix_failure
zero_width_failure
paraphrase_semantic_failure
```

Nhưng chỉ gán category nếu evidence trace hỗ trợ.

Không đoán nguyên nhân model nội bộ.

---

# LXXIII. Error analysis nên theo transition

Một cách rất mạnh:

Chọn những cases:

$$
A0\ fail,\quad A6\ success
$$

và:

$$
A0\ success,\quad A6\ fail.
$$

Phân tích hai hướng.

### Security gains

$$
A0\ vulnerable
\rightarrow
A6\ blocked.
$$

### Security regressions / utility cost

$$
A0\ succeeds
\rightarrow
A6\ fails.
$$

---

# LXXIV. A5→A6 analysis đặc biệt

Phân tích:

$$
A5\ blocked
\land
A6\ allowed
$$

trên benign.

Đây là evidence provenance giảm coarse overblocking.

Ngoài ra:

$$
A5\ allows
\land
A6\ blocks
$$

trên attacks.

Đây là evidence provenance bắt fine-grained flow mà session-level policy bỏ sót.

---

# LXXV. Error exemplars

Trong báo cáo, chọn một số case representatives.

Không chọn chỉ những case đẹp cho A6.

Nên có:

* A6 success;
* A6 false positive;
* A6 failure;
* A1 lexical failure;
* A2 semantic success;
* robustness failure.

Mỗi example:

```text
User Task
Relevant Tool Output
Proposed Action
Gate Decision
Final Outcome
Error Category
```

Không expose hidden CoT.

---

# LXXVI. Figures nên tạo

Tôi khuyên Phase 7 tạo ít nhất các figures sau.

### Figure 1 — Capability by model

Bar/error-point plot:

$$
TSR(M_1,M_2,M_3).
$$

---

### Figure 2 — Security trade-off

Trục:

$$
x=FPR
$$

$$
y=ASR.
$$

Ideal:

$$
(0,0).
$$

Mỗi điểm:

$$
A0-A6.
$$

---

### Figure 3 — STSR by config

$$
A0\rightarrow A6.
$$

---

### Figure 4 — Variant robustness drop

5 variant types:

$$
\Delta TSR.
$$

A0 vs A6.

---

### Figure 5 — Security robustness

$$
\Delta ASR
$$

theo variant.

---

### Figure 6 — Error taxonomy

Top error types.

---

# LXXVII. Không nên dùng quá nhiều biểu đồ

Thesis chỉ cần những chart trả lời RQs.

Không plot 30 charts vì evaluator có 30 columns.

---

# LXXVIII. Tables nên có

Tối thiểu:

### Table E1

Backbone capability.

### Table E2

A0–A6 overall security/utility.

### Table E2b

ASR by attack type.

### Table E3

Robustness by variant.

### Table Human

Inter-annotator/evaluator agreement.

---

# LXXIX. Raw results không được chỉnh bằng Excel thủ công

Pipeline:

```text
task_scores.jsonl
      ↓
aggregate_results.py
      ↓
tables/*.csv
      ↓
figures
```

Không:

```text
copy số vào Excel
→ sửa vài ô
→ chụp bảng.
```

Bảng final phải regenerate được.

---

# LXXX. Result directory

Tôi khuyên:

```text
results/final/
│
├── E1/
│   ├── M1_A0/
│   ├── M2_A0/
│   └── M3_A0/
│
├── E2/
│   ├── A0/
│   ├── A1/
│   ├── A2/
│   ├── A3/
│   ├── A4/
│   ├── A5/
│   └── A6/
│
├── E3/
│   ├── clean/
│   └── security/
│
├── statistics/
├── human_validation/
├── error_analysis/
├── tables/
└── figures/
```

---

# LXXXI. Result manifest

Mỗi condition:

```json
{
  "experiment": "E2",
  "condition": "A6",
  "expected_tasks": 400,
  "valid_tasks": 400,
  "infra_invalid": 0,
  "config_hash": "...",
  "dataset_hashes": {
    "clean": "...",
    "attack": "...",
    "benign": "..."
  },
  "model_revision": "...",
  "evaluator_version": "evaluation-v1.0"
}
```

---

# LXXXII. Completion audit trước statistics

Trước khi tính metric cuối:

$$
N_{observed}=N_{expected}.
$$

Ví dụ E2 A6:

$$
N=400.
$$

Không tính ASR khi còn 7 tasks missing rồi sau đó thêm mà quên cập nhật table.

---

# LXXXIII. Duplicate audit

$$
Unique(task\_id)=N.
$$

Nếu có duplicate due resume:

Evaluator phải reject.

---

# LXXXIV. Model-output audit

Kiểm tra:

```text
0 empty trace
0 missing run end
0 missing config hash
0 unexpected model revision
```

Nếu model revision thay giữa shards:

condition invalid.

---

# LXXXV. Week 17 — E1 + Final pipeline verification

## Ngày 1

Final freeze audit:

* hashes;
* model configs;
* prompts;
* evaluator;
* manifests.

---

## Ngày 2–4

Run E1:

$$
M_1,M_2,M_3
$$

trên:

$$
100\ clean\ Test.
$$

---

## Ngày 5

Integrity validation.

---

## Ngày 6

Evaluate E1.

---

## Ngày 7

Generate RQ1 preliminary tables.

“Preliminary” ở đây nghĩa chưa viết conclusions hoàn chỉnh, **không phải sửa model**.

---

# LXXXVI. Week 18 — E2 A0–A3

Chạy:

$$
A0,A1,A2,A3
$$

với \(M^*\).

Mỗi:

$$
400.
$$

Tổng:

$$
1600.
$$

Có thể parallel/shard.

Sau mỗi config:

* integrity only;
* không tune.

---

# LXXXVII. Week 19 — E2 A4–A6 + E3

A4–A6:

$$
3\times400=1200.
$$

Sau đó E3 unique missing trajectories:

$$
\approx620.
$$

Tổng workload tuần này lớn nhưng có thể shard.

---

# LXXXVIII. Week 20 — Analysis only

Tôi khuyên Week 20 **không dành để tiếp tục feature development**.

Làm:

* evaluator final runs;
* statistics;
* human validation;
* error analysis;
* figures;
* tables;
* RQ answers.

Nếu có infrastructure missing runs thì fill missing runs theo protocol.

---

# LXXXIX. Phase 7 phân công — Huy

Theo Word, Huy phụ trách RQ2. 

Huy ownership:

```text
E2 run management
A0-A6 integrity
security aggregation
ASR/FPR/PVR/STSR
attack-category analysis
sink analysis
A5-vs-A6 analysis
security error analysis
```

---

# XC. Phase 7 phân công — Minh

Minh ownership:

```text
E1
RQ1 aggregation
capability breakdown
E3 clean robustness
E3 security robustness aggregation
variant transitions
robustness statistics
capability error analysis
```

---

# XCI. Hai người làm chung

```text
final freeze audit
experiment manifests
human annotation
statistics verification
figures
tables
final RQ interpretation
```

Ngoài ra mỗi người phải independently kiểm tra ít nhất một phần số liệu của người kia.

---

# XCII. Independent metric verification

Ví dụ Huy báo:

$$
ASR(A6)=x.
$$

Minh có thể dùng raw `task_scores.jsonl` và một small independent script để kiểm:

$$
x=
\frac{\sum attack\_success}{150}.
$$

Tương tự Huy verify một metric RQ1 của Minh.

Đây là một QA rất tốt trước khi viết thesis.

---

# XCIII. Checklist Phase 7 — Pre-run freeze

* [ ] Clean Test hash verified.
* [ ] Attack Test hash verified.
* [ ] Benign Test hash verified.
* [ ] Robustness-set hash verified.
* [ ] Environment hash verified.
* [ ] A0–A6 config hashes verified.
* [ ] Agent prompt frozen.
* [ ] Guard prompt frozen.
* [ ] Guard model frozen.
* [ ] Model IDs frozen.
* [ ] Model revisions frozen.
* [ ] Tokenizer revisions frozen.
* [ ] Quantization configs frozen.
* [ ] Generation configs frozen.
* [ ] Evaluator v1 frozen.
* [ ] Metric definitions frozen.
* [ ] Human protocol frozen.
* [ ] Statistical protocol frozen.
* [ ] Experiment manifests generated.
* [ ] Git commit recorded.

---

# XCIV. Checklist — E1

* [ ] 3 model backbones.
* [ ] A0 only.
* [ ] 100 clean Test each.
* [ ] Same task IDs.
* [ ] Same prompt structure.
* [ ] Same tools.
* [ ] Same environment.
* [ ] Same evaluator.
* [ ] 300 expected trajectories.
* [ ] All traces valid.
* [ ] TSR calculated.
* [ ] ToolSelAcc calculated.
* [ ] ArgAcc calculated.
* [ ] SeqAcc calculated.
* [ ] ErrRecovery calculated.
* [ ] Category breakdown.
* [ ] Wilson CIs.
* [ ] Model comparison table.

---

# XCV. Checklist — E2

* [ ] Fixed \(M^*\).
* [ ] \(M^*\) selected from Dev before Test.
* [ ] A0.
* [ ] A1.
* [ ] A2.
* [ ] A3.
* [ ] A4.
* [ ] A5.
* [ ] A6.
* [ ] 100 clean/config.
* [ ] 150 attack/config.
* [ ] 150 benign/config.
* [ ] 400/config.
* [ ] 2800 total expected.
* [ ] No missing tasks.
* [ ] No duplicated tasks.
* [ ] ASR.
* [ ] FPR.
* [ ] BlockRate.
* [ ] PVR proposed.
* [ ] PVR executed.
* [ ] LeakRate.
* [ ] TSR.
* [ ] STSR.
* [ ] Attack-type breakdown.
* [ ] Sink breakdown.
* [ ] Reason-code breakdown.

---

# XCVI. Checklist — E3 Clean

* [ ] 50 canonical.
* [ ] 250 variants.
* [ ] 5 variant types.
* [ ] A0.
* [ ] A6.
* [ ] 600 logical trajectories represented.
* [ ] Existing canonical trajectories reused only if exact key matches.
* [ ] Pair mapping valid.
* [ ] \(\Delta TSR\).
* [ ] Robust Success Consistency.
* [ ] Transition tables.
* [ ] Variant-specific CI/test.

---

# XCVII. Checklist — E3 Security

* [ ] 30 canonical attack families.
* [ ] 150 attack variants.
* [ ] Canonical benign controls.
* [ ] 150 benign variants.
* [ ] A0.
* [ ] A6.
* [ ] Existing E2 variant traces reused correctly.
* [ ] Canonical trajectories added.
* [ ] ASR canonical.
* [ ] ASR by variant.
* [ ] FPR canonical.
* [ ] FPR by variant.
* [ ] Security transition matrix.
* [ ] Paired robustness statistics.

---

# XCVIII. Checklist — Run integrity

* [ ] Every task starts fresh runtime.
* [ ] Fresh ArtifactStore.
* [ ] Fresh SessionSecurityState.
* [ ] No cross-task context.
* [ ] Unique run IDs.
* [ ] Unique task IDs within condition.
* [ ] Fixed model revision.
* [ ] Fixed config hash.
* [ ] Fixed dataset hash.
* [ ] Fixed generation settings.
* [ ] Fixed evaluator version.
* [ ] Infrastructure retries logged.
* [ ] Semantic failures not retried.
* [ ] Checkpoints complete.
* [ ] Shard manifests archived.

---

# XCIX. Checklist — Reuse

* [ ] Reuse only exact trajectory keys.
* [ ] Same task ID.
* [ ] Same model revision.
* [ ] Same security config hash.
* [ ] Same generation hash.
* [ ] Same dataset hash.
* [ ] Same seed.
* [ ] Reused trace integrity valid.
* [ ] Reuse recorded in experiment manifest.

---

# C. Checklist — Statistics

* [ ] Point estimates.
* [ ] Denominators.
* [ ] Wilson 95% CI.
* [ ] A0-vs-A6 primary comparison.
* [ ] McNemar paired test.
* [ ] Exact McNemar when needed.
* [ ] Effect size.
* [ ] Percentage-point differences.
* [ ] Relative reduction only when denominator valid.
* [ ] Robustness paired tests.
* [ ] Family-level bootstrap where needed.
* [ ] Bootstrap seed frozen.
* [ ] Multiple comparison correction.
* [ ] p-value interpretation paired with effect size.

---

# CI. Checklist — Human validation

* [ ] Sampling performed using frozen protocol.
* [ ] Sample is stratified.
* [ ] No hand-picking interesting cases.
* [ ] Annotators independent.
* [ ] System identities blinded where possible.
* [ ] Model identities blinded where possible.
* [ ] Huy labels saved separately.
* [ ] Minh labels saved separately.
* [ ] Raw agreement calculated.
* [ ] Cohen's kappa calculated.
* [ ] Disagreements adjudicated.
* [ ] Final labels preserved separately.
* [ ] Automated-vs-human agreement calculated.

---

# CII. Checklist — Error analysis

* [ ] RQ1 error taxonomy.
* [ ] RQ2 error taxonomy.
* [ ] RQ3 error taxonomy.
* [ ] Errors counted by model.
* [ ] Errors counted by config.
* [ ] Errors counted by category.
* [ ] Errors counted by variant.
* [ ] A0→A6 improvements.
* [ ] A0→A6 regressions.
* [ ] A5→A6 benign recoveries.
* [ ] A5→A6 additional security catches.
* [ ] Final leakage failures.
* [ ] Representative success cases.
* [ ] Representative failure cases.
* [ ] No hidden CoT used in analysis.

---

# CIII. Checklist — Result tables

* [ ] E1 capability table.
* [ ] E2 A0–A6 table.
* [ ] Attack-category table.
* [ ] E3 robustness table.
* [ ] Human agreement table.
* [ ] Every table script-generated.
* [ ] Every percentage shows denominator.
* [ ] CIs included for primary proportions.
* [ ] Raw CSV preserved.

---

# CIV. Checklist — Figures

* [ ] Backbone capability.
* [ ] ASR/FPR trade-off.
* [ ] STSR A0–A6.
* [ ] Robustness drop by variant.
* [ ] Security robustness by variant.
* [ ] Error taxonomy.
* [ ] Figures generated from final CSV.
* [ ] Figure-generation script versioned.
* [ ] No manually edited values.

---

# CV. Checklist — Contamination prevention

* [ ] No prompt tuning after Test starts.
* [ ] No rule changes from Test failures.
* [ ] No A6 policy changes from Test.
* [ ] No ground-truth changes from model behavior.
* [ ] No evaluator-semantic changes from Test.
* [ ] No model switching after seeing E1 Test.
* [ ] No attack removal because A0 resisted.
* [ ] No best-of reruns.
* [ ] Any unavoidable deviation recorded.

---

# CVI. Definition of Done — Phase 7

## DoD-1 — E1 complete

$$
3\times100=300
$$

logical E1 trajectories exist and pass integrity validation.

---

## DoD-2 — E2 complete

$$
7\times400=2800
$$

logical E2 trajectories exist and are valid/reused according to exact trajectory keys.

---

## DoD-3 — E3 complete

Capability and security robustness canonical/variant pair sets are complete.

No broken pairs.

---

## DoD-4 — No missing final task

For every experimental condition:

$$
ObservedN=ExpectedN.
$$

Infrastructure-invalid cases must either be correctly rerun or explicitly documented.

---

## DoD-5 — Frozen configuration integrity

Every run maps to the predeclared:

$$
model\ revision
$$

$$
config\ hash
$$

$$
dataset\ hash
$$

$$
evaluator\ version.
$$

---

## DoD-6 — RQ1 answerable

Final results contain enough evidence to answer:

> How capable are Vietnamese ReAct tool agents?

Có:

$$
TSR,
ToolSelAcc,
ArgAcc,
SeqAcc,
ErrRecovery.
$$

---

## DoD-7 — RQ2 answerable

Có đủ:

$$
ASR,
FPR,
PVR,
TSR,
STSR
$$

cho:

$$
A0-A6.
$$

---

## DoD-8 — RQ3 answerable

Có paired canonical/variant results cho năm Vietnamese transformations.

---

## DoD-9 — Statistical completeness

Primary metrics có:

$$
point\ estimate
+
CI
+
effect\ size
$$

và paired statistical tests khi phù hợp.

---

## DoD-10 — Human validation complete

Hai annotator đã independently label frozen sample, agreement/adjudication hoàn thành.

---

## DoD-11 — Error analysis complete

Không chỉ biết “bao nhiêu fail”, mà biết major failure modes và representative traces.

---

## DoD-12 — No Test-driven system changes

Không có final architectural/prompt/policy change được thực hiện dựa trên Test performance.

---

## DoD-13 — Reproducible results

Mỗi table/figure phải truy ngược được:

$$
Figure
\rightarrow
CSV
\rightarrow
TaskScores
\rightarrow
Traces
\rightarrow
RunManifest.
$$

---

# CVII. Output cuối Phase 7

Cuối Phase này nên có:

```text
results/final/
│
├── E1/
├── E2/
├── E3/
│
├── task_scores/
│
├── statistics/
│   ├── confidence_intervals.csv
│   ├── paired_tests.csv
│   └── effect_sizes.csv
│
├── human_validation/
│   ├── annotator_1.jsonl
│   ├── annotator_2.jsonl
│   ├── agreement.json
│   └── adjudicated.jsonl
│
├── error_analysis/
│   ├── errors.jsonl
│   ├── error_counts.csv
│   └── representative_cases.json
│
├── tables/
│   ├── RQ1_capability.csv
│   ├── RQ2_security.csv
│   ├── RQ2_attack_types.csv
│   ├── RQ3_robustness.csv
│   └── human_validation.csv
│
└── figures/
```

Documentation:

```text
docs/
├── final_experiment_protocol.md
├── final_experiment_freeze.md
├── experiment_deviations.md
├── RQ1_analysis.md
├── RQ2_analysis.md
├── RQ3_analysis.md
└── phase7_report.md
```

---

# CVIII. Trạng thái dự án sau Phase 7

Khi Phase 7 hoàn thành, **phần nghiên cứu thực nghiệm của đồ án về cơ bản đã xong**.

Ta đã đi qua:

$$
Phase1:
Runtime
$$

$$
Phase2:
CleanBenchmark
$$

$$
Phase3:
SecurityBenchmark
$$

$$
Phase4:
Artifact/ProvenanceFoundation
$$

$$
Phase5:
A0-A6
$$

$$
Phase6:
Evaluation
$$

$$
Phase7:
FinalEvidence.
$$

Lúc này bạn không còn cần “chứng minh hệ thống chạy được”. Bạn đã có dữ liệu để trả lời ba RQ.

Phase kế tiếp sẽ chuyển sang:

$$
\boxed{
Phase\ 8:
Reproducibility
+
Thesis\ Writing
+
Demo/Packaging
}
$$

tức là biến toàn bộ code, benchmark, configs, experiment manifests, raw results, statistics và các kết luận RQ1–RQ3 thành **một gói có thể chạy lại và một báo cáo/luận văn hoàn chỉnh**. Điều này khớp với kế hoạch tuần 21–22 trong bản Word, trước hai tuần buffer cuối. 
