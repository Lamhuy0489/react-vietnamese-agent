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
