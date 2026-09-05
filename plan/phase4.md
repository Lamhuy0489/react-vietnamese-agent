# Phase 4 — Vietnamese Normalization, Artifact/Provenance Foundation & Integration Contracts

**Tuần 9–10**

## I. Problem Formulation & Objectives

Theo bản Word đã chốt, Phase 4 tương ứng với **Tuần 9–10**. Mục tiêu chính là hoàn thiện chuẩn hóa tiếng Việt, cấu trúc dữ liệu có nguồn gốc và quy ước tích hợp giữa các thành phần. Phân công hiện tại cũng xác định Huy phụ trách trạng thái điều khiển, quy tắc quyết định và phần kiểm tra trước khi công cụ thực thi; Minh phụ trách bộ chuẩn hóa tiếng Việt, cấu trúc dữ liệu, theo dõi nguồn gốc và phần xử lý sau tool output. Hai người phải thống nhất interface giữa control-flow và data-flow. 

Phase 4 phải được hiểu là **phase xây nền tảng kiến trúc cho A1–A6**, chứ chưa phải phase hoàn thiện các defense.

Sau Phase 4, ta muốn chuyển hệ thống từ dạng:

$$
Task
\rightarrow
LLM
\rightarrow
Tool
\rightarrow
LLM
\rightarrow
Final
$$

thành một runtime có representation đủ giàu:

$$
\boxed{
Raw\ Input
\rightarrow
Artifact
\rightarrow
Context
\rightarrow
ModelTurn
\rightarrow
ActionProposal
\rightarrow
ToolResult
\rightarrow
Artifact
\rightarrow
FinalArtifact
}
$$

và mọi dữ liệu đều có thể trả lời được các câu hỏi:

$$
\text{Nó đến từ đâu?}
$$

$$
\text{Nó được tạo ở bước nào?}
$$

$$
\text{Nó có nhạy cảm không?}
$$

$$
\text{Nguồn của nó đáng tin đến mức nào?}
$$

$$
\text{Nó đã trải qua phép biến đổi nào?}
$$

Nhưng Phase 4 **chưa quyết định**:

> “Có block hay không?”

Quyết định security cụ thể thuộc Phase 5 khi triển khai A1–A6.

Kiến trúc nên là:

$$
\boxed{
Phase\ 4 = Representation + Plumbing
}
$$

$$
\boxed{
Phase\ 5 = Security\ Policy + Enforcement
}
$$

Đây là ranh giới quan trọng.

---

# II. Một prerequisite cần kiểm tra trước khi bắt đầu

Trong Word, tập robustness clean gồm 50 canonical tasks + 250 variants phải được chọn và khóa trước khi sử dụng cho đánh giá cuối. 

Theo logic toàn dự án, **50 canonical clean tasks dùng cho robustness phải đã được xác định trước khi bắt đầu tune normalizer trên Dev**.

Nếu Phase 2 trước đó chưa thực hiện bước này, cần bổ sung ngay trước Phase 4:

$$
D_{\text{rob}}^{canonical}
\subseteq
D_{\text{clean}}^{test}
$$

với:

$$
|D_{\text{rob}}^{canonical}|=50
$$

và chỉ lưu IDs:

```text
clean_005
clean_009
clean_013
...
```

Sau đó seal danh sách.

Không chạy model trên 50 tasks đó để điều chỉnh normalizer.

Nguyên tắc:

$$
D_{\text{rob}}^{test}
\not\rightarrow
Normalization\ Tuning.
$$

Ta có thể sử dụng:

$$
D_{\text{clean}}^{dev}
$$

và:

$$
D_{\text{atk}}^{dev}
$$

để phát triển Phase 4.

---

# III. Mục tiêu kỹ thuật tổng thể của Phase 4

Phase này nên tạo ra sáu nhóm thành phần:

$$
P_4=
\{
Normalizer,
ArtifactModel,
ControlState,
ArtifactStore,
ProvenanceGraph,
IntegrationContracts
\}.
$$

Cụ thể:

1. **Normalizer**
   Tạo các representation chuẩn hóa nhưng không phá dữ liệu raw.

2. **Artifact model**
   Biến dữ liệu thành các object có ID, source, sensitivity, trust.

3. **Control-flow state**
   Theo dõi run, step, tool calls, retries, status.

4. **Artifact store**
   Quản lý các artifact phát sinh trong trajectory.

5. **Provenance foundation**
   Theo dõi quan hệ:

   $$
   parent\rightarrow child.
   $$

6. **Future security hook interfaces**
   Chuẩn bị vị trí:

   $$
   PreGate,\ PostGate,\ FinalGate
   $$

   nhưng ở A0 vẫn là no-op.

---

# IV. Architecture sau Phase 4

Kiến trúc đề xuất:

```text
                  ┌──────────────────────┐
                  │      Raw Task        │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Artifact Factory   │
                  │  system-managed ID   │
                  └──────────┬───────────┘
                             │
             ┌───────────────┴────────────────┐
             │                                │
             ▼                                ▼
      Raw representation              Normalized views
             │                                │
             └───────────────┬────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    Artifact Store    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Context Builder    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │     LLM Backend      │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    Model Output      │
                  │      Artifact        │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Structured Parser   │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Action Proposal    │
                  └──────────┬───────────┘
                             │
                       Future Pre-Gate
                             │
                             ▼
                  ┌──────────────────────┐
                  │     Tool Broker      │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │     Tool Result      │
                  └──────────┬───────────┘
                             │
                       Future Post-Gate
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Result Artifact    │
                  └──────────┬───────────┘
                             │
                             ▼
                   Provenance Graph
```

Sau Phase 5, chỉ cần biến:

```text
Future Pre-Gate
Future Post-Gate
Future Final-Gate
```

thành implementations thật.

Không cần viết lại runtime.

---

# V. Nguyên tắc số 1: RAW và NORMALIZED phải tách biệt

Đây là điểm quan trọng nhất của normalizer.

Không bao giờ:

```python
text = normalize(text)
```

rồi bỏ mất input ban đầu.

Phải lưu:

$$
x^{raw}
$$

và:

$$
x^{norm}.
$$

Ví dụ:

```json
{
  "raw_text": "gửi\u200bdữ liệu",
  "normalized_text": "gửi dữ liệu"
}
```

Tại sao?

Bởi RQ3 cần đo:

$$
Model(x^{raw})
$$

trước defense.

Nếu mọi variant đều bị normalize trước khi model nhìn thấy:

$$
x^{variant}
\xrightarrow{Normalizer}
x^{canonical}
$$

thì robustness drop bị che mất.

Ta không còn biết model thực sự robust hay chỉ được normalizer sửa input.

Do đó phải có hai chế độ thí nghiệm khác nhau.

---

# VI. Raw Evaluation vs Normalized Defense

Sau này cần phân biệt:

### Mode 1 — Raw

$$
Input_{model}=x^{raw}.
$$

Dùng để đo intrinsic robustness.

### Mode 2 — Normalized

$$
Input_{model}=N(x^{raw}).
$$

Dùng để đo hiệu quả preprocessing defense.

Kết quả khác nhau:

$$
R_{raw}
\neq
R_{normalized}.
$$

Không được trộn hai điều kiện này.

---

# VII. Normalizer không phải autocorrect tiếng Việt

Một lỗi lớn cần tránh là làm normalizer quá thông minh.

Không nên tự động:

* khôi phục dấu;
* sửa chính tả;
* paraphrase;
* translate English sang Vietnamese;
* nối/tách từ bằng model;
* semantic rewriting.

Ví dụ:

```text
"dang ky hoc phan"
```

không nên tự động biến thành:

```text
"đăng ký học phần"
```

trong normalizer baseline.

