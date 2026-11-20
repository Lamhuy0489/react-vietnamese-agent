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
