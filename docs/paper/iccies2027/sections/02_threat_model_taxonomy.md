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
