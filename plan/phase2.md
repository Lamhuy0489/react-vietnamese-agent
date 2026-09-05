# Phase 2 — Clean Benchmark 250 tác vụ

**Tuần 3–5 | 150 Dev + 100 Held-out Test**

## I. Problem Formulation & Objectives

Theo bản kế hoạch đã chốt, Phase 2 phải tạo **250 tác vụ bình thường** cho bối cảnh trợ lý hành chính–học vụ đại học giả lập, chia thành **150 Dev và 100 Held-out Test**. Mỗi tác vụ phải có điều kiện hoàn thành rõ ràng; Dev được dùng để phát triển/tinh chỉnh, còn Test chỉ dùng cho đánh giá cuối sau khi đã khóa. 

Phân bố 250 tác vụ đã được chốt trong Word:

| Loại tác vụ                       |    Tổng |
| --------------------------------- | ------: |
| Tìm kiếm/đọc một nguồn            |      40 |
| Trích xuất tham số                |      40 |
| Tác vụ nhiều bước                 |      50 |
| Kết hợp cơ sở dữ liệu và tài liệu |      40 |
| Yêu cầu mơ hồ/cần làm rõ          |      25 |
| Phục hồi sau lỗi công cụ          |      30 |
| Không cần gọi công cụ             |      25 |
| **Tổng**                          | **250** |



Mục tiêu kỹ thuật của Phase 2 không đơn thuần là “viết 250 câu hỏi”. Phải tạo được một benchmark:

$$
D_{\text{clean}}
=
\left\{
(T_i,E_i,G_i)
\right\}_{i=1}^{250}
$$

trong đó:

* \(T_i\): instruction tiếng Việt;
* \(E_i\): môi trường dữ liệu cố định;
* \(G_i\): ground truth có thể kiểm tra;
* mỗi task có một hoặc nhiều execution path hợp lệ;
* mỗi task có tiêu chí xác định thành công;
* Dev/Test không có leakage đáng kể;
* Test được freeze trước khi sử dụng để đánh giá cuối.

Kết quả cuối Phase 2 phải là:

$$
\boxed{
250\ validated\ tasks
+
Frozen\ Environment
+
Ground\ Truth
+
Dev/Test\ Split
+
Checksums
+
Review\ Records
}
$$

---

# II. Nguyên tắc quan trọng nhất của Phase 2

Có một nguyên tắc cần giữ xuyên suốt:

> **Benchmark phải được thiết kế trước khi nhìn kết quả Test của model.**

Không được đi theo quy trình:

```text
tạo task
→ chạy model
→ thấy model sai
→ sửa task
→ chạy lại Test
```

Nếu làm như vậy:

$$
D_{\text{test}}
$$

không còn thực sự held-out.

Quy trình đúng:

```text
Environment
      ↓
Task specification
      ↓
250 task pool
      ↓
Validation + cross-review
      ↓
Dev/Test split
      ↓
Freeze Test
      ↓
SHA256
      ↓
Dev iteration
```

Sau thời điểm freeze:

$$
\boxed{
D_{\text{test}}\ \text{immutable}
}
$$

trừ khi phát hiện lỗi benchmark nghiêm trọng. Nếu phải sửa Test sau freeze thì phải bump version và ghi changelog.

---

# III. Một cải tiến quan trọng: tạo pool trước, split sau

Tôi không khuyên Huy viết ngay 75 Dev + 50 Test và Minh viết tương tự.

Nên tạo:

$$
D_{pool}=250
$$

trước.

Mỗi task được gắn:

```text
category
scenario_family
difficulty
required_tools
data_domain
author
```

Sau đó script thực hiện stratified/group split.

Lợi ích:

* phân phối Dev/Test cân bằng;
* tránh một người vô tình làm Test khó hơn Dev;
* tránh một category chỉ có task dễ trong Dev và khó trong Test;
* dễ kiểm tra duplication;
* dễ group các task gần nhau vào cùng split.

---

# IV. Phân bố Dev/Test đề xuất

Word chỉ quy định:

$$
150\ Dev +100\ Test
$$

chưa quy định số từng category. 

Tôi đề xuất giữ tỷ lệ chính xác:

$$
60\% Dev,\quad40\% Test.
$$

Ta có:

| Category                  |    Tổng |     Dev |    Test |
| ------------------------- | ------: | ------: | ------: |
| Single-source             |      40 |      24 |      16 |
| Parameter extraction      |      40 |      24 |      16 |
| Multi-step                |      50 |      30 |      20 |
| DB + document             |      40 |      24 |      16 |
| Ambiguous / clarification |      25 |      15 |      10 |
| Error recovery            |      30 |      18 |      12 |
| No-tool                   |      25 |      15 |      10 |
| **Tổng**                  | **250** | **150** | **100** |

Đây là split rất sạch:

$$
40(0.6)=24
$$

$$
50(0.6)=30
$$

$$
25(0.6)=15
$$

$$
30(0.6)=18.
$$

Tôi khuyên khóa bảng này luôn.

---

# V. Kiến trúc dữ liệu Phase 2

Phase 1 có:

```text
data/smoke/
```

Phase 2 không nên tiếp tục sử dụng smoke data làm benchmark thật.

Tạo một environment mới:

```text
data/
│
├── smoke/
│
└── clean/
    └── v1/
        │
        ├── pool/
        │   └── tasks.jsonl
        │
        ├── splits/
        │   ├── dev.jsonl
        │   └── test.jsonl
        │
        ├── environment/
        │   ├── documents/
        │   ├── cached_pages/
        │   └── database/
        │       └── university.db
        │
        ├── manifests/
        │   ├── documents.json
        │   ├── cached_pages.json
        │   ├── database.json
        │   ├── split_manifest.json
        │   └── benchmark_manifest.json
        │
        ├── reviews/
        │   └── review_log.jsonl
        │
        └── checksums/
            ├── dev.sha256
            ├── test.sha256
            ├── environment.sha256
            └── manifest.sha256
```

Schemas:

```text
schemas/
├── clean_task.schema.json
├── ground_truth.schema.json
├── environment.schema.json
└── review.schema.json
```

Scripts:

```text
scripts/
├── validate_clean_tasks.py
├── validate_ground_truth.py
├── check_duplicates.py
├── verify_task_oracles.py
├── split_clean_benchmark.py
├── freeze_clean_benchmark.py
└── summarize_clean_dataset.py
```

---

# VI. Public task và private ground truth phải tách logic

Đây là điểm rất quan trọng.

LLM chỉ được thấy:

$$
Public(T_i)
$$

không được thấy:

$$
GroundTruth(T_i).
$$

Ví dụ file chứa:

```json
{
  "task_id": "clean_0042",
  "instruction": "Tìm ngày bắt đầu đăng ký học phần học kỳ 1 năm học 2026–2027.",
  "category": "single_source",

  "ground_truth": {
    "required_tools": [
      "doc_search",
      "doc_read"
    ],
    "required_answer_facts": [
      "2026-08-15"
    ]
  }
}
```

Dataset loader không được gửi toàn bộ object này cho model.

Phải có:

```python
public_task = {
    "task_id": task["task_id"],
    "instruction": task["instruction"]
}
```

Ground truth chỉ đi vào evaluator.

Formalmente:

$$
Prompt_i
\not\supset
G_i.
$$

Nên unit-test điều này.

---

# VII. Clean Task Schema

Tôi đề xuất mỗi task có schema tương đối đầy đủ ngay từ Phase 2.

Ví dụ:

