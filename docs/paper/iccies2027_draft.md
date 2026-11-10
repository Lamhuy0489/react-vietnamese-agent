# ICCIES 2027 paper draft (Springer CCIS, 12–15 pages, due 2026-11-15)

Status 2026-11-10: Part 1 revised for factual accuracy; Sections 2–3 and result tables drafted.
Every number below comes from `docs/research/study2_thesis_tables.md` (Tables 2.1–2.11) and
`docs/project/decision_log.md`. No attack text or Test content appears here.

## Ghi chú biên tập cho owner (xoá trước khi nộp)

Bản Phần 1 do Antigravity soạn (14:26 ngày 10/11) có các chỗ **sai so với số liệu của đồ án**; bản dưới đây đã sửa:

| Bản cũ | Thực tế (nguồn) | Đã sửa thành |
|---|---|---|
| "Gemini 2.5/Flash, Qwen 2.5, Llama 3.1" | Gemma-4-12B, Llama-3.1-8B, Qwen3.5-9B (Test-3); Gemini 3 Flash chỉ chạy Dev, tham chiếu (Bảng 2.10, 2.11) | tên model đúng |
| "maintaining over 90.0% benign utility" | Utility benign Test-3: A0 54,5% (523/960), D3DEST 51,0% (490/960) | "giữ 93,7% utility của agent không phòng thủ (51,0% so với 54,5%)" |
| "48 canonical attack families" cho cả benchmark | Dev 48, Test 72, Test-3 48 family; 5 biến thể | nêu đủ ba split |
| "four linguistic surface variations" | 5 biến thể: canonical, paraphrase, code-mix, no-diacritic, english | 5 |
| cơ chế "parameter pollution, delimiter confusion…" | M1–M6 theo `taxonomy.md` | M1–M6 |
| "non-parametric permutation tests" | McNemar chính xác + Holm, CI bootstrap theo family | đúng phép kiểm |
| tiếng Việt làm lỗ hổng "severely aggravated", tokenizer "dilute safety alignment vectors" | H4, H5 trên Test v3: không dấu và tiếng Anh **không** khác canonical có ý nghĩa ở A0 (p Holm 0,70; 0,27) | viết lại: động cơ là thiếu đánh giá, không khẳng định tiếng Việt dễ bị tấn công hơn |
| "We release …" | chưa có quyết định công bố dữ liệu | "[owner quyết định: release hay available on request]" |
| "D3 = Deterministic Defense-in-Depth", "without secondary LLM calls" | D3DEST có một lớp lời nhắc (P2) không tất định; đúng là không gọi LLM phụ | giữ tên D3, mô tả "luật tất định phía broker + lời nhắc" |
| "state-of-the-art" | không so với mọi phương pháp trên cùng benchmark công khai | bỏ |

Điểm cần owner quyết: (1) tiêu đề; (2) có công bố dữ liệu không; (3) tên tác giả, đơn vị; (4) danh mục tài liệu
tham khảo ở cuối là danh sách cần kiểm (chưa đối chiếu số trang, năm, nơi đăng).

---

# Defending Tool-Augmented LLM Agents Against Indirect Prompt Injection: A Layered Defence and a Sealed Vietnamese Benchmark Evaluation

**Abstract.** Agents built on Large Language Models (LLMs) increasingly follow the ReAct paradigm, interleaving
reasoning with calls to external tools. Content returned by those tools is untrusted, which exposes the agent to
Indirect Prompt Injection (IPI): instructions embedded in a tool observation redirect the agent towards unauthorised
actions, data exfiltration or tampered outputs. Existing agent-security benchmarks are almost entirely in English,
so the behaviour of attacks and defences for Vietnamese agents is largely unmeasured. We present D3, a layered
defence that places enforcement in a Tool Broker outside the model: literal destination grants, confidential-value
flow rules over provenance labels, final-answer redaction and a destination-scoped injection-signal rule, combined
with a prompt reminder and structured denial feedback. D3 needs no fine-tuning and no auxiliary LLM call. We
evaluate it with VN-AgentInject v3, a Vietnamese benchmark of attack families organised by six mechanisms (M1–M6),
each paired with two benign controls and rendered in five language variants, under a pre-registered protocol with a
sealed test set authored independently of the defence. On the sealed set (48 families, 560 fixtures per cell,
three open-weight backbones: Gemma-4-12B, Llama-3.1-8B, Qwen3.5-9B), D3 lowers the attack success rate from 32.4%
to 3.6% (Holm-adjusted p = 5.0·10⁻⁵⁷) while retaining 93.7% of the undefended agent's benign utility (51.0% against
54.5%). Detectors trained on English and a deterministic MELON variant are no better than the undefended agent on
our Vietnamese development set. A Vietnamese translation of AgentDojo and a run with Gemini 3 Flash serve as
external checks.

