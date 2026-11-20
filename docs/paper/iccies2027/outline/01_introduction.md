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