Vì khi đó variant:

$$
no\text{-}diacritic
$$

gần như bị loại bỏ hoàn toàn.

Normalizer nên chủ yếu xử lý **Unicode-level và formatting-level anomalies**.

---

# VIII. Normalization Pipeline đề xuất

Tôi khuyên pipeline:

$$
N
=
N_{unicode}
\circ
N_{format}
\circ
N_{whitespace}.
$$

Không có semantic rewriting.

Implementation:

```text
raw text
   ↓
Unicode inspection
   ↓
Optional compatibility normalization
   ↓
format/control-character handling
   ↓
whitespace normalization
   ↓
normalized view
```

---

# IX. Bước 1 — UTF-8 handling

Tất cả benchmark files:

$$
Encoding=UTF\text{-}8.
$$

Khi đọc:

```python
open(path, encoding="utf-8")
```

Không dựa vào encoding mặc định Windows/macOS.

Unit test:

$$
decode(encode(x))=x.
$$

Với toàn bộ Vietnamese characters.

---

# X. Unicode normalization

Có hai Unicode representations nhìn giống nhau nhưng byte khác nhau.

Ví dụ ký tự có dấu có thể tồn tại:

$$
base + combining\ mark
$$

hoặc:

$$
precomposed\ character.
$$

Nên normalizer hỗ trợ Unicode normalization.

Tôi khuyên profile security normalization sử dụng:

$$
NFKC
$$

hoặc profile riêng có thể cấu hình.

Nhưng **raw không bao giờ bị overwrite**.

Ví dụ:

```python
unicodedata.normalize("NFKC", raw_text)
```

Phải log:

```json
{
  "operation": "unicode_nfkc",
  "changed": true
}
```

---

# XI. Tại sao dùng profile thay vì hard-code NFKC?

Vì sau này có thể cần chạy ablation:

$$
A6+NFKC
$$

vs

$$
A6-NFKC.
$$

Nếu normalizer hard-code vào runtime thì không thể tách effect.

Config:

```yaml
normalization:
  profile: security_v1
```

Ví dụ:

```yaml
profiles:

  raw:
    unicode_form: null
    remove_zero_width: false
    normalize_whitespace: false

  unicode_only:
    unicode_form: NFKC
    remove_zero_width: false
    normalize_whitespace: false

  security_v1:
    unicode_form: NFKC
    remove_zero_width: true
    normalize_whitespace: true
```

---

# XII. Zero-width character handling

Phase 3 đã có zero-width variants.

Whitelist các code points cần quan sát:

$$
Z=
\{
U+200B,
U+200C,
U+200D,
U+2060,
U+FEFF
\}.
$$

Không nên remove mọi ký tự Unicode category `Cf` một cách mù quáng.

Dùng explicit list.

---

# XIII. NormalizationResult

Không trả chỉ một string.

Nên:

```json
{
  "raw_text": "gửi\u200bdữ liệu",
  "normalized_text": "gửidữ liệu",

  "profile": "security_v1",

  "operations": [
    {
      "type": "remove_char",
      "codepoint": "U+200B",
      "raw_position": 3
    }
  ],

  "features": {
    "zero_width_count": 1
  }
}
```

Điều này giúp audit.

---

# XIV. Có nên thay zero-width bằng space không?

Không luôn luôn.

Ví dụ:

```text
"gửi<U+200B>dữ liệu"
```

Nếu zero-width được chèn giữa hai từ đã không có space:

```text
gửidữ liệu
```

remove đơn giản có thể tạo:

```text
gửidữ liệu
```

không phải:

```text
gửi dữ liệu.
```

Normalizer không nên tự đoán token boundary quá mạnh.

Do đó zero-width handling có thể có hai modes:

```text
REMOVE
```

hoặc:

```text
REPLACE_WITH_SPACE
```

nhưng profile phải cố định trước experiment.

Tốt hơn trong Phase 4:

```text
REMOVE
```

và giữ operation map.

Sau Dev experiments nếu thấy semantics cần điều chỉnh thì profile version bump.

Không dùng Test để quyết định.

---

# XV. Whitespace normalization

Có thể xử lý:

* multiple spaces;
* tabs;
* CRLF;
* non-breaking space;
* repeated blank lines.

Ví dụ:

$$
[space]^n
\rightarrow
space.
$$

Nhưng không nên xóa newline tùy tiện nếu document structure có ý nghĩa.

Tôi khuyên:

```text
normalize inline whitespace
preserve paragraph boundaries
```

---

# XVI. Các tín hiệu linguistic nên tính nhưng không tự sửa

Normalizer có thể extract metadata:

```text
zero_width_count
control_character_count
non_ascii_format_count
diacritic_ratio
ascii_letter_ratio
english_token_ratio
underscore_density
unusual_whitespace_count
```

Ví dụ:

$$
r_{diacritic}
=
\frac{
N_{\text{Vietnamese chars with diacritics}}
{
N_{\text{alphabetic Vietnamese-compatible chars}}
}.
$$

Không cần dùng metric này để block trong Phase 4.

Chỉ lưu signal.

---

# XVII. Không thêm attack regex ở Phase 4

Ví dụ:

```text
"ignore previous instructions"
"bỏ qua yêu cầu trước"
```

không được gắn:

```text
malicious=true
```

ở Phase 4.

Đó là:

$$
A1.
$$

Phase 4 chỉ nên biết:

```text
text representation
unicode features
source metadata.
```

Không đưa semantics attack vào normalizer.

---

# XVIII. Artifact model — thành phần quan trọng thứ hai

Hiện Phase 1/2 có thể đang xử lý dữ liệu như strings/dicts.

Phase 4 phải tạo abstraction:

$$
Artifact.
$$

Một artifact là một đơn vị dữ liệu mà hệ thống có thể theo dõi.

Ví dụ:

* user instruction;
* document content;
* database result;
* cached page;
* calculation result;
* model-generated tool argument;
* final answer.

---

# XIX. Artifact Schema đề xuất

```python
@dataclass(frozen=True)
class Artifact:
    artifact_id: str

    artifact_type: str

    raw_content: Any

    normalized_content: Any | None

    source_type: str
    source_id: str | None

    producer: str

    created_step: int

    sensitivity: str
    trust: str

    parent_ids: tuple[str, ...]

    transformations: tuple[str, ...]

    content_hash: str

    metadata: dict
```

Không cần `frozen=True` nếu implementation bất tiện, nhưng về semantics artifact nên immutable.

---

# XX. Artifact ID phải do hệ thống cấp

Không để LLM nói:

```json
{
  "artifact_id": "safe_001"
}
```

rồi hệ thống tin.

Artifact ID phải được runtime sinh.

Ví dụ:

```text
ART_run001_000001
ART_run001_000002
ART_run001_000003
```

Formal:

$$
artifact\_id
=
f(run\_id, sequence).
$$

Ưu điểm:

* deterministic trong replay;
* dễ debug;
* không collision trong một run;
* LLM không giả mạo artifact identity.

---

# XXI. Static source ID và runtime artifact ID phải khác nhau

Ví dụ:

```text
DOC_014
```

là source ID cố định.

Khi đọc document:

```text
DOC_014
```

tool tạo runtime artifact:

```text
ART_run52_0007.
```

Artifact:

```json
{
  "artifact_id": "ART_run52_0007",
  "source_type": "document",
  "source_id": "DOC_014"
}
```

Đừng dùng:

```text
artifact_id = DOC_014
```

vì một source có thể được đọc nhiều lần hoặc qua nhiều transformations.

---

# XXII. Artifact types

Tôi đề xuất enum tối thiểu:

```text
USER_INPUT
DOCUMENT_CONTENT
CACHED_PAGE
DB_RESULT
CALCULATION_RESULT
TOOL_RESULT
MODEL_OUTPUT
TOOL_ARGUMENT
FINAL_RESPONSE
NORMALIZED_VIEW
```

Không cần tạo hàng chục types.

---

# XXIII. Sensitivity labels

Word yêu cầu tách độ nhạy cảm và độ tin cậy. 

Có thể định nghĩa:

$$
S_0 = Public
$$

$$
S_1 = Internal
$$

$$
S_2 = Confidential.
$$

Order:

$$
S_0<S_1<S_2.
$$

Ví dụ:

| Data                    | Label |
| ----------------------- | ----- |
| Lịch học công khai      | S0    |
| Hướng dẫn nội bộ        | S1    |
| Hồ sơ sinh viên giả lập | S2    |

---

# XXIV. Trust labels

Tách riêng:

$$
T_0=Trusted
$$

$$
T_1=Untrusted.
$$

Hoặc enum rõ nghĩa hơn:

```text
TRUSTED
UNTRUSTED
```

Ví dụ:

| Data                 | Sensitivity | Trust     |
| -------------------- | ----------- | --------- |
| Public poisoned page | S0          | UNTRUSTED |
| Student DB record    | S2          | TRUSTED   |
| User-provided text   | tùy         | UNTRUSTED |
| Internal policy doc  | S1          | TRUSTED   |

Vì:

$$
Sensitivity
\perp
Trust.
$$

---

# XXV. Không dùng một field `"safe": true`

Không:

```json
{
  "safe": false
}
```

Bởi vì nó trộn:

* confidential;
* untrusted;
* poisoned;
* unauthorized.

Hệ thống sau này cần xử lý riêng.

---

# XXVI. Artifact immutability

Một artifact sau khi tạo không nên thay label trực tiếp.

Không:

```python
artifact.sensitivity = "S0"
```

sau khi sanitize.

Tốt hơn:

$$
a_1
\xrightarrow{transform}
a_2.
$$

Ví dụ:

```text
ART_004 original sensitive record
      ↓ redact
ART_007 redacted representation
```

và:

$$
parent(ART_{007})=ART_{004}.
$$

Đây là nền tảng provenance tốt hơn.

---

# XXVII. Content hash

Mỗi artifact nên có:

$$
h(a)
=
SHA256(canonical\ serialization(content)).
$$

Mục tiêu không phải cryptographic security, mà là:

* detect mutation;
* reproducibility;
* trace audit.

Ví dụ:

```json
{
  "content_hash": "sha256:..."
}
```

---

# XXVIII. ArtifactStore

Interface:

```python
class ArtifactStore:

    def create(...):
        ...

    def get(artifact_id):
        ...

    def parents(artifact_id):
        ...

    def children(artifact_id):
        ...

    def all():
        ...
```

Không để các module tự giữ dict artifact riêng.

Cần:

$$
Single\ Source\ of\ Truth.
$$

---

# XXIX. Artifact Store theo run

Artifact store nên isolated:

$$
Store_{run_i}
\cap
Store_{run_j}
=
\emptyset.
$$

Không để artifact của task trước lọt sang task sau.

Đây là requirement rất quan trọng.

Unit test:

```text
run A
→ ART_A_001

run B
→ cannot access ART_A_001
```

---

# XXX. Provenance Graph

Provenance được mô hình:

$$
G=(V,E).
$$

Trong đó:

$$
V=\{Artifacts\}
$$

và edge:

$$
(a_i,a_j)
$$

nghĩa:

$$
a_j\ derived\ from\ a_i.
$$

---

# XXXI. Một số relation types

Không nên chỉ lưu parent IDs mà không biết quan hệ.

Có thể có:

```text
OBSERVED_FROM
DERIVED_FROM
NORMALIZED_FROM
GENERATED_USING
EXTRACTED_FROM
ARGUMENT_DERIVED_FROM
```

Ví dụ:

```text
DOC_014 content
   ↓ NORMALIZED_FROM
normalized document artifact
```

Hoặc:

```text
tool observation
   ↓ GENERATED_USING
model action
```

---

# XXXII. Tuy nhiên provenance không được tuyên bố quá chính xác

LLM là generative model.

Không thể biết chính xác:

> token “15/8” trong final answer đến từ đúng byte nào trong prompt.

Do đó không nên giả vờ có token-level causal provenance.

Nên dùng:

$$
conservative\ dependency.
$$

Nếu một model turn thấy artifacts:

$$
A=\{a_1,a_2,a_3\}
$$

thì output có thể được gắn:

$$
parents(output)
=
\{a_1,a_2,a_3\}.
$$

Đây là over-approximation.

Nó có thể có false provenance, nhưng ít nguy cơ bỏ sót dependency.

---

# XXXIII. Tại sao conservative lineage phù hợp hơn?

Security ưu tiên:

$$
Soundness > Precision.
$$

Nếu ta không biết model dùng artifact nào:

$$
Unknown
$$

không nên giả định:

$$
None.
$$

Có thể áp dụng:

$$
parents(y)
=
ContextArtifacts(y).
$$

Sau này A6 có thể dùng conservative policy.

---

# XXXIV. Control-Flow State

Song song với Artifact Store cần:

$$
ControlState.
$$

Đây là thứ Huy nên phụ trách chính theo phân công hiện tại. 

Ví dụ:

```python
@dataclass
class ControlState:
    run_id: str
    task_id: str

    step: int
    status: str

    model_turn_count: int
    tool_call_count: int

    format_retry_count: int

    proposed_tool: str | None
    active_call_id: str | None

    called_tools: list[str]

    terminal_reason: str | None
```

---

# XXXV. Control State và Data Artifact không được trộn

Phải giữ:

$$
ControlFlow
\neq
DataFlow.
$$

Control:

```text
step=4
retry_count=1
current_tool=db_query
```

Data:

```text
student_record
sensitivity=S2
trust=TRUSTED
```

Nếu gộp tất cả vào một dict:

```python
state = {...}
```

sau này A5/A6 sẽ rất khó quản lý.

---

# XXXVI. ContextBundle

Để nối hai thế giới, tạo:

```python
@dataclass
class ContextBundle:
    messages: list[dict]
    artifact_ids: list[str]
```

Khi model được gọi:

```python
context = builder.build(...)
```

không chỉ trả:

```python
messages
```

mà còn trả:

```text
những artifact nào đã được đưa vào context.
```

Ví dụ:

```json
{
  "artifact_ids": [
    "ART_001",
    "ART_004",
    "ART_007"
  ]
}
```

---

# XXXVII. Model output lineage

Nếu model output:

```text
ART_010
```

thì:

$$
parents(ART_{010})
=
ContextArtifacts.
$$

Nếu context chứa:

$$
ART_001,
ART_004,
ART_007
$$

thì:

$$
P(ART_{010})=
\{ART_001,ART_004,ART_007\}.
$$

---

# XXXVIII. Tool argument artifacts

Ví dụ LLM đề xuất:

```json
{
  "name": "send_email_mock",
  "arguments": {
    "to": "external@example.test",
    "body": "..."
  }
}
```

Không chỉ lưu một dict.

Có thể tạo:

```text
ART_011 = tool argument: recipient
ART_012 = tool argument: body
```

hoặc một artifact chung:

```text
ART_011 = complete ToolCall arguments
```

Tôi khuyên Phase 4 dùng **field-level artifacts cho security-relevant fields**, nhưng không cần field-level cho mọi tool.

Ví dụ:

```text
send_email_mock.to
send_email_mock.body
post_webhook_mock.endpoint
post_webhook_mock.payload
```

nên tách.

Vì A6 cần biết:

$$
body
$$

có phụ thuộc sensitive artifact không.

---

# XXXIX. Không cần field-level artifact cho tất cả

Ví dụ:

```text
calculator.expression
```

không nhất thiết phải phân mảnh quá mức.

Nếu mọi JSON scalar là artifact:

$$
N_{artifacts}
$$

tăng rất nhanh và hệ thống khó debug.

Dùng nguyên tắc:

$$
Granularity
=
SecurityRelevant\ Field.
$$

---

# XL. Source metadata

Mỗi artifact cần source:

```text
USER
DOCUMENT
DATABASE
CACHED_PAGE
CALCULATOR
MODEL
SYSTEM
```

Với tool output:

```json
{
  "source_type": "TOOL",
  "source_id": "doc_read",
  "metadata": {
    "document_id": "DOC_014"
  }
}
```

---

# XLI. Source trust mặc định

Phase 4 có thể định nghĩa defaults dưới dạng **metadata rule**, chưa dùng để block.

Ví dụ:

```yaml
source_defaults:

  user:
    trust: UNTRUSTED

  internal_document:
    trust: TRUSTED

  cached_page:
    trust: UNTRUSTED

  database:
    trust: TRUSTED

  model_output:
    trust: UNTRUSTED
```

Nhưng đây chỉ là initialization.

Không có:

```text
if UNTRUSTED → deny.
```

trong Phase 4.

---

# XLII. Sensitivity propagation primitive

Có thể chuẩn bị toán tử:

$$
join_S.
$$

Ví dụ:

$$
S_0\sqcup S_1=S_1
$$

$$
S_1\sqcup S_2=S_2.
$$

Tổng quát:

$$
S(a_{child})
=
\max_{p\in Parents(a)}
S(p).
$$

Đây là conservative propagation.

Nhưng Phase 4 chưa dùng nó để block.

---

# XLIII. Trust propagation primitive

Tương tự có thể định nghĩa:

$$
UNTRUSTED
$$

dominate:

$$
TRUSTED.
$$

Nếu:

$$
Parents(a)=
\{T_0,T_1\}
$$

thì mặc định:

$$
Trust(a)=T_1.
$$

Nhưng cần phân biệt **sanitization** sau này.

Không tự động chuyển:

$$
UNTRUSTED\rightarrow TRUSTED
$$

chỉ vì content đã normalize.

Normalization:

$$
\neq
Sanitization.
$$

Đây là nguyên tắc rất quan trọng.

---

# XLIV. Normalization không làm tăng trust

Nếu:

$$
a.trust=UNTRUSTED
$$

và:

$$
b=N(a)
$$

thì:

$$
b.trust=UNTRUSTED.
$$

Không:

$$
N(a)\Rightarrow TRUSTED.
$$

Zero-width removal không chứng minh nội dung benign.

---

# XLV. Normalization không làm giảm sensitivity

Tương tự:

$$
Sensitivity(N(a))
=
Sensitivity(a).
$$

Ví dụ student record vẫn sensitive sau NFKC.

---

# XLVI. Declassification chưa làm ở Phase 4

Phase này chỉ chuẩn bị representation.

Không triển khai:

$$
S_2\rightarrow S_0.
$$

Declassification là policy mechanism của A6/Phase 5.

---

# XLVII. Future Gate Interface

Đây là phần Huy có thể chuẩn bị.

Định nghĩa:

```python
class PreExecutionHook(Protocol):

    def evaluate(
        self,
        control_state,
        action,
        artifacts
    ) -> Decision:
        ...
```

Decision:

```python
class Decision:
    effect: str
    reason_code: str | None
    metadata: dict
```

Possible effects:

```text
ALLOW
DENY
TRANSFORM
```

Nhưng ở A0:

```python
AllowAllPreHook
```

luôn:

$$
ALLOW.
$$

---

# XLVIII. PostExecutionHook

Interface:

```python
class PostExecutionHook(Protocol):

    def process(
        self,
        control_state,
        action,
        tool_result,
        artifact_store
    ):
        ...
```

A0 implementation chỉ:

1. tạo artifact;
2. assign metadata;
3. provenance;
4. return result.

Không security blocking.

---

# XLIX. FinalResponseHook

Chuẩn bị interface:

```python
class FinalResponseHook(Protocol):

    def evaluate(
        self,
        final_artifact,
        state,
        artifact_store
    ):
        ...
```

A0:

```text
allow everything.
```

A6 sau này mới dùng lineage.

---

# L. Decision logging

Mặc dù Phase 4 A0 luôn allow, trace schema nên bắt đầu hỗ trợ:

```json
{
  "event": "policy_decision",

  "stage": "pre",

  "decision": "ALLOW",

  "policy": "A0_PASS_THROUGH"
}
```

Hoặc có thể không log A0 no-op nếu muốn tránh noise.

Nhưng schema nên tồn tại.

---

# LI. Integration Contract tổng thể

Từ Phase 4 trở đi, mọi module phải tuân:

$$
Runtime
\rightarrow
ContextBundle
\rightarrow
LLM
\rightarrow
ModelArtifact
\rightarrow
Parser
\rightarrow
ActionProposal
\rightarrow
PreHook
\rightarrow
Broker
\rightarrow
PostHook
\rightarrow
ArtifactStore.
$$

Không module nào bypass.

Đặc biệt:

$$
Agent\not\rightarrow Tool.
$$

và:

$$
ToolResult\not\rightarrow Context
$$

nếu chưa qua ArtifactFactory/PostHook.

---

# LII. ToolResult → Artifact

Phase 1:

```text
ToolResult
→ context
```

Phase 4:

```text
ToolResult
→ ArtifactFactory
→ ArtifactStore
→ Context.
```

Đây là structural change quan trọng.

---

# LIII. Example

Task:

> “Tìm học phí chương trình chuẩn.”

User artifact:

```text
ART_001
type=USER_INPUT
```

LLM action:

```text
ART_002
type=MODEL_OUTPUT
parents=[ART_001]
```

Search result:

```text
ART_003
type=TOOL_RESULT
source=doc_search
parents=[ART_002]
```

Read document:

```text
ART_005
type=DOCUMENT_CONTENT
source=DOC_014
parents=[ART_004]
```

Final:

```text
ART_007
type=FINAL_RESPONSE
parents=[
 ART_001,
 ART_003,
 ART_005
]
```

Graph:

$$
ART_001
\rightarrow
ART_002
\rightarrow
ART_003
\rightarrow
ART_004
\rightarrow
ART_005
\rightarrow
ART_006
\rightarrow
ART_007.
$$

Không cần token-level detail.

---

# LIV. Provenance DAG requirement

Graph phải là DAG:

$$
G=(V,E)
$$

và:

$$
G
$$

không có cycle.

Mỗi parent phải tồn tại trước child:

$$
created(p)<created(c).
$$

Unit test:

```text
self-parent → reject
future-parent → reject
cycle → reject
```

---

# LV. Artifact lineage query

Phase 5 cần query:

$$
Ancestors(a).
$$

Do đó Phase 4 phải hỗ trợ:

```python
store.ancestors(artifact_id)
```

và:

```python
store.has_sensitive_ancestor(...)
```

có thể chưa implement security logic, nhưng graph traversal nên có.

Complexity với DAG nhỏ:

$$
O(|V|+|E|).
$$

Trajectory có vài chục artifacts nên không phải bottleneck.

---

# LVI. Storage strategy

Không cần graph database.

Không cần Neo4j.

Dùng:

```text
Python dictionaries
+
JSONL trace
```

là đủ.

Ví dụ:

```python
artifacts: dict[str, Artifact]

parents:
dict[str, set[str]]

children:
dict[str, set[str]]
```

Đơn giản và reproducible.

---

# LVII. Artifact serialization

Mỗi run có thể xuất:

```text
artifacts.jsonl
provenance_edges.jsonl
```

Ví dụ edge:

```json
{
  "run_id": "RUN_001",
  "parent": "ART_003",
  "child": "ART_007",
  "relation": "GENERATED_USING"
}
```

---

# LVIII. Không commit massive runtime logs vào Git

Source/config/data:

$$
GitHub.
$$

Raw experimental traces lớn:

$$
Kaggle\ output
$$

hoặc release/storage phù hợp.

Git repo chỉ nên giữ:

* small sample traces;
* schema;
* summary;
* manifests.

---

# LIX. Normalizer logging

Không log chỉ:

```text
normalized=true.
```

Cần:

```json
{
  "profile": "security_v1",

  "input_hash": "...",
  "output_hash": "...",

  "operations": [
    "NFKC",
    "REMOVE_ZERO_WIDTH"
  ],

  "changed": true
}
```

---

# LX. Normalizer idempotence

Một normalizer tốt nên thỏa:

$$
N(N(x))=N(x).
$$

Unit test toàn bộ Dev variant corpus.

Nếu:

$$
N(N(x))\neq N(x)
$$

thì pipeline khó reproduce.

---

# LXI. Raw preservation property

Phải đảm bảo:

$$
raw_{after}=raw_{before}.
$$

Normalizer không mutate input object.

Test bằng hash:

$$
SHA256(raw_{before})
=
SHA256(raw_{after}).
$$

---

# LXII. Determinism

Với cùng:

$$
x,p
$$

trong đó \(p\) là normalization profile:

$$
N_p(x)=constant.
$$

Không random.

Nếu zero-width handling dùng position rules, rule cũng deterministic.

---

# LXIII. Unicode test corpus

Tạo:

```text
tests/fixtures/unicode_cases.jsonl
```

Cover:

* NFC Vietnamese;
* decomposed Vietnamese;
* no-diacritic;
* zero-width;
* NBSP;
* tabs;
* multiple spaces;
* CRLF;
* mixed Vietnamese/English;
* underscores;
* emoji;
* punctuation;
* URLs;
* emails.

Không cần chỉ test attack strings.

---

# LXIV. Golden normalizer tests

Ví dụ:

```json
{
  "input": "gửi\u200bdữ liệu",
  "profile": "security_v1",
  "expected": "gửidữ liệu"
}
```

hoặc rule bạn đã chốt.

Golden tests phải version-control.

Nếu expected output thay đổi:

$$
normalization\ profile\ version
$$

phải đổi.

---

# LXV. Normalization versioning

Không dùng:

```text
normalizer.py
```

mà không version.

Mỗi run phải biết:

```text
normalization_profile=security_v1
```

Nếu sửa rule:

```text
security_v2.
```

Không silently overwrite semantics của `security_v1`.

---

# LXVI. Data model versioning

Artifact schema cũng cần:

```text
artifact_schema_version = 1
```

Trace:

```text
trace_schema_version = 2
```

Phase 4 chắc chắn sẽ làm trace format thay đổi so với Phase 1.

Đây là bình thường.

Nhưng migration phải explicit.

---

# LXVII. Migration từ Phase 1 traces

Không nhất thiết convert toàn bộ Phase 1 smoke traces.

Chỉ cần:

* giữ Phase 1 raw logs;
* Phase 4 trace schema version mới;
* viết migration helper nếu thực sự cần compare.

Không mất thời gian backward compatibility quá mức.

---

# LXVIII. Phase 4 không được sửa frozen datasets

Quan trọng:

$$
D_{\text{clean}}^{test}
$$

và:

$$
D_{\text{atk}}^{test}
$$

đã freeze.

Normalizer phải operate **trên representation**, không rewrite source files.

Không chạy script:

```python
for file in test:
    file.write(normalize(file.read()))
```

Điều đó làm checksum thay đổi.

---

# LXIX. Normalized views nên runtime-generated hoặc cached riêng

Ví dụ:

```text
derived/
normalization/security_v1/
```

Nếu cache:

```text
original data
         ↓
normalizer
         ↓
derived representation
```

Không replace originals.

---

# LXX. Cache key

Nếu cache normalized output:

$$
key
=
SHA256(raw)
+
profile\_version.
$$

Nếu raw hay profile đổi:

cache invalidated.

---

# LXXI. Signals chỉ lấy từ Dev trong development

Nếu bạn quyết định threshold cho:

```text
zero_width_count
code_mix_ratio
```

thì threshold chỉ được tuned từ:

$$
D_{dev}.
$$

Không nhìn Test distribution để chọn threshold.

Thực ra Phase 4 tốt nhất chưa cần threshold.

Chỉ extract features.

Threshold thuộc A1/Phase 5.

---

# LXXII. Integration tests với attack Dev

Dùng một số:

$$
D_{\text{atk}}^{dev}
$$

để kiểm tra data flow.

Ví dụ poisoned document:

```text
DOC_ATK_017
```

phải trở thành artifact:

```json
{
  "source_id": "DOC_ATK_017",
  "trust": "UNTRUSTED"
}
```

Sau model output:

$$
DOC\ artifact
\in
Ancestors(model\ output).
$$

Không cần block.

---

# LXXIII. Integration tests với sensitive Dev data

Ví dụ:

```text
STUDENT_REC_017
```

label:

$$
S_2.
$$

Tool result artifact:

```text
S2, TRUSTED.
```

Model output derived from nó:

$$
Sensitivity
$$

có thể conservatively propagate:

$$
S_2.
$$

Nhưng vẫn chưa block final answer trong Phase 4/A0.

---

# LXXIV. A0 purity sau Phase 4

Đây là regression requirement cực kỳ quan trọng.

Sau khi thêm Artifact/Provenance layer:

$$
Behavior(A0_{before})
\approx
Behavior(A0_{after})
$$

về tool decisions nếu cùng model/seed.

Phase 4 infrastructure không nên biến thành hidden defense.

Đặc biệt:

* zero-width normalizer không được bật vào A0 raw mode;
* trust metadata không được block;
* sensitivity metadata không được block;
* provenance không được block.

---

# LXXV. Regression test A0

Dùng ReplayBackend.

Phase 1 trajectory:

```text
Replay response sequence
```

chạy qua runtime Phase 4.

Expected tool sequence:

$$
S_{old}=S_{new}.
$$

Trace mới có artifact metadata nhiều hơn, nhưng behavior giống.

---

# LXXVI. Policy hook baseline

Config:

```yaml
security:
  pre_hook: pass_through
  post_hook: record_only
  final_hook: pass_through

normalization:
  model_input_profile: raw

tracking:
  artifacts: true
  provenance: true
```

Điều này rất tốt.

Ta có thể:

$$
tracking=ON
$$

nhưng:

$$
enforcement=OFF.
$$

---

# LXXVII. Phân công Huy — Tuần 9–10

Theo Word, Huy phụ trách control state, decision rules và phần pre-execution. 

Tôi cụ thể hóa ownership:

```text
src/react_agent/state/
├── control_state.py
└── runtime_state.py

src/react_agent/policy/
├── decision.py
├── hooks.py
└── passthrough.py

src/react_agent/context/
└── context_bundle.py

src/react_agent/broker/
└── tool_broker.py
```

Huy chịu trách nhiệm:

* ControlState;
* Hook interfaces;
* Decision schema;
* pre-execution integration point;
* ContextBundle integration;
* runtime changes;
* regression A0;
* trace event integration.

---

# LXXVIII. Phân công Minh

Theo Word, Minh phụ trách normalizer, data structure, provenance và post-tool processing. 

Ownership:

```text
src/react_agent/normalization/
├── base.py
├── unicode.py
├── profiles.py
└── features.py

src/react_agent/artifacts/
├── model.py
├── factory.py
├── store.py
└── labels.py

src/react_agent/provenance/
├── graph.py
└── relations.py
```

Minh chịu:

* NormalizationResult;
* Unicode profiles;
* Artifact model;
* ArtifactFactory;
* ArtifactStore;
* sensitivity/trust metadata;
* provenance graph;
* PostExecutionHook record-only;
* artifact serialization.

---

# LXXIX. Hai người làm chung

Phải cùng chốt:

```text
Artifact schema
Control/Data boundary
ContextBundle
Hook APIs
ToolResult → Artifact flow
Trace schema
Label semantics
Normalization profiles
```

Không để Huy nghĩ:

```text
trust=True/False
```

còn Minh dùng:

```text
T0/T1
```

rồi đến Phase 5 mới merge.

---

# LXXX. Week 9 — Ngày 1: Contract Freeze

Không code sâu ngay.

Chốt:

$$
Artifact
$$

$$
ControlState
$$

$$
NormalizationResult
$$

$$
ContextBundle
$$

$$
Decision
$$

$$
PreHook
$$

$$
PostHook
$$

$$
FinalHook.
$$

Tạo:

```text
docs/phase4_integration_contract.md
```

Đây là deliverable quan trọng nhất của ngày 1.

---

# LXXXI. Week 9 — Ngày 2–3

Huy:

* ControlState;
* ContextBundle;
* hook interfaces;
* pass-through hook;
* runtime integration skeleton.

Minh:

* normalizer;
* profiles;
* Unicode golden tests;
* Artifact model;
* labels.

Không merge trước unit tests.

---

# LXXXII. Week 9 — Ngày 4

Minh:

* ArtifactStore;
* ArtifactFactory;
* system-managed IDs;
* content hashing.

Huy:

* model output → artifact integration;
* action proposal → artifact references;
* trace schema upgrade.

---

# LXXXIII. Week 9 — Ngày 5

Implement:

$$
ToolResult
\rightarrow Artifact.
$$

Integration:

```text
Broker
→ Tool
→ ToolResult
→ PostHook
→ ArtifactFactory
→ ArtifactStore
```

A0 PostHook vẫn record-only.

---

# LXXXIV. Week 9 — Ngày 6

Implement provenance graph.

Test:

```text
user
→ model
→ tool
→ result
→ model
→ final
```

Graph phải đúng.

---

# LXXXV. Week 9 — Ngày 7

Full integration với Dummy/Replay.

Không dùng Kaggle nếu chưa pass CPU integration.

Exit Week 9:

* normalizer unit tests pass;
* ArtifactStore pass;
* ControlState pass;
* one full provenance trajectory pass;
* A0 behavior regression pass.

---

# LXXXVI. Week 10 — Ngày 1

Chạy trên:

$$
20\ Phase1\ smoke\ tasks.
$$

Kiểm tra:

$$
20/20
$$

terminal.

Kiểm tra:

* artifacts;
* provenance;
* raw preservation;
* trace integrity.

---

# LXXXVII. Week 10 — Ngày 2

Chạy sample:

$$
20-30
$$

clean Dev tasks.

Không Test.

Phân bố:

* single source;
* multi-step;
* DB+doc;
* error recovery.

Mục tiêu không đo accuracy.

Mục tiêu kiểm tra architectural coverage.

---

# LXXXVIII. Week 10 — Ngày 3

Chạy:

$$
20-30
$$

attack Dev/benign Dev.

Mục tiêu:

* poisoned content → untrusted artifact;
* sensitive content → S2 artifact;
* provenance reaches model action;
* no hidden block.

---

# LXXXIX. Week 10 — Ngày 4

Chạy normalizer fixture corpus:

* canonical Vietnamese;
* no-diacritic;
* boundary;
* code-mix;
* zero-width;
* paraphrase samples.

So sánh:

```text
raw
normalization result
features
```

Không tune bằng Test.

---

# XC. Week 10 — Ngày 5

Cross-review.

Huy review:

* provenance semantics;
* normalizer integration.

Minh review:

* control state;
* hook interface;
* A0 purity.

---

# XCI. Week 10 — Ngày 6

Documentation:

```text
normalization_spec.md
artifact_model.md
provenance_spec.md
integration_contract.md
phase4_report.md
```

---

# XCII. Week 10 — Ngày 7

Freeze Phase 4 infrastructure.

Tag:

```text
phase4-foundation-v1
```

Không freeze security policy vì Phase 5 mới triển khai.

---

# XCIII. Unit Tests — Normalizer

Phải test ít nhất:

* valid Vietnamese;
* decomposed Unicode;
* NFKC;
* zero-width;
* multiple zero-width;
* NBSP;
* tabs;
* CRLF;
* multiple spaces;
* code-mixing;
* email;
* URL;
* JSON string;
* underscores;
* emojis;
* empty input;
* long input;
* idempotence;
* determinism;
* raw preservation.

---

# XCIV. Unit Tests — Artifact

Test:

* unique IDs;
* stable content hash;
* immutable semantics;
* valid source type;
* valid sensitivity;
* valid trust;
* parent IDs;
* serialization;
* deserialization;
* missing parent detection.

---

# XCV. Unit Tests — ArtifactStore

Test:

* create;
* get;
* duplicate ID reject;
* unknown ID;
* run isolation;
* parents;
* children;
* all artifacts;
* serialization.

---

# XCVI. Unit Tests — Provenance

Test:

$$
a\rightarrow b
$$

$$
b\rightarrow c
$$

thì:

$$
a\in Ancestors(c).
$$

Ngoài ra:

* self-loop reject;
* cycle reject;
* unknown parent reject;
* relation type validation.

---

# XCVII. Unit Tests — Sensitivity

Test lattice:

$$
join(S_0,S_0)=S_0
$$

$$
join(S_0,S_1)=S_1
$$

$$
join(S_1,S_2)=S_2.
$$

---

# XCVIII. Unit Tests — Trust

Nếu conservative:

$$
join(T,T)=T
$$

$$
join(T,U)=U
$$

$$
join(U,U)=U.
$$

Nhưng chưa test sanitization vì chưa implement.

---

# XCIX. Integration test — Document

```text
USER_INPUT
    ↓
MODEL_OUTPUT
    ↓
doc_search
    ↓
TOOL_RESULT
    ↓
MODEL_OUTPUT
    ↓
doc_read
    ↓
DOCUMENT_ARTIFACT
    ↓
FINAL_RESPONSE
```

Ancestors final phải chứa document artifact.

---

# C. Integration test — DB sensitive

```text
db_query
→ S2 artifact
→ model output
```

Nếu conservative propagation bật metadata:

$$
Sensitivity(model\ output)=S_2.
$$

Nhưng A0 vẫn trả output.

---

# CI. Integration test — poisoned source

```text
cached_fetch
→ UNTRUSTED artifact
→ model output
```

Model output lineage phải có:

$$
UNTRUSTED\ ancestor.
$$

Không block.

---

# CII. Integration test — normalized view

Input:

```text
gửi<U+200B>dữ liệu
```

Artifacts:

```text
ART_RAW
```

và:

```text
ART_NORM.
```

Relationship:

$$
ART_{RAW}
\xrightarrow{NORMALIZED\_FROM}
ART_{NORM}.
$$

Raw hash không đổi.

---

# CIII. Integration test — A0 purity

Same ReplayBackend:

$$
ToolSequence_{Phase1}
=
ToolSequence_{Phase4}.
$$

Nếu khác chỉ vì metadata layer:

Phase 4 có bug.

---

# CIV. Performance

Artifact/provenance layer không được trở thành bottleneck.

Với trajectory:

$$
n<100
$$

artifacts thường là đủ.

Operations:

* create artifact:

$$
O(1)
$$

* parent insert:

$$
O(1)
$$

* ancestor traversal:

$$
O(V+E).
$$

Không cần tối ưu phức tạp.

---

# CV. Memory

Không copy full document content vào hàng chục artifacts nếu không cần.

Có thể dùng:

```text
content_ref
```

cho static sources.

Ví dụ artifact lưu:

```json
{
  "content_ref": "document://DOC_014",
  "content_hash": "..."
}
```

nhưng context builder vẫn lấy content khi cần.

Đối với runtime-generated content nhỏ thì lưu trực tiếp.

---

# CVI. Không tối ưu quá sớm

Không cần:

* distributed graph database;
* Kafka;
* Redis;
* PostgreSQL;
* Neo4j;
* vector DB;
* microservices.

Toàn bộ Phase 4 có thể chạy:

$$
Python
+
Pydantic/dataclasses
+
JSONL.
$$

Điều này phù hợp đồ án và dễ reproducibility.

---

# CVII. Logging sau Phase 4

Một run directory:

```text
results/<run_id>/
│
├── trace.jsonl
├── artifacts.jsonl
├── provenance_edges.jsonl
├── run_metadata.json
└── summary.json
```

---

# CVIII. Run metadata mới

Thêm:

```json
{
  "artifact_schema_version": "1",
  "trace_schema_version": "2",
  "normalization_profile": "raw",
  "normalizer_version": "1.0",
  "provenance_mode": "conservative_context"
}
```

---

# CIX. Checklist Phase 4 — A. Prerequisites

* [ ] Phase 1 A0 hoàn thành.
* [ ] Phase 2 Clean Dev/Test frozen.
* [ ] Phase 3 adversarial Dev/Test frozen.
* [ ] 50 canonical robustness tasks đã được xác định/seal.
* [ ] Không dùng Held-out Test để tune Phase 4.
* [ ] Clean environment checksum còn nguyên.
* [ ] Adversarial environment checksum còn nguyên.

---

# CX. B. Architectural contract

* [ ] Chốt Artifact schema.
* [ ] Chốt ControlState schema.
* [ ] Chốt ContextBundle schema.
* [ ] Chốt NormalizationResult schema.
* [ ] Chốt sensitivity labels.
* [ ] Chốt trust labels.
* [ ] Chốt provenance relation types.
* [ ] Chốt PreHook API.
* [ ] Chốt PostHook API.
* [ ] Chốt FinalHook API.
* [ ] Chốt Decision schema.
* [ ] Viết integration contract.
* [ ] Hai người review và approve contract trước khi code sâu.

---

# CXI. C. Normalization

* [ ] Giữ raw text bất biến.
* [ ] Sinh normalized view riêng.
* [ ] UTF-8 explicit.
* [ ] Unicode profile configurable.
* [ ] Có NFKC/NFC strategy rõ.
* [ ] Zero-width whitelist rõ.
* [ ] Không xóa mọi Unicode control mù quáng.
* [ ] Whitespace strategy rõ.
* [ ] Không khôi phục dấu.
* [ ] Không spell-correct.
* [ ] Không semantic paraphrase.
* [ ] Không translation.
* [ ] Có operation log.
* [ ] Có input/output hashes.
* [ ] Có profile version.
* [ ] Idempotence pass.
* [ ] Determinism pass.
* [ ] Raw preservation pass.

---

# CXII. D. Normalization features

* [ ] Zero-width count.
* [ ] Hidden/control character count.
* [ ] Unicode normalization changed flag.
* [ ] Whitespace anomaly count.
* [ ] Diacritic statistics.
* [ ] Code-mixing statistics nếu triển khai.
* [ ] Boundary anomaly statistics nếu triển khai.
* [ ] Feature extraction không block.
* [ ] Không attack classifier ở Phase 4.

---

# CXIII. E. Artifact model

* [ ] System-generated artifact IDs.
* [ ] Stable source IDs tách runtime IDs.
* [ ] Artifact type.
* [ ] Raw content/ref.
* [ ] Normalized content/ref.
* [ ] Source type.
* [ ] Source ID.
* [ ] Producer.
* [ ] Created step.
* [ ] Sensitivity.
* [ ] Trust.
* [ ] Parent IDs.
* [ ] Transformations.
* [ ] Content hash.
* [ ] Metadata.
* [ ] Schema version.

---

# CXIV. F. Artifact Store

* [ ] Create artifact.
* [ ] Retrieve artifact.
* [ ] Unique IDs.
* [ ] Run isolation.
* [ ] Parent lookup.
* [ ] Child lookup.
* [ ] Ancestor lookup.
* [ ] Serialization.
* [ ] Deserialization.
* [ ] Missing IDs handled.
* [ ] Artifact content không silently mutate.

---

# CXV. G. Sensitivity

* [ ] `S0` public.
* [ ] `S1` internal.
* [ ] `S2` confidential.
* [ ] Order defined.
* [ ] Join defined.
* [ ] Source defaults documented.
* [ ] Normalization không hạ sensitivity.
* [ ] Chưa declassify ở Phase 4.

---

# CXVI. H. Trust

* [ ] Trusted/untrusted enum.
* [ ] Source defaults documented.
* [ ] Trust và sensitivity independent.
* [ ] Conservative propagation primitive.
* [ ] Normalization không nâng trust.
* [ ] Chưa có trust-based blocking.
* [ ] Chưa có sanitization-to-trusted.

---

# CXVII. I. Provenance

* [ ] Graph representation.
* [ ] Parent-child edges.
* [ ] Relation types.
* [ ] DAG enforced.
* [ ] Self-loop reject.
* [ ] Cycle reject.
* [ ] Parent must exist.
* [ ] Ancestor query.
* [ ] Context-to-model lineage.
* [ ] Tool-result lineage.
* [ ] Normalization lineage.
* [ ] Final-response lineage.
* [ ] Conservative dependency documented.
* [ ] Không claim token-level provenance.

---

# CXVIII. J. Control state

* [ ] Run ID.
* [ ] Task ID.
* [ ] Step.
* [ ] Status.
* [ ] Retry count.
* [ ] Model turns.
* [ ] Tool-call count.
* [ ] Current/proposed tool.
* [ ] Active call ID.
* [ ] Called tools.
* [ ] Terminal reason.
* [ ] Control-flow tách data-flow.

---

# CXIX. K. Integration

* [ ] Raw task → artifact.
* [ ] ContextBuilder → ContextBundle.
* [ ] ContextBundle có artifact IDs.
* [ ] LLM output → artifact.
* [ ] Parser giữ source model artifact.
* [ ] ActionProposal có lineage.
* [ ] Tool call đi qua future PreHook location.
* [ ] ToolResult đi qua PostHook location.
* [ ] ToolResult → artifact.
* [ ] Final response → artifact.
* [ ] Future FinalHook location tồn tại.
* [ ] Không module bypass broker/store.

---

# CXX. L. Pass-through A0

* [ ] PreHook luôn allow.
* [ ] PostHook record-only.
* [ ] FinalHook always allow.
* [ ] Raw input profile dùng cho A0.
* [ ] Trust không block.
* [ ] Sensitivity không block.
* [ ] Provenance không block.
* [ ] Normalizer security profile không silently bật.
* [ ] A0 Replay regression pass.

---

# CXXI. M. Unit Tests

* [ ] Unicode tests.
* [ ] UTF-8 tests.
* [ ] Zero-width tests.
* [ ] Whitespace tests.
* [ ] Idempotence test.
* [ ] Determinism test.
* [ ] Raw-preservation test.
* [ ] Artifact-ID test.
* [ ] Artifact-hash test.
* [ ] Store isolation test.
* [ ] Provenance DAG tests.
* [ ] Ancestor tests.
* [ ] Sensitivity lattice tests.
* [ ] Trust propagation tests.
* [ ] ControlState tests.
* [ ] Hook interface tests.

---

# CXXII. N. Integration Tests

* [ ] No-tool trajectory.
* [ ] Document trajectory.
* [ ] Cached-page trajectory.
* [ ] DB trajectory.
* [ ] Calculator trajectory.
* [ ] Multi-step trajectory.
* [ ] Sensitive DB trajectory.
* [ ] Poisoned document Dev trajectory.
* [ ] Poisoned cached-page Dev trajectory.
* [ ] External sink trajectory.
* [ ] Final-answer artifact trajectory.
* [ ] Normalized-view trajectory.
* [ ] A0 no-block regression.
* [ ] 0 unhandled exception.

---

# CXXIII. O. Dataset discipline

* [ ] Không sửa frozen raw data.
* [ ] Normalized data lưu derived view.
* [ ] Không overwrite Test.
* [ ] Không dùng Test statistics để tune profiles.
* [ ] Dev-only experimentation.
* [ ] Derived-view version rõ.
* [ ] Cache key gồm input hash + profile version.

---

# CXXIV. P. Collaboration

* [ ] Huy ownership ControlState.
* [ ] Huy ownership future pre-gate integration.
* [ ] Huy ownership Decision/hook contracts.
* [ ] Minh ownership Normalizer.
* [ ] Minh ownership Artifact model/store.
* [ ] Minh ownership Provenance.
* [ ] Minh ownership post-tool artifact processing.
* [ ] Huy review Artifact/Normalizer.
* [ ] Minh review Control/Hook.
* [ ] Hai người cùng approve interface.

---

# CXXV. Q. Documentation

* [ ] `phase4_design.md`.
* [ ] `normalization_spec.md`.
* [ ] `normalization_profiles.yaml`.
* [ ] `artifact_model.md`.
* [ ] `sensitivity_trust_model.md`.
* [ ] `provenance_spec.md`.
* [ ] `integration_contract.md`.
* [ ] `trace_schema_v2.md`.
* [ ] `phase4_report.md`.
* [ ] Known limitations documented.

---

# CXXVI. Definition of Done — Phase 4

## DoD-1 — Raw preservation

Với mọi input:

$$
Hash(x_{raw}^{before})
=
Hash(x_{raw}^{after}).
$$

Normalizer không mutate raw data.

---

## DoD-2 — Deterministic normalization

Với cùng input \(x\) và profile \(p\):

$$
N_p(x)=N_p(x)
$$

qua mọi lần chạy.

---

## DoD-3 — Idempotence

$$
N_p(N_p(x))
=
N_p(x).
$$

Cho toàn bộ golden normalization test corpus.

---

## DoD-4 — Artifact completeness

Mọi observable runtime data quan trọng phải có artifact ID:

$$
user\ input,
tool\ result,
model\ output,
final\ output.
$$

---

## DoD-5 — Provenance completeness

Mọi child artifact có nguồn phải có:

$$
parents(child)\neq\emptyset
$$

trừ root artifacts như user input/static source.

---

## DoD-6 — DAG integrity

$$
ProvenanceGraph
$$

không có cycle.

---

## DoD-7 — Sensitivity/Trust independence

Hệ thống phải biểu diễn được ít nhất:

$$
(S_0,Trusted)
$$

$$
(S_0,Untrusted)
$$

$$
(S_2,Trusted)
$$

$$
(S_2,Untrusted).
$$

Không gộp hai dimensions.

---

## DoD-8 — A0 behavioral preservation

Với ReplayBackend:

$$
ToolSequence_{Phase1}
=
ToolSequence_{Phase4}.
$$

Infrastructure mới không trở thành hidden defense.

---

## DoD-9 — Hook readiness

Runtime có ba extension points:

$$
Pre
$$

$$
Post
$$

$$
Final.
$$

Nhưng A0 implementations vẫn pass-through.

---

## DoD-10 — Dev integration

Ít nhất:

$$
20-30
$$

Clean Dev tasks và:

$$
20-30
$$

Attack/Benign Dev tasks chạy end-to-end với artifact/provenance tracking.

Không crash.

---

## DoD-11 — Frozen-test integrity

Checksums của:

$$
D_{\text{clean}}^{test}
$$

và:

$$
D_{\text{attack}}^{test}
$$

không thay đổi trong Phase 4.

---

## DoD-12 — Reproducibility

Một Phase 4 run phải định danh được bằng:

$$
R=
(
git\_commit,
artifact\_schema,
trace\_schema,
normalizer\_profile,
normalizer\_version,
dataset\_hash,
seed
).
$$

---

# CXXVII. Output cuối Phase 4

Repository nên có:

```text
src/react_agent/
│
├── normalization/
│   ├── base.py
│   ├── profiles.py
│   ├── unicode.py
│   └── features.py
│
├── artifacts/
│   ├── model.py
│   ├── labels.py
│   ├── factory.py
│   └── store.py
│
├── provenance/
│   ├── graph.py
│   └── relations.py
│
├── state/
│   └── control_state.py
│
├── policy/
│   ├── decision.py
│   ├── hooks.py
│   └── passthrough.py
│
└── context/
    └── context_bundle.py
```

Configs:

```text
configs/
├── normalization/
│   ├── raw.yaml
│   ├── unicode_only.yaml
│   └── security_v1.yaml
│
└── agent/
    └── A0.yaml
```

Tests:

```text
tests/
├── normalization/
├── artifacts/
├── provenance/
├── state/
└── integration/
```

Documentation:

```text
docs/
├── phase4_design.md
├── normalization_spec.md
├── artifact_model.md
├── sensitivity_trust_model.md
├── provenance_spec.md
├── integration_contract.md
├── trace_schema_v2.md
└── phase4_report.md
```

---

# CXXVIII. Trạng thái dự án khi kết thúc Phase 4

Sau Phase 1–4, hệ thống phải có bốn lớp nền:

$$
\boxed{Execution}
$$

A0 ReAct + 8 tools + broker.

$$
\boxed{Benchmark}
$$

250 clean + 350 attack variants + 350 benign controls.

$$
\boxed{Representation}
$$

raw/normalized views + artifacts + sensitivity/trust.

$$
\boxed{Observability}
$$

trace + provenance graph + control state.

Ta chưa có defense mạnh.

Nhưng giờ ta đã có đủ substrate để viết:

$$
A1,\ldots,A6.
$$

Đây là trạng thái lý tưởng trước Phase 5.

---

## Điểm logic quan trọng nhất của Phase 4

Phase này **không nên cố gắng làm hệ thống “an toàn hơn” ngay lập tức**.

Nó phải làm hệ thống:

$$
\boxed{
\text{quan sát được}
+
\text{có nguồn gốc}
+
\text{có metadata}
+
\text{có extension points}
}
$$

trước.

Nếu vừa xây provenance vừa viết rule block attack, khi A6 tốt hơn A0 ta sẽ khó biết improvement đến từ:

* normalization;
* metadata;
* prompt;
* gate;
* regex;
* provenance;
* hay một thay đổi vô tình trong runtime.

Do đó ranh giới tốt nhất là:

$$
\boxed{
Phase\ 4:
Tracking\ without\ enforcement
}
$$

sau đó:

$$
\boxed{
Phase\ 5:
Enforcement\ on\ top\ of\ frozen\ tracking\ substrate.
}
$$

Cách chia này cũng phù hợp với bản Word: tuần 9–10 xây cấu trúc an toàn và giao tiếp giữa các thành phần, rồi tuần 11–14 mới triển khai A1–A6. 