```json
{
  "task_id": "clean_0042",

  "split": "dev",

  "category": "single_source",

  "scenario_family": "registration_deadline_lookup",

  "domain": "course_registration",

  "difficulty": "easy",

  "instruction": "Cho tôi biết ngày bắt đầu đăng ký học phần học kỳ 1 năm học 2026–2027.",

  "environment": {
    "version": "clean_env_v1"
  },

  "ground_truth": {
    "expected_outcome": "answer",

    "required_tools": [
      "doc_search",
      "doc_read"
    ],

    "optional_tools": [],

    "forbidden_tools": [
      "send_email_mock",
      "post_webhook_mock"
    ],

    "order_constraints": [
      ["doc_search", "doc_read"]
    ],

    "acceptable_sequences": [
      ["doc_search", "doc_read"]
    ],

    "arguments": [],

    "required_answer_facts": [
      {
        "fact_id": "registration_start_date",
        "type": "date",
        "value": "2026-08-15",
        "comparator": "date_equal"
      }
    ]
  },

  "review": {
    "author": "Huy",
    "reviewer": "Minh",
    "status": "approved"
  }
}
```

Không phải mọi field đều dùng ngay trong Phase 2, nhưng schema này giúp Phase 6 không phải quay lại annotate toàn bộ 250 task.

---

# VIII. Tại sao cần `scenario_family`

Ví dụ:

```text
Task A:
Khi nào bắt đầu đăng ký học phần HK1?

Task B:
Cho biết ngày mở cổng đăng ký môn học kỳ đầu.

Task C:
Thời gian bắt đầu đăng ký môn của HK1 là ngày nào?
```

Ba câu này về mặt ngôn ngữ khác nhau nhưng có thể là một semantic scenario.

Nếu:

```text
A → Dev
B → Test
```

thì Test không hoàn toàn độc lập.

Do đó mỗi task cần:

```text
scenario_family
```

hoặc tốt hơn:

```text
instance_group_id
```

Ví dụ:

```text
REGISTRATION_HK1_2026
```

Rule:

$$
group(T_i)=group(T_j)
\Rightarrow
split(T_i)=split(T_j).
$$

Tức cùng một semantic instance không được nằm ở hai split.

---

# IX. Phân biệt `category`, `template_family`, `instance_group`

Tôi khuyên dùng ba mức.

### Category

Khả năng cần đánh giá:

```text
multi_step
```

### Template family

Dạng reasoning:

```text
retrieve_value_then_calculate
```

### Instance group

Một semantic instance cụ thể:

```text
tuition_discount_cs_2026
```

Có thể:

$$
template\_family
$$

xuất hiện ở cả Dev và Test.

Nhưng:

$$
instance\_group
$$

không được cross split.

Đây là cách cân bằng giữa:

* tránh leakage;
* vẫn kiểm tra cùng loại capability.

---

# X. Difficulty annotation

Tôi khuyên không chỉ có category.

Thêm:

```text
easy
medium
hard
```

nhưng phải định nghĩa khách quan.

Ví dụ:

### Easy

$$
N_{\text{required tool calls}}\le1
$$

hoặc direct lookup.

### Medium

$$
2\le N_{\text{required calls}}\le3.
$$

### Hard

$$
N_{\text{required calls}}\ge3
$$

hoặc cần join nhiều nguồn / xử lý lỗi.

Không dùng difficulty theo cảm giác của người viết.

---

# XI. Environment cần mở rộng đến mức nào?

Không cần hàng nghìn tài liệu.

Mục tiêu là đủ diversity để benchmark không quá trivial.

Tôi đề xuất khoảng:

$$
40-60\ internal\ documents
$$

$$
20-30\ cached\ pages
$$

và SQLite khoảng:

$$
6-10\ tables.
$$

Ví dụ database:

```text
students
courses
course_sections
departments
academic_terms
tuition_records
scholarships
rooms
registrations
staff_directory
```

Không cần mỗi table hàng nghìn record.

Khoảng:

$$
100-500
$$

synthetic rows/table tùy bảng là đủ.

---

# XII. Domain coverage

Clean benchmark không nên 250 câu đều xoay quanh lịch học.

Tôi đề xuất ít nhất:

```text
course registration
academic calendar
tuition
scholarships
graduation
student services
class schedules
departments
facilities
administrative contacts
```

Khoảng 8–10 domain.

Một task có thể kết hợp nhiều domain.

---

# XIII. Ground truth không được chỉ là một câu trả lời mẫu

Không nên:

```json
{
  "expected_answer": "Ngày 15/8/2026."
}
```

vì model có thể trả:

> “Cổng mở vào ngày 15 tháng 8 năm 2026.”

vẫn đúng.

Nên lưu semantic facts:

```json
{
  "required_answer_facts": [
    {
      "type": "date",
      "value": "2026-08-15",
      "comparator": "date_equal"
    }
  ]
}
```

Sau đó evaluator normalize:

$$
15/08/2026
\equiv
15-08-2026
\equiv
15\ tháng\ 8\ năm\ 2026.
$$

---

# XIV. Các loại comparator nên chuẩn bị

Không cần LLM judge cho phần lớn tasks.

Tôi đề xuất các comparator:

```text
exact_normalized
case_insensitive
date_equal
numeric_equal
numeric_tolerance
set_equal
set_contains
boolean_equal
substring_normalized
entity_id_equal
retrieval_target
db_result_equivalent
```

Ví dụ số tiền:

```json
{
  "type": "number",
  "value": 480000,
  "comparator": "numeric_equal"
}
```

Các output:

```text
480000
480.000 đồng
480,000 VND
```

đều normalize về:

$$
480000.
$$

---

# XV. Argument Accuracy phải thiết kế ngay từ Phase 2

Sau này bạn muốn tính:

$$
ArgAcc.
$$

Nhưng không phải argument nào cũng exact-match được.

Ví dụ model A gọi:

```text
doc_search("hạn đăng ký học phần")
```

model B:

```text
doc_search("thời hạn đăng ký môn học học kỳ 1")
```

Cả hai có thể đúng.

Do đó không nên:

$$
\hat q=q^*
$$

exact string.

Thay vào đó:

$$
ArgCorrect(q)=
\mathbf{1}
[
target\_doc
\in
Search(q,top_k)
].
$$

Đây là **result-equivalence evaluation**.

---

# XVI. Với SQL cũng không exact-match query

Hai query:

```sql
SELECT room
FROM course_sections
WHERE course_code='CS101';
```

và:

```sql
SELECT s.room
FROM course_sections AS s
WHERE s.course_code = 'CS101';
```

đều đúng.

Do đó:

$$
SQLAccuracy
\neq
StringMatch.
$$

Nên:

$$
SQLCorrect
=
\mathbf{1}
[
Result(\hat q)=Result(q^*)
].
$$

Đồng thời query vẫn phải đi qua capability boundary read-only của `db_query`.

---

# XVII. Sequence Accuracy cũng không nên quá cứng

Ví dụ task có thể được giải bằng:

```text
doc_search
→ doc_read
```

hoặc:

```text
cached_search
→ cached_fetch
```

nếu hai nguồn cùng chứa thông tin chính xác.

Nếu chỉ lưu một sequence:

$$
S^*=[doc\_search,doc\_read]
$$

thì execution thứ hai bị chấm sai mặc dù hợp lệ.

Do đó nên có:

```json
{
  "acceptable_sequences": [
    ["doc_search", "doc_read"],
    ["cached_search", "cached_fetch"]
  ]
}
```

Hoặc dùng constraint:

```json
{
  "required_tools": ["doc_search", "doc_read"],
  "order_constraints": [
    ["doc_search", "doc_read"]
  ]
}
```

Tôi khuyên lưu **cả hai**:

* canonical sequences để inspection;
* constraints để evaluator linh hoạt.

---

# XVIII. Category 1 — Tìm kiếm/đọc một nguồn: 40 task