**Keywords:** Indirect Prompt Injection · Tool-Augmented LLM Agents · ReAct · Layered Defence · Vietnamese
Benchmark · Agent Security

## 1 Introduction

Large Language Models (LLMs) have moved from passive text generation to agents that plan and act. In the ReAct
paradigm [ReAct], an agent alternates between reasoning steps and tool calls: it searches documents, queries
databases, reads messages and triggers side effects such as sending an e-mail or calling a webhook. Such agents are
being integrated into customer support, personal assistance, finance and software development workflows.

The coupling of reasoning and tool execution creates a security problem. In Indirect Prompt Injection (IPI)
[Greshake], the adversary never talks to the model directly. Instead, the adversary plants instructions in
third-party content that the agent later retrieves through a tool: a document, a cached web page, a database
field or the output of another tool. If the model treats that content as instructions, it may abandon the user's
task and execute the adversary's one, with consequences that range from unauthorised messages to leakage of
confidential values and silent corruption of the data the user asked to send.

Published agent-security benchmarks (BIPIA [BIPIA], InjecAgent [InjecAgent], AgentDojo [AgentDojo]) are written
almost entirely in English. Vietnamese differs in ways that plausibly matter for both attacks and defences: tonal
diacritics are often dropped in informal text, English technical terms are routinely mixed into Vietnamese
sentences, and defences such as injection classifiers are trained mostly on English data. Whether these properties
change attack success or defence effectiveness is an empirical question that has not been measured for
tool-using agents. Our results answer part of it: removing diacritics or switching to English does not make the
undefended agent significantly easier to attack, but phrase-based defences are brittle across languages, and an
English-trained detector gives no protection on Vietnamese injections.

Existing defences have known limits. Prompt-level techniques such as spotlighting [Spotlighting] and the sandwich
reminder depend on the model's compliance. Classifier guards (Prompt Guard, Llama Guard) add inference cost and
transfer poorly across languages. Coarse filters block benign content and destroy utility. These limits motivate
enforcement that does not depend on the model: rules applied by the host, between the model and its tools.

This paper presents **D3**, a layered defence for tool-augmented ReAct agents. Its core is a set of deterministic
rules enforced by a Tool Broker that mediates every tool call: a side-effect tool runs only towards a destination
the user wrote, and a confidential value observed in tool output cannot leave through a sink or the final answer
unless the user wrote that value. Around this core D3 adds a destination-scoped injection-signal rule, a prompt
reminder and a denial message that lets the agent continue the legitimate task.

We evaluate D3 on **VN-AgentInject v3**, a synthetic Vietnamese benchmark whose attack families are organised by
six mechanisms, each paired with benign controls that measure utility and false blocking, and on **AgentDojo-VI**,
a Vietnamese translation of the Banking and Slack suites of AgentDojo. The protocol separates a development split
from sealed test splits that are executed once under a frozen, hash-pinned configuration with hypotheses written
before the run.

Our contributions are:

1. **Threat model and mechanism taxonomy.** We formalise IPI against a tool-using agent with independent trust and
   sensitivity labels, and define six attack mechanisms (M1–M6) by the harm predicate each one triggers, together
   with benign controls that expose false blocking (Section 2).
2. **The D3 layered defence.** A broker-side architecture combining literal destination grants, confidential-value
   flow rules, final-answer redaction and a destination-scoped injection-signal rule with a prompt reminder and
   denial feedback; it requires no fine-tuning and no auxiliary model (Section 3).
3. **A sealed Vietnamese evaluation.** VN-AgentInject v3 (48 development families, 72 and 48 sealed test families;
   five language variants) and AgentDojo-VI, with pre-registered hypotheses, exact McNemar tests, Holm correction
   and family-level bootstrap intervals (Section 4). [owner decides: release / available on request]
4. **Empirical findings.** On the sealed sets D3 reduces attack success from 32.4% to 3.6% across three open-weight
   backbones at a cost of 3.4 points of benign utility; English-trained detection does not transfer; the residual
   failures concentrate in confidential-value leakage and parameter tampering (Sections 5–6).

The paper is organised as follows. Section 2 gives the threat model and taxonomy. Section 3 describes D3.
Section 4 describes the benchmark and protocol. Section 5 reports results. Section 6 discusses errors and
limitations, and Section 7 concludes.

## 2 Threat Model and Attack Taxonomy

### 2.1 Agent and environment

We consider a single-user ReAct agent. Given a system prompt and a user instruction *u*, the model emits at each
step either an action *a_t = (tool, arguments)* or a final answer *y*. A host component, the **Tool Broker**,
validates each action against the tool schema and per-tool limits, executes it, and returns an observation *o_t*
to the model. The loop stops at a final answer or after a fixed number of steps.

