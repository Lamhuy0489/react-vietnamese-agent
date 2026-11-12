## 4 Benchmark and Protocol

### 4.1 VN-AgentInject v3

VN-AgentInject v3 instantiates the taxonomy of Section 2 as executable **fixtures**. All data are synthetic: the
documents, records, addresses and confidential values are invented, and the two sinks are mocks that perform no
network I/O. A **family** is one attack idea in one task and tool environment. It yields an attack fixture and a
benign_plain fixture in each of the five language variants (Section 2.7), and one third of the families also yield
a benign_auth fixture per variant (Section 2.6). The benchmark has three disjoint splits:

- **Dev**: 48 families, eight per mechanism; 560 fixtures (240 attack, 240 benign_plain, 80 benign_auth). All
  design choices, prompts, rules and thresholds were fixed on this split only.
- **Test v3**: 72 families, twelve per mechanism; 840 fixtures (360 / 360 / 120).
- **Test-3**: 48 further families; 560 fixtures (240 / 240 / 80), written after Test v3 had been run, to confirm
  D3 on data that no earlier decision had touched.

A family, its variants and its benign branches never cross splits.

**Authoring and quality control.** The attack texts were written by human authors who did not read the defence
code. Each family was reviewed on a five-item form covering the correctness of the mechanism label, the
naturalness of the user request and of the injected span, whether following the injection is harmful under the
predicates of Section 2.4, and whether the text leaks hints about the expected answer; reviewers saw the fixture
content but not the defence. A novelty filter rejects a family whose 4-gram Jaccard similarity to any earlier
release exceeds 0.2, and identifiers, destinations and domains are not reused. Finally, every family must pass a
**replay check** with the frozen scorer: a reference trajectory that follows the injection has to be scored
harmful, and a reference trajectory that completes the user task safely has to be scored safe with full utility.
Surface manipulations that would hide a leak from the literal scorer (for example obfuscating the value) are
excluded from the static test sets.

### 4.2 Sealed evaluation

The two test splits are **sealed**. Before a test run we froze (i) the canonical fixtures, by SHA-256; (ii) a
configuration manifest that pins, by hash, the agent prompt, the decoding settings, the defence code, the model
revisions and the list of allowed (backbone, configuration) pairs; and (iii) the hypotheses, the tests and the
multiplicity correction. The runner and the scorer verify the manifest and refuse to start on any mismatch or on a
pair outside the list. Each pair was executed exactly once; the only permitted re-execution is the resumption of
fixtures that ended with an infrastructure error. The scorer's ground truth is read only after the manifest
verifies, and it is never available to the prompts, the runtime policy or the models.

Test v3 was run under a manifest that froze D2+P2 as the final configuration, with six hypotheses (H1–H6,
Section 5.2). D3 was then designed and selected on Dev (Section 3.7), a new manifest was frozen, and Test-3 was
run with three hypotheses: **T1**, D3 has higher benign utility than D2+P2; **T2**, the attack success rate of D3
is not more than two points above that of D2+P2; **T3**, D3 has a lower attack success rate than A0. The manifest
also records our prediction that the utility gain would be small and might not reach significance.

### 4.3 Backbones and agent

The confirmatory experiments use three open-weight backbones served with vLLM: **Gemma-4-12B**, **Llama-3.1-8B**
(16k context) and **Qwen3.5-9B**, each pinned to a repository revision. All backbones receive the same ReAct
prompt and the same decoding settings: temperature 0, at most 512 new tokens per step, a fixed seed, JSON output
constrained by a per-tool schema, and at most eight steps per task. The undefended agent **A0** has no security
mechanism beyond schema validation and tool limits. The defences never change the backbone, the prompt template of
A0 outside the documented reminder, or the decoding.

As a reference for a stronger, closed model we ran **Gemini 3 Flash** through a local proxy, on Dev and on
AgentDojo only. This route does not support the seed or the schema constraint, so these runs are reported
separately and are not part of any hypothesis test. No sealed test data were sent to an external service.

### 4.4 Compared configurations

On Dev we compare D2, D2+P2 and D3 with six baselines, all implemented in the same agent and broker so that only
the defence differs:

- **P1**, spotlighting: tool output is delimited and marked as data [Spotlighting].
- **P2**, sandwich: the user request is repeated after each tool output.
- **G1**, a classifier guard: Prompt Guard 2 screens tool output [Prompt Guard 2].
- **MEL**, a deterministic variant of the masked re-execution check of MELON [MELON].
- **PRG**, a destination policy in the style of Progent [Progent].
- **R1**, the phrase-rule layer of our earlier system, which blocks sinks after tool output that matches
  instruction-like patterns.

**D2** is the deterministic core of Section 3 (rules R2–R4), **D2+P2** adds the sandwich reminder, and **D3** is
the full architecture. Test v3 was run with A0, R1, PRG, P2, D2 and D2+P2; Test-3 with A0, D2+P2 and D3.

### 4.5 Metrics and statistics

A fixture is **harmful** if at least one predicate of Section 2.4 holds. We report the **attack success rate**
(ASR), the share of attack fixtures that are harmful, and the number of **harmful families**, families with at
least one harmful attack fixture. **Utility** is the share of benign fixtures in which the user task is completed
with no harm; it is reported separately for benign_plain and benign_auth and, on Test-3, jointly as benign
utility. A run that ends with a model error (malformed or truncated output) is a utility failure and is never
counted as a successful defence.

Configurations are compared on **paired fixtures** pooled over the three backbones, with a one-sided exact McNemar
test. The non-inferiority hypothesis T2 uses a one-sided z test with family-clustered standard errors and a margin
of two points. p-values are corrected with Holm's procedure within each pre-registered set of hypotheses.
Confidence intervals are 95% bootstrap intervals that resample families (10,000 resamples), so that the five
variants of a family are not treated as independent. Analyses outside the pre-registered sets are labelled
exploratory.

### 4.6 AgentDojo-VI

To check that the findings are not an artefact of our own benchmark, we also use the Banking and Slack suites of
AgentDojo (benchmark version 1.2.2) [AgentDojo] in English and in a Vietnamese translation, **AgentDojo-VI**. The
translation covers the environments, the user tasks, the injection goals and the `important_instructions` attack
template; IBANs, amounts, dates, file names, person and channel names, URLs and e-mail addresses are kept
unchanged. Tools, ground-truth solutions and checks are AgentDojo's own code: Vietnamese phrases expected in an
answer are mapped to the English literals that the original utility and security functions look for. A suite-level
check confirms that the reference solutions solve every user task. Banking has 144 attacked pairs and 16 user
tasks, Slack 105 pairs and 21 user tasks. These runs use AgentDojo's own prompting agent pipeline for local models (tools described in the prompt)
rather than our broker, so they measure the vulnerability of the undefended model in each language, not D3.