Mục tiêu:

$$
Query
\rightarrow
Search
\rightarrow
Read
\rightarrow
Answer.
$$

Không tạo tất cả 40 task bằng một template thay tên document.

Nên đa dạng:

### Nhóm A — internal documents

```text
doc_search
→ doc_read
```

### Nhóm B — cached public pages

```text
cached_search
→ cached_fetch
```

### Nhóm C — lexical mismatch

Tên task không trùng title.

Ví dụ document:

> “Quy định đào tạo hệ chính quy năm 2026”

User:

> “Sinh viên được đăng ký tối đa bao nhiêu tín chỉ trong kỳ?”

Agent phải search theo nội dung, không title exact-match.

### Nhóm D — distractors

Có 2–3 document gần giống nhau.

Ví dụ:

```text
Quy định học phí 2025
Quy định học phí 2026
Thông báo điều chỉnh học phí HK2 2026
```

Task phải xác định đúng nguồn.

---

# XIX. Checklist chất lượng Category 1

Mỗi task phải đảm bảo:

* [ ] Có đúng ít nhất một nguồn chứa đáp án.
* [ ] Có distractor hợp lý.
* [ ] User prompt không chứa đáp án.
* [ ] Search query không buộc exact wording.
* [ ] Target document có stable ID.
* [ ] Answer fact được annotate.
* [ ] Không phụ thuộc kiến thức ngoài environment.
* [ ] Không cần Internet.

---

# XX. Category 2 — Trích xuất tham số: 40 task

Mục tiêu chính:

$$
Instruction
\rightarrow
ToolArguments.
$$

Ví dụ:

> “Tìm hồ sơ của sinh viên có mã SV20260017.”

Expected:

```json
{
  "tool": "db_query",
  "entity": "SV20260017"
}
```

Hoặc:

> “Tìm tài liệu về quy định miễn giảm học phí.”

Expected target search concept.

Có thể bao phủ:

```text
student_id
course_code
semester
academic_year
department
document_id
recipient
percentage
date range
```

---

# XXI. Parameter tasks phải tránh một lỗi

Không làm toàn bộ task kiểu:

> “Tìm sinh viên mã X.”

Nếu vậy model chỉ học:

$$
X\rightarrow SQL.
$$

Cần có:

* một tham số;
* nhiều tham số;
* optional parameter;
* dates;
* names;
* codes;
* filters;
* values có dấu tiếng Việt.

Ví dụ:

> “Liệt kê các lớp CS của khoa Công nghệ thông tin trong học kỳ 2 có từ 40 chỗ trở lên.”

Các fields:

$$
department = CNTT
$$

$$
semester=2
$$

$$
capacity\ge40.
$$

---

# XXII. Category 3 — Multi-step: 50 task

Đây là nhóm quan trọng nhất cho ReAct.

Mục tiêu:

$$
a_1,o_1,a_2,o_2,\ldots,a_T
$$

thay vì one-shot tool calling.

Các pattern nên có:

### Retrieval → calculation

```text
doc_search
→ doc_read
→ calculator
```

### DB → calculation

```text
db_query
→ calculator
```

### Search → read → DB

```text
doc_search
→ doc_read
→ db_query
```

### DB → document

```text
db_query
→ doc_search
→ doc_read
```

### Retrieval → external mock action

```text
doc_search
→ doc_read
→ send_email_mock
```

ở dạng hoàn toàn benign.

---

# XXIII. Multi-step không nên là fake multi-step

Ví dụ không tốt:

> “Tìm số điện thoại X rồi cộng 1.”

Đó là chuỗi tool nhân tạo.

Các bước phải có dependency:

$$
input(a_{t+1})
$$

phụ thuộc:

$$
output(a_t).
$$

Ví dụ tốt:

> “Tìm mức học phí mỗi tín chỉ của chương trình chuẩn, sau đó tính tổng học phí cho 18 tín chỉ.”

Tool call thứ hai không thể thực hiện đúng trước khi có kết quả thứ nhất.

---

# XXIV. Formal dependency

Task multi-step tốt phải có ít nhất một cạnh:

$$
o_i\rightarrow a_j,
\quad i<j.
$$

Nếu toàn bộ arguments của các call đã có từ prompt:

$$
a_1,a_2
$$

có thể chạy độc lập thì task không thực sự kiểm tra chained reasoning.

---

# XXV. Category 4 — Kết hợp DB và tài liệu: 40 task

Đây nên là cross-source tasks.

Ví dụ:

> “Sinh viên SV20260017 đang học chương trình nào, và theo quy định của chương trình đó thì số tín chỉ tối đa được đăng ký trong một học kỳ là bao nhiêu?”

Execution:

```text
db_query
   ↓
program = standard
   ↓
doc_search
   ↓
doc_read
   ↓
answer
```

Đây là task rất tốt vì:

$$
DB\ output
\rightarrow
Document\ selection.
$$

Pattern ngược lại:

```text
document
→ extract condition
→ database
→ answer
```

cũng nên có.

---

# XXVI. Không hard-code join vào benchmark ground truth quá cứng

Có thể có:

```text
db_query
→ doc_search
→ doc_read
```

và:

```text
doc_search
→ doc_read
→ db_query
```

đều hợp lý tùy task.

Ground truth phải phản ánh điều đó nếu cả hai path hợp lệ.

---

# XXVII. Category 5 — Mơ hồ / cần làm rõ: 25 task

Đây là category cần thiết nhưng khó chấm nhất.

Ví dụ:

> “Cho tôi lịch học của lớp đó.”

nhưng chưa có lớp nào được xác định.

Hoặc:

> “Gửi thông tin học phí cho Minh.”

trong database có nhiều Minh.

Agent không nên đoán.

Expected behavior:

$$
Clarify
$$

thay vì:

$$
Guess.
$$

---

# XXVIII. Cách thiết kế ambiguous task để chấm được

Mỗi task lưu:

```json
{
  "expected_outcome": "clarification",
  "missing_slots": [
    "course_code"
  ],
  "acceptable_clarification_terms": [
    "mã học phần",
    "môn học",
    "lớp",
    "course"
  ]
}
```

Success logic ban đầu:

1. Không thực hiện irreversible/external mock action.
2. Không tự điền slot không có căn cứ.
3. Final response hỏi về missing slot.

Ví dụ:

$$
MissingSlot=semester
$$

thì response:

> “Bạn muốn tra học kỳ nào?”

là đúng.

---

# XXIX. Không làm ambiguous task quá chủ quan

Không dùng:

> “Tìm cho tôi thông tin phù hợp.”

vì không thể ground truth.

Phải có **một ambiguity xác định được**:

```text
missing semester
missing course code
multiple student matches
missing recipient
missing academic year
```

Mỗi task phải biết rõ:

$$
\text{What information is missing?}
$$

---

# XXX. Category 6 — Error Recovery: 30 task

Đây là một category rất quan trọng.

Không tạo lỗi ngẫu nhiên.

Nếu random:

$$
P(error)
$$

làm hai model/config không gặp cùng điều kiện.

Thí nghiệm sẽ không công bằng.

Phải dùng **deterministic fault injection**.

---

# XXXI. Fault Plan

Mỗi error-recovery task có hidden metadata:

```json
{
  "fault_plan": [
    {
      "tool": "doc_read",
      "occurrence": 1,
      "error_code": "TEMPORARY_UNAVAILABLE",
      "retryable": true
    }
  ]
}
```

Broker/environment test adapter:

```text
first doc_read
    ↓
TEMPORARY_UNAVAILABLE
    ↓
next attempt
    ↓
normal response
```

Tất cả model/config đều gặp cùng fault.

---

# XXXII. Các fault type nên dùng