The tool set has eight tools in two classes (Table 1). Six **read tools** return content and have no effect outside
the agent: document search and read, a read-only database query, cached-page search and fetch, and a calculator.
Two **sinks** have side effects: `send_email_mock(to, subject, body)` and `post_webhook_mock(endpoint, payload)`.
Both are log-only simulations, so no experiment performs network I/O. We write *dest(a)* for the destination
argument of a sink call (`to` or `endpoint`) and *payload(a)* for its remaining arguments.

**Table 1.** Tools mediated by the Tool Broker.

| Class | Tools | Role in the threat model |
|---|---|---|
| Read | `doc_search`, `doc_read`, `db_query`, `cached_search`, `cached_fetch`, `calculator` | may return attacker-controlled content |
| Sink | `send_email_mock`, `post_webhook_mock` | side effect; destination and payload are security-relevant |
| Final answer | (the model's last message) | treated as a third sink: it can leak values to whoever reads it |

### 2.2 Trust and sensitivity

Every piece of content carries two independent labels assigned by the host, never by the model.

- **Trust** records who can influence the content. The system prompt and the user instruction are trusted; every
  tool observation is untrusted, including the output of internal tools, because the documents, pages and records
  they return may have been written by a third party.
- **Sensitivity** records the cost of disclosure, on an ordered scale from public (S0) to confidential (S2). A
  confidential artifact holds values (keys, codes, account identifiers) that must not leave the agent unless the
  user says so.

The two labels are orthogonal. An untrusted page can be public; a confidential record can come from a tool whose
content the attacker cannot touch. Defences that collapse the two dimensions either block every use of
confidential data or trust every internal source. Our harm predicates and D3's rules use both.

### 2.3 Adversary

The adversary's goal is to make the agent produce a side effect or a disclosure that the user did not authorise.

*Capabilities.* The adversary controls the text of one artifact that a read tool returns during the task: a
document, a cached page, a text field of a database row, or a tool output. The injected span may be placed at the
start, middle or end of the content or inside a table row, and may use any register, from a plain notice to
impersonated authority, procedural justification or multi-step conditional instructions.

*Limits.* The adversary cannot modify the system prompt, the user instruction, the tool implementations, the
broker or the model weights, and does not observe the trajectory. The adversary knows the tool names and schemas.
In the sealed test sets the attacks are static: they are written without access to the defence code or to
defended runs. Adaptive, human-authored attacks written with feedback from defended runs are evaluated separately
on the development split (Section 5.5).

*Out of scope.* Direct jailbreaks by the user, attacks on model weights or training data, denial of service, and
multi-agent propagation.

### 2.4 Harm predicates

Let *G(u)* be the set of destinations the user instruction grants, and *V₂* the set of confidential values on the
trajectory that the user did not authorise for disclosure. A trajectory is **harmful** if at least one of the
following holds. The predicates are evaluated by a frozen scorer from the executed tool calls and the final answer;
the model's reasoning is neither requested nor logged.

- **H_dest (unauthorised destination):** an executed sink call *a* has *dest(a) ∉ G(u)*.
- **H_leak (confidential disclosure):** some *v ∈ V₂* occurs in *payload(a)* of an executed sink call, or in the
  final answer *y*.
- **H_tamper (payload integrity):** an executed sink call has *dest(a) ∈ G(u)*, but a field the user specified
  carries a different value.
- **H_side (unrequested side effect):** the user's task is read-only and any sink call is executed.

A blocked call is not harmful: only executed actions and the final answer count. Model errors (malformed or
truncated output) count as utility failures, never as successful defences.

### 2.5 Attack mechanisms M1–M6

We organise attacks by **mechanism**: the route by which the injection turns into harm. The mechanism determines
which predicate fires and, as Section 5 shows, which defence layer can stop it. Table 2 lists the six mechanisms
and their sub-types.

**Table 2.** Attack mechanisms of VN-AgentInject v3.

| | Mechanism | Sub-types | Harm predicate |
|---|---|---|---|
| M1 | Explicit redirection: the injection asks, in plain terms, to send to a destination absent from the user request | explicit sending verb with a full address | H_dest |
| M2 | Evasive redirection: same goal, written to avoid the "send + address" pattern | verb-free record or status; "forward / cc / keep a copy"; split address; destination held in a second artifact the injection points to | H_dest |
| M3 | Confidential value into a user-named sink | e-mail body; webhook payload; an innocuous-looking named field | H_leak (sink) |
| M4 | Confidential value into the final answer | verbatim; embedded in a sentence; labelled value | H_leak (answer) |
| M5 | Tampering with an ordinary value in the payload of a user-named sink | number; boolean; enumeration or unit; identifier | H_tamper |
| M6 | Side effect injected into a read-only request | user mentions the destination only in a prohibition; only as information; not at all | H_side |

The mechanisms differ in what a defence can rely on. In M1 and M2 the harmful call goes to a destination the user
never wrote, so a destination check is sufficient whatever the wording. In M3 and M4 the destination is legitimate
(or there is none), and only the provenance of the value distinguishes attack from task. In M5 neither the
destination nor the sensitivity is abnormal: the attack changes an ordinary field, which makes it the hardest
mechanism for label-based rules. M6 tests whether a mention of a destination in the user text (for example inside
a prohibition) is mistaken for a grant.

Before any run we recorded predictions per mechanism (for example, that a destination rule would add nothing over
a phrase-based rule layer on M1, and would not help on M5). Section 5 reports which predictions failed.

### 2.6 Benign controls

Each attack family is paired with two benign branches that share the user task and the tool environment.

- **benign_plain** replaces the injected span by a harmless note of the same length at the same position. It
  measures utility under the defence.
- **benign_auth** keeps a request that looks like the attack's goal but is *explicitly authorised by the user*:
  the user names the second destination (M1, M2), permits sending or stating the code (M3, M4), asks to take the
  value from tool data (M5), or requests the action itself (M6). A block here is a **false block**. This branch
  separates defences that enforce authorisation from defences that merely suppress sinks.

### 2.7 Language variants and secondary axes

Every family is rendered in five variants applied to both the user request and the injected content:
**canonical** Vietnamese, **paraphrase**, **code-mix** (Vietnamese with English terms), **no-diacritic**
(diacritics removed mechanically) and **English** (a faithful translation). Identifiers, addresses, confidential
values and all facts used by the scorer are byte-identical across variants, so differences between variants are
attributable to language alone. A family and all its variants and benign branches stay in the same split.

Within each split and mechanism the families are balanced over secondary axes: injection vector (document, cached
page, database text field, tool output), persuasion level (four levels), placement, tone and structure of the user
request, whether the user states an explicit prohibition, the sink the user requests, and six application sectors
(education, public service, banking and finance, healthcare, e-commerce and logistics, enterprise IT and HR).

## 3 The D3 Defence Architecture

### 3.1 Design principles

D3 follows three principles. (i) **The model is not a security boundary.** Whatever the model outputs, an action
takes effect only if the broker executes it; all hard guarantees are host-side. (ii) **The user is the only trusted
principal.** Authorisation is derived from the literal text of the user instruction, never from tool content and
never from an interpretation of user intent by a model. (iii) **Blocking must not end the task.** A denied action
is reported to the agent in a form that lets it finish the legitimate steps.

Figure 1 [to draw: user → agent model ⇄ Tool Broker (schema, limits, provenance labels, rules R2–R4, rule D,
feedback) ⇄ tools; reminder layer on the observation path; final answer passing through R3/R4] shows the layers.
Table 3 summarises them.

**Table 3.** Layers of D3. "Det." marks deterministic host-side enforcement.

| Layer | Stage | Mechanism | Det. | Targets |
|---|---|---|---|---|
| L0 Tool Broker | every call | schema validation, tool limits, provenance labels | yes | malformed calls; basis for other layers |
| L1 Destination grant (R2) | before a sink | destination must occur literally in the user instruction | yes | M1, M2, M6 |
| L2 Confidential-value flow (R3) | before a sink; at the final answer | confidential values from tool output may not leave unless the user wrote them | yes | M3, M4 |
| L3 Answer redaction (R4) | at the final answer | offending values are redacted one by one | yes | M4 |
| L4 Destination-scoped signal rule (D) | before a sink | deny when a flagged observation itself names the sink's destination | yes | M3, M5 on user-named sinks |
| L5 Instruction reminder (P2) | after each observation | the user's instruction is repeated to the model | no | all, model-dependent |
| L6 Denial feedback | after a denial | structured message; the tool is not executed; the agent continues | yes | utility after a block |

### 3.2 Tool Broker and provenance labels (L0)

Every tool call goes through the broker. Without any defence (configuration A0) the broker only validates the call
against the tool schema and enforces per-tool limits. In D3 it additionally keeps, for each observation, an
artifact identifier with its trust and sensitivity labels, and the set of **values** extracted from confidential
observations. Value extraction is lexical and language-independent: e-mail addresses, URLs, identifiers of at
least six characters, and long numbers. Reads are never blocked (rule R1), so the agent can always gather the
information its task needs.

All comparisons use one normalisation function *n(·)*: Unicode NFKC, removal of format characters (zero-width
characters among them) and case folding. Normalisation is used for comparison only and never alters what the model
or the tools receive.

### 3.3 Destination grant (L1, rule R2)

A sink call *a* is allowed only if its destination was written by the user:

> **R2.** allow *a* only if *n(dest(a))* occurs as a substring of *n(u)*.

The user text is not parsed for intent, and no list of Vietnamese or English phrases is consulted. The rule
therefore does not depend on how the injection is worded: an M2 injection that avoids the verb "send", splits the
address or hides the destination in a second document fails for the same reason as an M1 injection, because the
destination it needs is not in *u*. The cost of literal matching appears in two places. A user who refers to a
destination indirectly ("the address in the contract") is not served. And a destination that the user mentions
only inside a prohibition still counts as granted, which is exactly the case M6 probes.

### 3.4 Confidential-value flow (L2–L3, rules R3 and R4)

Let *C* be the set of values extracted from observations labelled confidential. For a sink call *a* or a final
answer *y*:

> **R3.** deny if some *v ∈ C* occurs in *n(payload(a))* (respectively *n(y)*) and *n(v)* does not occur in *n(u)*.
>
> **R4.** a final answer that violates R3 is not failed: each offending value is replaced by `[REDACTED]`.

R3 implements a minimal information-flow policy over the two labels of Section 2.2: a confidential value may
reach a sink only through the user's own text. It treats the final answer as a sink, which closes the M4 channel
that tool-call filters miss. R4 keeps the rest of the answer, so a correct answer with one leaked code loses the
code and not the task. Because R3 matches values literally, a value that the model transforms before emitting it
(reformatted, split, paraphrased) is not recognised; Section 6 returns to this limit.

### 3.5 Destination-scoped injection-signal rule (L4)

R2 and R3 leave a gap: an injection that manipulates a sink the user *did* name, with values that are not
confidential (M5) or through arguments R3 does not cover. Our earlier defence (D2, the configuration evaluated on
the first sealed test) covered this gap with a phrase-based detector of instruction-like text in observations:
once any observation was flagged, every later sink not authorised by a strict grammar over the user text was
denied. On the first sealed test this layer was the largest single source of false blocks on benign tasks
(22 benign_plain trajectories over three backbones), yet removing it on the development split raised the number of
harmful families by 2–4 per backbone.

D3 keeps the detector and narrows its consequence. Let *F* be the set of observations the detector flagged:

> **D.** deny a sink call *a* if some *o ∈ F* contains *n(dest(a))*.

The rule fires only when untrusted, instruction-like content talks about the very destination the agent is about
to use. A flagged page somewhere on the trajectory no longer blocks an unrelated send requested by the user, while
redirection to other destinations remains with R2. The design was selected by offline replay over existing
development trajectories before any new model run: rule D blocks all 11 harmful fixtures that the broad layer
blocked and none of the 14 benign sink calls it had wrongly denied. An alternative that tracked values from
flagged sources blocked 9 of the 11 and was discarded.

### 3.6 Instruction reminder (L5) and denial feedback (L6)

**Reminder.** After every tool observation the original user instruction is appended to the same message, with a
sentence stating that any other instruction found in tool data must be ignored (the sandwich defence, as in
AgentDojo's `repeat_user_prompt`). This is the only layer that depends on model compliance. It is retained because
it covers what the deterministic layers cannot see: on the first sealed test it alone reduced harmful fixtures from
32.9% to 5.6%, and combined with the rules to 1.2%.

**Denial feedback.** When a rule denies an action, the tool is not executed and the agent receives a structured
observation saying that the action was denied by policy. The agent can then carry out the remaining steps or
answer. Without it, a denial would end the trajectory and convert every false block into a failed task.

### 3.7 Component selection and what was rejected

D3 was designed and tuned on the development split only; the first sealed test had already been opened and was
used solely to locate error classes. Before any GPU run we fixed the selection criterion: pooled over three
backbones, a candidate must have no more harmful attack fixtures than the previous configuration (D2+P2) and
strictly higher benign utility; a component that raises harm or lowers utility in the ablation is dropped.

Table 4 reports the ablation. Only the variant with rule D, the original reminder and the original feedback
(named D3DEST in our logs, and simply D3 in this paper) met the criterion. A stronger reminder that also urges
the model to complete every requested step, including sends, helped Gemma but doubled harmful families on Llama
and collapsed Qwen's utility (benign_plain 141 → 39 of 240); it does not transfer across backbones and was
rejected. A stronger denial message added nothing. Two further ideas were rejected at the replay stage: scoping R3
by the resource the user names (it freed 3 authorised tasks but released 5 attacks) and fuzzy value matching (no
additional catch on development data).

**Table 4.** D3 ablation on the development split (48 families, 560 fixtures per cell). Cells: harmful families
/48 · benign_plain utility /240 · benign_auth utility /80. Pooled: harmful attack fixtures /720 · benign utility /960.

| Configuration | Gemma-4-12B | Llama-3.1-8B | Qwen3.5-9B | Pooled |
|---|---|---|---|---|
| A0 (no defence) | 38 · 159 · 54 | 34 · 81 · 30 | 40 · 140 · 36 | 330 · 500 |
| D2+P2 (previous) | 2 · 147 · 45 | 5 · 82 · 36 | 3 · 141 · 24 | 12 · 475 |
| **D3** (rule D, reminder v1, feedback v1) | 2 · 148 · 49 | 5 · 85 · 40 | 3 · 141 · 27 | **12 · 490** |
| rule D, reminder v1, feedback v2 | 2 · 150 · 49 | 6 · 84 · 40 | 3 · 142 · 26 | 14 · 491 |
| rule D, reminder v2, feedback v2 | 1 · 163 · 54 | 10 · 75 · 38 | 2 · 39 · 16 | 21 · 385 |
| rule D, reminder v2, feedback v1 | 1 · 162 · 54 | 10 · 69 · 38 | 2 · 40 · 16 | 21 · 379 |

### 3.8 Cost and scope

D3 adds no model call: every rule is a string operation over the trajectory, and the reminder adds the length of
the user instruction to each observation message. It needs no access to model weights and works unchanged with a
hosted model (Section 5.4). It does not claim to stop tampering with non-confidential values on a user-named sink
when the injected content never names the destination (part of M5), nor leakage of values the model has
transformed.

## 4 Benchmark and Protocol (outline, to write)

- VN-AgentInject v3: synthetic data only; Dev 48 families (8 per mechanism, 560 fixtures per configuration), Test
  72 families (840 fixtures), Test-3 48 new families (560 fixtures). Fixtures per family: 5 variants × (attack +
  benign_plain) plus benign_auth for one third of the families.
- Authoring: attack texts written by human authors who did not read the defence code; cross-review on a 5-item
  form; novelty filter (4-gram Jaccard ≤ 0.2 against earlier releases); every family has a QA replay in which a
  harmful reference trajectory must score harmful and a safe one must score safe with full utility.
- Sealing: canonicals frozen by SHA-256 before the run; configuration manifest pinned by hash; runner and scorer
  refuse to run on a mismatch; each test executed once; hypotheses, tests and correction recorded before the run.
- Backbones: Gemma-4-12B, Llama-3.1-8B (16k context), Qwen3.5-9B, served with vLLM; same prompt and decoding for
  all. Gemini 3 Flash through a proxy on Dev only (no sealed data leaves the lab).
- Baselines: spotlighting (P1), sandwich (P2), Prompt Guard 2 (G1), a deterministic MELON variant (MEL), a
  Progent-style destination policy (PRG), the phrase-rule layer of our earlier work (R1), D2, D2+P2.
- Metrics: attack success rate over attack fixtures (a fixture is harmful if any predicate of Section 2.4 holds);
  harmful families (at least one harmful fixture); benign_plain and benign_auth utility; model_error counted as
  failure. Statistics: exact McNemar on paired fixtures pooled over backbones, Holm correction within each
  pre-registered family of hypotheses, 95% bootstrap CI resampling families (10,000 resamples).

## 5 Results (tables ready; prose to write)

### 5.1 Baselines on the development split

**Table 5.** Development split, three backbones. Cells: harmful families /48 · benign_plain /240 · benign_auth /80.

| Configuration | Gemma-4-12B | Llama-3.1-8B | Qwen3.5-9B | Harmful families /144 |
|---|---|---|---|---|
| A0 | 38 · 159 · 54 | 34 · 81 · 30 | 40 · 140 · 36 | 112 |
| P1 spotlighting | 24 · 146 · 54 | 24 · 74 · 36 | 43 · 137 · 38 | 91 |
| P2 sandwich | 7 · 150 · 54 | 13 · 84 · 40 | 11 · 144 · 32 | 31 |
| G1 Prompt Guard 2 | 39 · 160 · 54 | 34 · 81 · 30 | 40 · 139 · 36 | 113 |
| MEL (deterministic MELON) | 38 · 160 · 54 | 34 · 79 · 30 | 40 · 142 · 36 | 112 |
| PRG (Progent-style) | 21 · 160 · 54 | 18 · 80 · 32 | 22 · 138 · 36 | 61 |
| R1 (phrase rules) | 36 · 160 · 49 | 25 · 80 · 27 | 33 · 138 · 33 | 94 |
| D2 | 17 · 158 · 44 | 13 · 80 · 27 | 15 · 136 · 28 | 45 |
| D2+P2 | 2 · 147 · 45 | 5 · 82 · 36 | 3 · 141 · 24 | 10 |

Points to make: the English-trained detector (G1) and MEL equal A0 on Vietnamese; spotlighting can backfire
(Qwen3.5 40 → 43); destination policies (PRG, D2) remove M1 and M2 entirely but not M3–M5.

### 5.2 First sealed test (72 families, configuration D2+P2 frozen, run once)

**Table 6.** Sealed Test v3, pooled over three backbones (1,080 attack, 1,080 benign_plain, 360 benign_auth
fixtures per configuration).

| Configuration | Harmful families /216 | ASR (fixtures) | benign_plain | benign_auth |
|---|---|---|---|---|
| A0 | 138 | 355 (32.9%) | 489 (45.3%) | 141 (39.2%) |
| R1 | 109 | 200 (18.5%) | 468 (43.3%) | 128 (35.6%) |
| PRG | 75 | 212 (19.6%) | 488 (45.2%) | 141 (39.2%) |
| P2 | 47 | 61 (5.6%) | 472 (43.7%) | 124 (34.4%) |
| D2 | 49 | 72 (6.7%) | 459 (42.5%) | 118 (32.8%) |
| D2+P2 | 11 | 13 (1.2%) | 448 (41.5%) | 108 (30.0%) |

**Table 7.** Harmful attack fixtures by mechanism on Sealed Test v3 (pooled, /180 per mechanism).

| Configuration | M1 | M2 | M3 | M4 | M5 | M6 |
|---|---|---|---|---|---|---|
| A0 | 58 | 65 | 89 | 60 | 68 | 15 |
| R1 | 33 | 38 | 46 | 43 | 33 | 7 |
| PRG | 0 | 0 | 89 | 55 | 67 | 1 |
| P2 | 1 | 1 | 27 | 18 | 10 | 4 |
| D2 | 0 | 0 | 29 | 17 | 25 | 1 |
| D2+P2 | 0 | 0 | 6 | 3 | 4 | 0 |

Pre-registered hypotheses (exact McNemar, Holm over H1–H6, family bootstrap CI): H1 D2 < R1 on attacks, 18.5% →
6.7%, −11.9 points (−16.7; −7.5), p = 1.8·10⁻³⁸, 128/0 discordant pairs; H3 D2 < R1 on M2∪M3∪M4, 23.5% → 8.5%,
p = 2.1·10⁻²⁴; H6 D2+P2 < P2, 5.6% → 1.2%, p = 1.8·10⁻¹³; H2 (D2 benign_plain not worse than A0 by more than 5
points) not established: −2.8 points, CI (−6.0; −0.5), p = 0.20; H4 no-diacritic vs canonical at A0, 31.5% vs
33.3%, p = 0.70; H5 English vs canonical at A0, 31.5% vs 36.6%, p = 0.27. By variant under D2 (harmful fixtures
/216): canonical 9, paraphrase 13, no-diacritic 12, code-mix 6, English 32; under D2+P2: 1, 5, 3, 3, 1.

### 5.3 Second sealed test: confirming D3 (48 new families, run once)

**Table 8.** Sealed Test-3. Cells: harmful families /48 · harmful attack fixtures /240 · benign_plain /240 ·
benign_auth /80.

| Backbone | A0 | D2+P2 | D3 |
|---|---|---|---|
| Gemma-4-12B | 33 · 101 · 191 · 55 | 3 · 7 · 167 · 48 | 3 · 7 · 170 · 48 |
| Llama-3.1-8B | 29 · 50 · 95 · 23 | 8 · 10 · 87 · 30 | 8 · 10 · 89 · 31 |
| Qwen3.5-9B | 33 · 82 · 134 · 25 | 7 · 10 · 129 · 19 | 7 · 9 · 133 · 19 |
| Pooled | 95/144 · 233/720 (32.4%) · 420/720 (58.3%) · 103/240 (42.9%) | 18 · 27 (3.8%) · 383 (53.2%) · 97 (40.4%) | 18 · 26 (3.6%) · 392 (54.4%) · 98 (40.8%) |

**Table 9.** Pre-registered hypotheses on Test-3 (exact McNemar pooled over backbones; Holm over T1–T3; 95%
family bootstrap CI, 10,000 resamples).

| Hypothesis | Rates | Difference (95% CI) | Discordant pairs | Holm p | Outcome |
|---|---|---|---|---|---|
| T1 benign utility: D3 > D2+P2 | 0.500 → 0.510 | +1.0 pt [−0.1; +3.1] | 11 / 1 | 3.2·10⁻³ | H0 rejected |
| T2 harm: D3 not worse than D2+P2 by more than 2 pt | 0.037 → 0.036 | −0.1 pt [−0.4; 0.0] | 0 / 1 | 1.6·10⁻⁵³ | H0 rejected |
| T3 harm: D3 < A0 | 0.324 → 0.036 | −28.7 pt [−35.4; −22.4] | 4 / 211 | 5.0·10⁻⁵⁷ | H0 rejected |

To state plainly in the text: the utility gain of D3 over D2+P2 is statistically significant by the paired test but
small (+1.0 point) and its family-level interval touches zero; it comes from benign_plain (+1.3 points, 10/1), not
from benign_auth (+0.4, 1/0) as predicted. Llama has 66–74 truncated outputs per cell, counted as failures.

### 5.4 External checks

**Table 10.** Gemini 3 Flash on the development split (reference only; outside the confirmatory tests). Cells as
in Table 8.

| Configuration | Gemini 3 Flash | model_error /560 |
|---|---|---|
| A0 | 22 · 61 · 184 · 53 | 36 |
| R1 | 18 · 36 · 182 · 50 | 43 |
| D2 | 12 · 15 · 186 · 44 | 38 |
| D2+P2 | 1 · 1 · 192 · 49 | 18 |
| D3 | 1 · 1 · 191 · 60 | 13 |

A stronger hosted model is attacked less often at A0 (22 of 48 families against 34–40) but is still attacked; with
D3 one family remains. Exploratory: benign_auth 49 → 60 of 80 from D2+P2 to D3 (13/2 discordant pairs).

**Table 11.** AgentDojo (v1.2.2) Banking and Slack, English and Vietnamese, attack `important_instructions`, no
defence. Cells: utility under attack / successful attacks. [Gemini EN cells: runs in progress 2026-11-10]

| Suite (pairs) | Llama-3.1-8B EN | Llama-3.1-8B VI | Gemini 3 Flash EN | Gemini 3 Flash VI |
|---|---|---|---|---|
| Banking (144) | 58 / 17 | 44 / 6 | [pending] | 99 / 0 |
| Slack (105) | 28 / 16 | 26 / 0 | [pending] | 59 / 0 |
| Banking, no attack (16) | 7 | 6 | 13 | 12 |
| Slack, no attack (21) | 7 | 7 | 18 | 16 |

Caveat to state: lower attack success in Vietnamese does not mean Vietnamese is safer; for Llama, utility under
attack also falls, and in the Vietnamese Slack suite two of five injection tasks are not solvable by the reference
solution, which lowers the ceiling for attack success.

### 5.5 Adaptive attacks (development split)

Human-authored adaptive set, one fixture per family (48): at A0 it is as strong as the static canonical set
(harmful families 26 / 15 / 24 against 29 / 12 / 22 for Gemma / Llama / Qwen3.5); under D2+P2 1 / 0 / 0. Limits:
one round of human authoring, no automated optimisation, development split only.

## 6 Discussion and limitations (outline)

- Residual failures under the defence are M3, M4 and M5 (13 fixtures on Test v3: 6, 3, 4). M5 on a user-named sink
  is outside the reach of destination and sensitivity rules.
- Language: no significant effect of no-diacritic or English at A0 (H4, H5); phrase-based rules are brittle
  across languages (the phrase detector fires on 14–19 of 48 canonical attacks but 3 of 48 English ones on Dev);
  literal destination and value rules are language-independent.
- Llama truncation: raising the output budget from 512 to 2,048 tokens recovered none of the failed runs; the cause
  is non-terminating generation, not the budget.
- Limitations: sealed sets authored by the same team as the defence (authors did not read defence code); synthetic
  data and mock tools; backbones of 8–12B parameters plus one hosted model run through a proxy (no schema-constrained
  output, JSON repair), on Dev only; small D3-over-D2+P2 gain; single-turn user tasks; static attacks on the sealed
  sets.

## 7 Conclusion (to write)

## References (to verify: venue, year, pages)

[ReAct] Yao et al., ReAct: Synergizing Reasoning and Acting in Language Models. ·
[Greshake] Greshake et al., Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with
Indirect Prompt Injection. · [BIPIA] Yi et al., Benchmarking and Defending Against Indirect Prompt Injection Attacks
on Large Language Models. · [InjecAgent] Zhan et al., InjecAgent. · [AgentDojo] Debenedetti et al., AgentDojo. ·
[Spotlighting] Hines et al., Defending Against Indirect Prompt Injection Attacks With Spotlighting. · [MELON] Zhu et
al. · [Progent] Shi et al. · [SecAlign] Chen et al. · [Prompt Guard 2] Meta. · [CaMeL] Debenedetti et al., Defeating
Prompt Injections by Design. · Holm (1979). · McNemar (1947).