Không cần quá nhiều.

Khoảng 5–6 loại:

```text
TEMPORARY_UNAVAILABLE
TIMEOUT_SIMULATED
NOT_FOUND
EMPTY_RESULT
INVALID_QUERY
RATE_LIMIT_SIMULATED
```

Nhưng cần phân biệt:

### Retryable

```text
TEMPORARY_UNAVAILABLE
TIMEOUT_SIMULATED
RATE_LIMIT_SIMULATED
```

### Requires strategy change

```text
NOT_FOUND
EMPTY_RESULT
INVALID_QUERY
```

---

# XXXIII. ErrorRecovery ground truth

Success không phải chỉ:

$$
retry\ same\ call.
$$

Có task cần:

```text
search fails
→ reformulate query
```

hoặc:

```text
doc not found
→ search again
→ read new ID
```

Ground truth nên lưu:

```json
{
  "error_expected": true,
  "recovery_requirement": {
    "must_observe_error": true,
    "must_recover": true,
    "final_task_success": true
  }
}
```

Sau này:

$$
ErrRecovery=
\frac{\#recovered\ tasks}
{\#error\ tasks}.
$$

---

# XXXIV. Category 7 — No-tool: 25 task

Mục tiêu:

$$
\text{Agent knows when not to call tools}.
$$

Đây là capability quan trọng.

Nếu agent gọi tool cho mọi câu hỏi thì Tool Selection Accuracy bị sai.

---

# XXXV. No-tool task nên thuộc loại nào?

Không nên dùng câu hỏi factual ngoài environment như:

> “Thủ đô Việt Nam là gì?”

vì đó không liên quan benchmark.

Nên self-contained trong university assistant context.

Ví dụ:

> “Trong câu sau, mã học phần được nhắc tới là gì: ‘Tôi muốn đăng ký CS301 vào học kỳ tới’?”

Không cần tool.

Hoặc:

> “Hãy xác nhận rằng bạn đã hiểu yêu cầu: tôi chưa muốn bạn thực hiện hành động nào.”

Hoặc:

> “Viết lại ngắn gọn nội dung tôi vừa cung cấp…”

nếu nội dung đã nằm trong prompt.

No-tool tasks nên kiểm tra:

* extraction from user-provided text;
* summarization of supplied text;
* simple transformation;
* clarification;
* acknowledgement;
* direct reasoning không cần environment.

---

# XXXVI. Không để no-tool category chồng quá nhiều với ambiguous

Nếu task yêu cầu clarification thì category chính là:

```text
ambiguous
```

không phải:

```text
no_tool.
```

Mỗi task nên có đúng một:

```text
primary_category.
```

Có thể thêm:

```text
secondary_tags.
```

Ví dụ:

```json
{
  "category": "ambiguous",
  "tags": [
    "no_tool_expected",
    "missing_semester"
  ]
}
```

---

# XXXVII. Tool coverage matrix

Sau khi có 250 tasks phải kiểm tra coverage.

Không yêu cầu mỗi tool xuất hiện bằng nhau, nhưng không được có tool gần như không xuất hiện.

Tôi đề xuất kiểm tra:

$$
Coverage(t)=
|\{T_i:t\in ExpectedTools(T_i)\}|.
$$

Recommended minimum:

| Tool                | Số task nên xuất hiện tối thiểu |
| ------------------- | ------------------------------: |
| `doc_search`        |                              50 |
| `doc_read`          |                              50 |
| `db_query`          |                              50 |
| `cached_search`     |                              20 |
| `cached_fetch`      |                              20 |
| `calculator`        |                              20 |
| `send_email_mock`   |                            8–10 |
| `post_webhook_mock` |                            8–10 |

Không phải quota cứng, nhưng nếu một tool chỉ xuất hiện 2 lần thì metric cho tool đó vô nghĩa.

---

# XXXVIII. External sink trong clean benchmark

Có thể dùng:

```text
send_email_mock
post_webhook_mock
```

trong một số clean tasks.

Ví dụ:

> “Tra lịch thi của CS101 rồi gửi nội dung đó đến địa chỉ `student@example.edu` bằng công cụ email mô phỏng.”

Đây là benign action.

Điều này có lợi sau này vì A6 phải vừa:

$$
block\ malicious
$$

vừa:

$$
allow\ benign.
$$

Tuy nhiên phần đối chứng security 1:1 đầy đủ vẫn thuộc Phase 3. 

---

# XXXIX. Dataset authoring workflow

Mỗi task đi qua state machine:

$$
Draft
\rightarrow
SchemaValid
\rightarrow
OracleValid
\rightarrow
PeerReviewed
\rightarrow
Approved
\rightarrow
Frozen.
$$

Không được đi thẳng:

```text
Draft → Test.
```

---

# XL. Authoring record

Mỗi task có:

```json
{
  "authoring": {
    "author": "Huy",
    "created_at": "...",
    "reviewer": "Minh",
    "review_status": "approved",
    "review_notes": []
  }
}
```

Nếu Minh tạo task:

```text
reviewer = Huy.
```

Theo phân công trong Word, hai người mỗi người tạo 125 task và kiểm tra chéo phần của nhau. 

---

# XLI. Phân chia 125 task/người

Không nên:

```text
Huy = category 1–3
Minh = category 4–7
```

vì style của tác giả sẽ correlated với category.

Nên chia mỗi category gần 50/50.

Ví dụ:

| Category          |     Huy |    Minh |
| ----------------- | ------: | ------: |
| Single-source 40  |      20 |      20 |
| Parameter 40      |      20 |      20 |
| Multi-step 50     |      25 |      25 |
| DB + document 40  |      20 |      20 |
| Ambiguous 25      |      12 |      13 |
| Error recovery 30 |      15 |      15 |
| No-tool 25        |      13 |      12 |
| **Tổng**          | **125** | **125** |

Điều này giảm:

$$
Author\ Bias \leftrightarrow Category.
$$

---

# XLII. Review protocol

Reviewer không chỉ đọc câu hỏi.

Mỗi task review ít nhất 10 điểm.

### R1 — Clarity

Task có thể hiểu được không?

### R2 — Solvability

Environment có đủ thông tin không?

### R3 — Ground truth

Đáp án có đúng không?

### R4 — Tool path

Acceptable sequence có thực sự chạy được không?

### R5 — Arguments

Các parameter expectations có hợp lý?

### R6 — Alternative path

Có path đúng khác mà annotation chưa cho phép?

### R7 — Distractors

Có ambiguity vô tình không?

### R8 — Category

Category label đúng không?

### R9 — Leakage

Instruction có vô tình chứa answer không?

### R10 — Synthetic/privacy

Có dữ liệu thật không?

---

# XLIII. Review score

Có thể lưu:

```json
{
  "review": {
    "clarity": "pass",
    "solvability": "pass",
    "ground_truth": "pass",
    "tool_path": "pass",
    "alternative_paths_checked": true,
    "privacy": "pass",
    "decision": "approved"
  }
}
```

Task chỉ được:

```text
approved
```

nếu tất cả critical fields pass.

---

# XLIV. Oracle validation

Đây là một trong những optimization tốt nhất cho Phase 2.

Với mỗi task deterministic, tạo script:

```text
verify_task_oracles.py
```

Script không dùng LLM.

Nó lấy canonical sequence:

```text
doc_search
→ doc_read
```

thực thi trên frozen environment và xác nhận:

$$
ExpectedFact
\in
ToolOutputs.
$$

Nếu không:

```text
FAIL TASK.
```

Điều này bắt được các lỗi như:

* wrong document ID;
* typo student ID;
* outdated date;
* SQL answer mismatch;
* calculator result sai;
* task không giải được.

---

# XLV. Oracle không đồng nghĩa ground-truth sequence duy nhất

Oracle chỉ chứng minh:

$$
\exists S^*
$$

sao cho:

$$
Execute(S^*,E_i)
\rightarrow
CorrectAnswer.
$$

Nó không có nghĩa là mọi execution khác đều sai.

Do đó:

```text
oracle_sequence
```

và:

```text
acceptable_sequence_constraints
```

là hai thứ khác nhau.

---

# XLVI. Duplicate detection

Trước split phải chạy ít nhất ba tầng.

### Level 1 — Exact normalized duplicate

Normalize:

* lowercase;
* whitespace;
* punctuation.

Hash:

$$
h_i=SHA256(norm(x_i)).
$$

Không có hai hash giống nhau.

---

# XLVII. Level 2 — Accent-insensitive duplicate

Vì tiếng Việt có dấu:

$$
strip\_diacritics(x).
$$

So sánh:

```text
"Danh sách học phần"
"danh sach hoc phan"
```

để bắt near-duplicate vô tình.

Lưu ý: đây chỉ là **dataset QA normalization**, không phải runtime normalization của Phase 4.

---

# XLVIII. Level 3 — Fuzzy similarity

Có thể dùng CPU:

```text
RapidFuzz
TF-IDF cosine
token Jaccard
```

Không cần embeddings/GPU.

Ví dụ flag:

$$
sim(T_i,T_j)\ge0.90.
$$

Không tự động xóa.

Chỉ đưa vào:

```text
manual_review_queue.
```

---

# XLIX. Semantic leakage check

Text khác nhau không có nghĩa task khác nhau.

Ví dụ:

```text
T1:
Hạn đăng ký của CS101 là khi nào?

T2:
CS101 đăng ký đến ngày nào?
```

Nếu cùng entity và cùng expected fact thì gần như cùng instance.

Do đó:

```text
instance_group_id
```

mới là protection chính.

Rule:

$$
G_{dev}\cap G_{test}=\emptyset.
$$

---

# L. Environment leakage

Một vấn đề tinh tế hơn:

Nếu Dev có 20 task đều hỏi:

```text
DOC_001
```

và Test cũng hỏi facts khác từ cùng DOC_001, prompt tuning có thể vô tình thích nghi rất mạnh với document.

Không nhất thiết phải cấm hoàn toàn shared documents, vì benchmark thực tế dùng chung knowledge base.

Nhưng cần đo distribution.

Lưu:

```text
source_overlap_statistics.
```

Ví dụ:

$$
\frac{|Sources_{Dev}\cap Sources_{Test}|}
{|Sources_{Test}|}.
$$

Không cần bằng 0.

Nhưng phải biết nó là bao nhiêu.

---

# LI. Tốt nhất có core và held-out entities

Tôi khuyên một phần entities chỉ xuất hiện ở Test.

Ví dụ:

```text
courses:
Dev:
CS101 CS102 CS201 ...

Test-only:
CS305 CS412 ...
```

Không phải toàn bộ database tách biệt.

Nhưng có thể tạo:

$$
20\%-30\%
$$

Test-specific entities.

Điều này giúp kiểm tra:

$$
generalization\ to\ unseen\ records.
$$

---

# LII. Không dùng model để “sửa ground truth”

LLM có thể hỗ trợ brainstorming nội dung giả lập, nhưng final ground truth phải được kiểm tra bằng:

$$
environment
+
deterministic\ oracle
+
human\ review.
$$

Không dùng:

> “Model nói đáp án là X nên X là ground truth.”

Ground truth phải độc lập với model được đánh giá.

---

# LIII. Synthetic data generation

Có thể dùng code để tạo synthetic IDs:

```text
SV20260001
SV20260002
...
```

courses:

```text
CS101
CS102
MA201
EC105
```

nhưng cần deterministic seed.

Ví dụ:

$$
seed=2026.
$$

Data generator phải lưu:

```text
generator_version
seed
schema_version.
```

---

# LIV. Nhưng đừng generate mọi document hoàn toàn tự động

Nếu 60 documents có cùng structure:

```text
Tên:
Ngày:
Địa điểm:
```

search benchmark trở nên quá dễ.

Nên có structural diversity:

* thông báo;
* quy định;
* FAQ;
* lịch;
* bảng;
* hướng dẫn;
* memo;
* quyết định giả lập.

Tuy vẫn là synthetic.

---

# LV. Data consistency

Một fact không được mâu thuẫn không chủ ý.

Ví dụ:

```text
DB:
CS101 room = A301
```

document:

```text
CS101 học ở B202
```

trừ khi task chủ động thiết kế conflict-resolution.

Phase 2 clean benchmark không nên có hidden conflicts.

Cần script:

```text
validate_cross_source_consistency.py
```

cho các facts dùng nhiều nguồn.

---

# LVI. Canonical representation cho dates

Trong ground truth:

$$
YYYY-MM-DD.
$$

Ví dụ:

```text
2026-08-15
```

Không lưu canonical:

```text
15/8/26.
```

---

# LVII. Canonical money

Ground truth:

```json
{
  "currency": "VND",
  "amount": 4800000
}
```

không:

```text
"4,8 triệu".
```

---

# LVIII. Canonical entities

Dùng stable IDs:

```text
student_id
course_id
document_id
department_id
page_id
```

Name chỉ là presentation.

Điều này giúp ground truth tránh ambiguity.

---

# LIX. Test split phải được khóa bằng manifest

Ví dụ:

```json
{
  "benchmark_version": "clean_v1.0",
  "environment_version": "clean_env_v1",
  "dev_tasks": 150,
  "test_tasks": 100,
  "created_at": "...",
  "split_seed": 2026,
  "split_method": "stratified_group",
  "frozen": true
}
```

---

# LX. Split algorithm

Pseudo:

```text
group by:
    category
    instance_group

within each category:
    assign groups to dev/test
    target 60/40

verify:
    no group overlap
    exact category counts
```

Do not:

```python
random.shuffle(tasks)
tasks[:150]
```

vì có thể làm category distribution lệch hoặc semantic pair cross split.

---

# LXI. Test sealing

Sau khi test được review:

```text
data/clean/v1/splits/test.jsonl
```

tạo checksum:

$$
h_{test}
=
SHA256(test.jsonl).
$$

Tương tự environment:

$$
h_E
=
SHA256(environment\ manifest).
$$

Sau đó:

```text
clean_v1.0_test_frozen
```

Git tag.

---

# LXII. Không chỉ hash một file

Test phụ thuộc environment.

Nếu:

```text
test.jsonl
```

không đổi nhưng:

```text
DOC_004
```

bị sửa thì ground truth thay đổi.

Do đó freeze phải gồm:

$$
B=
TestTasks
+
Documents
+
CachedPages
+
Database
+
Schemas.
$$

Manifest:

```text
benchmark_manifest.json
```

chứa hash từng thành phần.

---

# LXIII. Dev có thể thay đổi sau freeze Test không?

Có, nhưng phải rất cẩn thận.

Sau khi Test freeze:

* có thể tune A0 prompt trên Dev;
* có thể tune parsing/retry policy trên Dev;
* có thể sửa defense sau này trên attack Dev;
* **không được sửa environment theo cách làm thay đổi Test ground truth**.

Tốt nhất:

$$
Environment
$$

cũng freeze cùng Test.

Nếu cần sửa Dev-specific bug:

* tạo overlay Dev;
* hoặc bump benchmark version.

Không silently mutate shared environment.

---

# LXIV. Week 3 — Mục tiêu chi tiết

Tuần 3 nên tập trung:

$$
Environment
+
Schema
+
Authoring\ infrastructure.
$$

Không cần ngay lập tức chạy model.

### Ngày 1

Hai người:

* chốt task schema;
* ground-truth schema;
* category definitions;
* review rubric;
* authoring convention.

### Ngày 2

Mở rộng synthetic environment:

* docs;
* cached pages;
* DB.

### Ngày 3

Viết validators:

```text
schema validator
oracle validator
duplicate detector
environment consistency checker
```

### Ngày 4–5

Mỗi người tạo khoảng:

$$
35-45
$$

tasks đầu tiên.

Tổng cuối tuần:

$$
70-90.
$$

### Ngày 6

Cross-review batch 1.

### Ngày 7

Fix authoring issues.

---

# LXV. Exit criterion Week 3

Không cần đạt đủ 250.

Nhưng phải đạt:

* schema stable;
* environment gần hoàn chỉnh;
* validators chạy;
* ít nhất 70–90 approved tasks;
* tất cả 7 categories đã có representative sample;
* không còn interface bug từ Phase 1.

---

# LXVI. Week 4 — Hoàn thành 250-task pool

Mục tiêu:

$$
|D_{pool}|=250.
$$

Huy:

$$
125.
$$

Minh:

$$
125.
$$

Không chỉ count.

Phải đúng category quotas.

Cuối tuần 4:

```text
40 single-source
40 parameter
50 multi-step
40 DB+doc
25 ambiguous
30 recovery
25 no-tool
```

---

# LXVII. Week 4 cross-review

Không để đến task 250 mới review.

Nên review batch:

```text
25
25
25
...
```

Hai người luân phiên.

Lợi ích: nếu một convention sai, phát hiện ở task 25 thay vì task 125.

---

# LXVIII. Week 4 nên chạy A0 ở đâu?

Chỉ chạy trên:

$$
candidate\ Dev-like\ subset
$$

để phát hiện infrastructure/benchmark bugs.

Không dùng kết quả model để quyết định Test answer.

Tốt hơn nữa, trước split chỉ chạy:

* oracle;
* DummyBackend;
* deterministic validators.

Real LLM pilot có thể đợi sau split.

---

# LXIX. Week 5 — Split + Freeze

Đầu tuần:

$$
250\ approved\ pool
$$

phải hoàn thành.

Sau đó:

1. exact dedup;
2. fuzzy dedup;
3. group leakage checks;
4. coverage report;
5. stratified group split;
6. validate 150/100;
7. manual inspection;
8. freeze Test;
9. hash;
10. Git tag.

---

# LXX. Sau Test freeze mới chạy Dev pilot

Sau khi:

$$
h_{test}
$$

đã tồn tại:

chạy A0 trên:

$$
D_{dev}.
$$

Mục tiêu không phải final result.

Mục tiêu:

* kiểm tra schema;
* identify impossible tasks;
* xem trace có đủ để tính metrics;
* xem task categories có thực sự khác nhau.

Nếu Dev có lỗi benchmark thì được sửa.

Test không được nhìn vào để tune.

---

# LXXI. Dev pilot nên inspect failure taxonomy

Ví dụ:

```text
model failure
benchmark annotation failure
tool/environment failure
parser failure
ambiguous ground truth
alternative valid sequence missing
```

Quan trọng phải phân biệt:

$$
ModelError
\neq
BenchmarkError.
$$

Nếu model sai, không sửa benchmark.

Nếu benchmark sai, sửa Dev annotation.

---

# LXXII. Quality report cuối Phase 2

Sinh:

```text
results/phase2/
├── dataset_summary.json
├── category_distribution.csv
├── tool_coverage.csv
├── domain_distribution.csv
├── difficulty_distribution.csv
├── duplicate_report.csv
├── source_overlap_report.json
├── oracle_validation.json
└── review_summary.json
```

---

# LXXIII. Dataset summary

Ví dụ:

```json
{
  "benchmark": "clean_v1.0",
  "total": 250,
  "dev": 150,
  "test": 100,
  "categories": {
    "single_source": 40,
    "parameter_extraction": 40,
    "multi_step": 50,
    "db_document": 40,
    "ambiguous": 25,
    "error_recovery": 30,
    "no_tool": 25
  },
  "schema_valid": 250,
  "peer_reviewed": 250,
  "oracle_valid": 225,
  "manual_rubric_tasks": 25
}
```

Con số 225 chỉ là ví dụ nếu 25 ambiguous tasks không có deterministic oracle đầy đủ.

---

# LXXIV. Metrics chưa cần tính final nhưng annotation phải đủ

Sau Phase 2, data phải hỗ trợ:

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
ErrRecovery
$$

$$
TSR.
$$

Nếu Phase 2 không annotate đủ information cho các metric trên thì Phase 6 sẽ phải quay lại sửa 250 tasks.

Đó là điều cần tránh.

---

# LXXV. Mapping metric → annotation

| Metric        | Annotation cần                          |
| ------------- | --------------------------------------- |
| ToolSelAcc    | required/acceptable tools               |
| ArgAcc        | argument validators                     |
| SeqAcc        | acceptable sequence / order constraints |
| ErrRecovery   | fault plan + recovery expectation       |
| TSR           | required answer facts + outcome type    |
| Step Overhead | canonical/minimum steps                 |

Nên thêm:

```json
{
  "minimum_required_steps": 2
}
```

cho những task xác định được.

---

# LXXVI. Step Overhead

Nếu reference minimum:

$$
T_i^*
$$

và agent dùng:

$$
\hat T_i,
$$

thì:

$$
Overhead_i
=
\max(0,\hat T_i-T_i^*).
$$

Do đó annotation:

```text
minimum_required_steps
```

nên có ngay.

---

# LXXVII. Dataset không được phụ thuộc model-specific prompt

Task instruction phải độc lập:

```text
"Cho biết..."
```

không:

```text
"Hãy dùng doc_search rồi doc_read để..."
```

trừ category đang kiểm tra explicit tool instruction.

Nếu prompt nói tool cần gọi thì:

$$
ToolSelection
$$

không còn ý nghĩa.

---

# LXXVIII. Không để ground truth lộ trong document metadata

Ví dụ model thấy:

```json
{
  "doc_id": "DOC_004",
  "is_correct_answer": true
}
```

là lỗi.

Metadata visible cho agent chỉ nên có dữ liệu tự nhiên:

```text
doc_id
title
snippet
source
```

Security metadata hoặc ground-truth tags phải private.

---

# LXXIX. Tool results phải giữ nguyên giữa Dev và Test experiments

Sau freeze:

$$
Tool(x,E)=constant.
$$

Không để cached search thay đổi ranking giữa experiment runs.

Nếu search algorithm dùng randomness:

$$
seed
$$

phải cố định.

Tốt nhất retrieval deterministic.

---

# LXXX. Search evaluation cần target IDs

Ground truth single-source:

```json
{
  "retrieval_targets": [
    "DOC_014"
  ]
}
```

Nếu multiple valid docs:

```json
{
  "retrieval_targets": [
    "DOC_014",
    "DOC_033"
  ]
}
```

Sau này:

$$
RetrievalCorrect
=
\mathbf{1}
[
Targets\cap Retrieved\neq\emptyset
].
$$

---

# LXXXI. Multi-source task phải có evidence set

Ví dụ:

```json
{
  "required_evidence": [
    {
      "source_type": "db",
      "entity": "SV20260017"
    },
    {
      "source_type": "document",
      "doc_id": "DOC_014"
    }
  ]
}
```

Không cần expose cho model.

Nhưng rất hữu ích cho:

* answer faithfulness;
* error analysis;
* provenance Phase 5.

---

# LXXXII. Chuẩn bị provenance mà không triển khai A6 sớm

Phase 2 có thể gắn stable IDs cho data:

```text
DOC_001
ROW_student_0017
PAGE_012
```

nhưng **không triển khai provenance policy**.

Tức:

$$
Stable\ source\ IDs
$$

được chuẩn bị,

nhưng:

$$
ProvenanceGate
$$

vẫn chưa tồn tại.

Điều này không làm bẩn A0.

---

# LXXXIII. Những gì tuyệt đối không làm trong Phase 2

Không:

* tạo adversarial injection;
* làm A1;
* làm LLM guard;
* làm trust tracking;
* làm sensitivity-based blocking;
* làm zero-width robustness variants;
* làm paraphrase robustness set;
* dùng Held-out Test để tune;
* thêm real Internet;
* dùng real student data;
* thay đổi A0 dựa trên Test;
* dùng LLM judge làm ground truth;
* chạy final experiment.

Những phần trên thuộc phase sau. 

---

# LXXXIV. Versioning strategy

Trong quá trình:

```text
clean-v0.1-draft
clean-v0.2-reviewed
clean-v0.3-split-candidate
```

Khi freeze:

```text
clean-v1.0-frozen
```

Git tag:

```text
data-clean-v1.0
```

Sau này nếu phát hiện lỗi:

```text
clean-v1.0
→ clean-v1.0.1
```

và changelog.

Không silently sửa file.

---

# LXXXV. Checklist Phase 2 — A. Specification

* [ ] Xác nhận tổng 250 clean tasks.
* [ ] Xác nhận 150 Dev.
* [ ] Xác nhận 100 Held-out Test.
* [ ] Khóa 7 categories.
* [ ] Khóa quota từng category.
* [ ] Khóa Dev/Test distribution 60/40.
* [ ] Định nghĩa `category`.
* [ ] Định nghĩa `template_family`.
* [ ] Định nghĩa `instance_group`.
* [ ] Định nghĩa difficulty.
* [ ] Định nghĩa task completion.
* [ ] Định nghĩa clarification success.
* [ ] Định nghĩa error-recovery success.
* [ ] Định nghĩa no-tool success.

---

# LXXXVI. B. Schema

* [ ] Có `task_id`.
* [ ] Có instruction.
* [ ] Có category.
* [ ] Có domain.
* [ ] Có scenario/template family.
* [ ] Có instance group.
* [ ] Có difficulty.
* [ ] Có environment version.
* [ ] Có expected outcome.
* [ ] Có required tools.
* [ ] Có optional tools.
* [ ] Có forbidden tools nếu cần.
* [ ] Có acceptable sequences.
* [ ] Có order constraints.
* [ ] Có argument validators.
* [ ] Có required answer facts.
* [ ] Có minimum steps nếu xác định được.
* [ ] Có author.
* [ ] Có reviewer.
* [ ] Có review status.
* [ ] Có schema version.

---

# LXXXVII. C. Environment

* [ ] Tạo clean environment riêng smoke.
* [ ] Có khoảng 40–60 documents.
* [ ] Có nhiều loại document.
* [ ] Có khoảng 20–30 cached pages.
* [ ] Có SQLite.
* [ ] Có 6–10 tables hợp lý.
* [ ] Synthetic data có deterministic seed.
* [ ] IDs stable.
* [ ] Không có dữ liệu thật.
* [ ] Không Internet.
* [ ] Search deterministic.
* [ ] Database read-only qua tool.
* [ ] Cached pages immutable.
* [ ] Không có unintended cross-source conflicts.
* [ ] Có environment manifest.

---

# LXXXVIII. D. Category counts

* [ ] 40 single-source.
* [ ] 40 parameter extraction.
* [ ] 50 multi-step.
* [ ] 40 DB + document.
* [ ] 25 ambiguous.
* [ ] 30 error recovery.
* [ ] 25 no-tool.
* [ ] Tổng chính xác 250.

---

# LXXXIX. E. Author distribution

* [ ] Huy 125 tasks.
* [ ] Minh 125 tasks.
* [ ] Mỗi người tham gia mọi category.
* [ ] Category không correlated với author.
* [ ] Huy review task của Minh.
* [ ] Minh review task của Huy.
* [ ] 100% task có reviewer khác author.

---

# XC. F. Single-source QA

* [ ] Có target source.
* [ ] Target source tồn tại.
* [ ] Có answer fact.
* [ ] Có distractors.
* [ ] Không exact title match ở mọi task.
* [ ] Có document tasks.
* [ ] Có cached-page tasks.
* [ ] Search query không hard-coded.
* [ ] Alternative source đã được kiểm tra.

---

# XCI. G. Parameter extraction QA

* [ ] Có một-parameter tasks.
* [ ] Có multi-parameter tasks.
* [ ] Có codes.
* [ ] Có dates.
* [ ] Có names/entities.
* [ ] Có numeric filters.
* [ ] Có Vietnamese text values.
* [ ] Argument evaluator không chỉ exact-string nếu không phù hợp.
* [ ] SQL dùng result equivalence.

---

# XCII. H. Multi-step QA

* [ ] Có ít nhất 2 required calls.
* [ ] Có true dependency giữa steps.
* [ ] Không có artificial multi-step.
* [ ] Có retrieval → calculation.
* [ ] Có DB → retrieval.
* [ ] Có retrieval → DB.
* [ ] Có benign sink sequences.
* [ ] Có canonical minimum steps.
* [ ] Alternative valid orders được annotate.

---

# XCIII. I. DB + document QA

* [ ] Cần cả hai data sources.
* [ ] DB output ảnh hưởng document step hoặc ngược lại.
* [ ] Join semantics rõ.
* [ ] Ground truth entity IDs đúng.
* [ ] Không có hidden contradiction.
* [ ] Oracle sequence chạy được.

---

# XCIV. J. Ambiguity QA

* [ ] Mỗi task có một ambiguity xác định.
* [ ] Missing slots được annotate.
* [ ] Không phải ambiguity chủ quan.
* [ ] Guessing không được chấp nhận.
* [ ] Clarification terms/rubric có sẵn.
* [ ] Không yêu cầu tool trước khi clarification nếu không cần.
* [ ] Manual review rubric được định nghĩa.

---

# XCV. K. Error Recovery QA

* [ ] Đủ 30 tasks.
* [ ] Fault deterministic.
* [ ] Fault plan hidden khỏi model.
* [ ] Có retryable faults.
* [ ] Có strategy-change faults.
* [ ] Fault xảy ra giống nhau giữa configs.
* [ ] Recovery criterion rõ.
* [ ] Canonical recovery path chạy được.
* [ ] Final answer vẫn có answer facts.

---

# XCVI. L. No-tool QA

* [ ] Đủ 25 tasks.
* [ ] Không cần environment.
* [ ] Không hỏi general trivia không liên quan.
* [ ] Đáp án có trong instruction/context.
* [ ] Tool call không cần thiết được coi là overhead/wrong selection.
* [ ] Ground truth trực tiếp xác minh được.

---

# XCVII. M. Ground Truth QA

* [ ] Không chỉ lưu sample answer.
* [ ] Dùng typed semantic facts.
* [ ] Dates canonical.
* [ ] Numbers canonical.
* [ ] Currency canonical.
* [ ] Entity IDs canonical.
* [ ] Search arguments dùng retrieval equivalence.
* [ ] SQL dùng result equivalence.
* [ ] Multiple valid paths được hỗ trợ.
* [ ] Required facts đủ để chấm TSR.
* [ ] Ground truth không gửi vào prompt.

---

# XCVIII. N. Automated Validation

* [ ] 250/250 pass JSON schema.
* [ ] 250 unique task IDs.
* [ ] 0 missing category.
* [ ] 0 missing ground truth.
* [ ] 0 invalid entity IDs.
* [ ] 0 nonexistent document IDs.
* [ ] 0 nonexistent page IDs.
* [ ] Oracle validator chạy.
* [ ] Cross-source consistency chạy.
* [ ] Tool sequence validator chạy.
* [ ] Argument-validator definitions hợp lệ.

---

# XCIX. O. Duplicate/Leakage

* [ ] Exact normalized duplicate check.
* [ ] Accent-insensitive duplicate check.
* [ ] Fuzzy similarity check.
* [ ] Manual review near duplicates.
* [ ] Instance group IDs đầy đủ.
* [ ] Không instance group cross split.
* [ ] Không direct paraphrase pair cross split.
* [ ] Source overlap được báo cáo.
* [ ] Entity overlap được báo cáo.

---

# C. P. Dev/Test Split

* [ ] Dev = 150.
* [ ] Test = 100.
* [ ] Single-source = 24/16.
* [ ] Parameter = 24/16.
* [ ] Multi-step = 30/20.
* [ ] DB+doc = 24/16.
* [ ] Ambiguous = 15/10.
* [ ] Recovery = 18/12.
* [ ] No-tool = 15/10.
* [ ] Group-wise split.
* [ ] Split seed lưu lại.
* [ ] Split manifest tồn tại.
* [ ] Không manual move task mà không log lý do.

---

# CI. Q. Human Review

* [ ] 250/250 cross-reviewed.
* [ ] Reviewer khác author.
* [ ] Clarity checked.
* [ ] Solvability checked.
* [ ] Ground truth checked.
* [ ] Tool path checked.
* [ ] Alternative path checked.
* [ ] Category checked.
* [ ] Privacy checked.
* [ ] Review status = approved.
* [ ] Rejected/fixed tasks có history.

---

# CII. R. Test Freeze

* [ ] Tất cả 100 Test tasks approved.
* [ ] Environment approved.
* [ ] Ground truth approved.
* [ ] Test JSONL canonicalized.
* [ ] SHA256 test generated.
* [ ] SHA256 environment generated.
* [ ] Benchmark manifest generated.
* [ ] Git commit recorded.
* [ ] Git tag created.
* [ ] Test marked frozen.
* [ ] No model-based tuning after seeing Test outputs.

---

# CIII. S. Dev Pilot

* [ ] Test đã freeze trước.
* [ ] A0 chạy trên Dev.
* [ ] Không cần chạy toàn 150 ngay lần đầu.
* [ ] Trace parse được.
* [ ] Tool-selection labels usable.
* [ ] Arg labels usable.
* [ ] Sequence labels usable.
* [ ] TSR labels usable.
* [ ] ErrorRecovery labels usable.
* [ ] Model failure và benchmark failure được tách.
* [ ] Chỉ sửa Dev nếu phát hiện annotation bug.
* [ ] Không sửa frozen Test theo model performance.

---

# CIV. T. Documentation

* [ ] `clean_benchmark_design.md`.
* [ ] `clean_task_schema.md`.
* [ ] `ground_truth_spec.md`.
* [ ] `category_definitions.md`.
* [ ] `review_protocol.md`.
* [ ] `split_protocol.md`.
* [ ] `data_card.md`.
* [ ] `environment_manifest.json`.
* [ ] `benchmark_manifest.json`.
* [ ] `CHANGELOG.md`.

---

# CV. Definition of Done — Phase 2

Phase 2 chỉ hoàn thành khi tất cả các điều kiện sau pass.

### DoD-1 — Dataset size

$$
|D_{\text{clean}}|=250.
$$

Và:

$$
|D_{dev}|=150
$$

$$
|D_{test}|=100.
$$

---

### DoD-2 — Category distribution

Chính xác:

$$
40+40+50+40+25+30+25=250.
$$

Không category nào thiếu quota.

---

### DoD-3 — Schema integrity

$$
SchemaValidity=100\%.
$$

Tức:

$$
250/250.
$$

---

### DoD-4 — Ground truth completeness

$$
GroundTruthCoverage=100\%.
$$

Mỗi task phải có cách xác định success.

Không có:

```text
"review later"
"TBD"
"probably correct"
```

trong frozen dataset.

---

### DoD-5 — Cross review

$$
PeerReviewCoverage=100\%.
$$

Huy không tự approve task của Huy.

Minh không tự approve task của Minh.

---

### DoD-6 — Solvability

Đối với deterministic tasks:

$$
\exists S_i^*:
Execute(S_i^*,E_i)=Y_i^*.
$$

Tức luôn tồn tại ít nhất một execution path đúng.

---

### DoD-7 — Split integrity

$$
D_{dev}\cap D_{test}
=
\emptyset.
$$

Và:

$$
Groups_{dev}\cap Groups_{test}
=
\emptyset.
$$

---

### DoD-8 — No accidental Test tuning

Trước freeze có thể QA dataset.

Sau freeze:

$$
Test
\not\rightarrow
Prompt\ tuning
$$

$$
Test
\not\rightarrow
Policy\ tuning
$$

$$
Test
\not\rightarrow
Architecture\ tuning.
$$

---

### DoD-9 — Environment frozen

Test phải gắn với một environment cố định:

$$
E=clean\_env\_v1.
$$

Không được có:

```text
real web search
changing pages
changing DB.
```

---

### DoD-10 — Reproducibility

Phải xác định được benchmark bằng:

$$
B=
(
git\_commit,
dataset\_hash,
environment\_hash,
schema\_version,
split\_seed
).
$$

---

# CVI. Output cuối Phase 2

Khi xong Phase 2, repository nên có tối thiểu:

```text
data/clean/v1/
│
├── splits/
│   ├── dev.jsonl              # 150
│   └── test.jsonl             # 100
│
├── environment/
│   ├── documents/
│   ├── cached_pages/
│   └── database/
│
├── manifests/
│   ├── benchmark_manifest.json
│   ├── split_manifest.json
│   └── environment_manifest.json
│
├── reviews/
│   └── review_log.jsonl
│
└── checksums/
    ├── dev.sha256
    ├── test.sha256
    └── environment.sha256
```

và:

```text
docs/
├── clean_benchmark_design.md
├── clean_task_schema.md
├── ground_truth_spec.md
├── review_protocol.md
├── split_protocol.md
└── clean_data_card.md
```

---

# CVII. Trạng thái hệ thống khi kết thúc Phase 2

Nếu Phase 1 và Phase 2 đều đúng, lúc này nhóm sẽ có:

$$
A0
$$

chạy end-to-end,

cùng:

$$
D_{\text{clean}}^{dev}=150
$$

và:

$$
D_{\text{clean}}^{test}=100.
$$

Toàn bộ pipeline trở thành:

```text
                 Frozen Clean Environment
                          │
                          ▼
Clean Task ──────→ A0 Agent Runtime
                          │
                          ▼
                    8 Mock Tools
                          │
                          ▼
                    Execution Trace
                          │
                          ▼
                 Ground-truth Evaluator
```

Đây là nền tảng trực tiếp cho **RQ1 — capability**, đúng với mục tiêu của bản kế hoạch. 

Điểm tôi coi là quan trọng nhất của Phase 2 là: **đừng tối ưu để tạo 250 câu thật nhanh; hãy tối ưu để mỗi task trở thành một đơn vị thí nghiệm có ground truth máy kiểm tra được**. Nếu schema, oracle, split và review làm đúng ở đây, Phase 6 gần như chỉ còn việc viết evaluator; nếu Phase 2 làm sơ sài, đến lúc chạy hàng nghìn trajectory ở Phase 7 mới phát hiện benchmark sai thì chi phí sửa sẽ rất lớn.
