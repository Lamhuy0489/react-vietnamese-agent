# Research Contract

Status: **frozen for implementation**, except named model identities and exact
generation parameters, which are selected and frozen before final experiments.

## Research questions

1. RQ1: How capable is a Vietnamese ReAct tool agent on normal tasks?
2. RQ2: Do A0–A6 reduce attacks, leakage, and policy violations while retaining
   legitimate utility?
3. RQ3: How do Vietnamese surface variations affect capability and security?

## Scope

- One ReAct agent; no multi-agent system.
- Existing LLMs only; no primary-experiment fine-tuning.
- Eight deterministic mock tools in a synthetic university environment.
- No real Internet use in the core benchmark and no real external side effects.
- Observable actions/results only; no hidden chain-of-thought collection.

## Frozen design decisions

- Capability experiment targets **three LLM backbones**; exact models remain a
  pre-experiment configuration decision.
- Security experiment holds one selected backbone fixed across A0–A6.
- A0–A6 are cumulative defense levels; each level preserves prior components
  unless an explicit ablation is separately named.
  Preserving a component means its checks still run; a later level may refine
  a coarse earlier veto only with more precise evidence (A6 discharges A3–A5
  session vetoes for a sink call whose destination and payload values are proven
  to come from the user; decision log 2026-10-26). Rule and guard vetoes are never
  refined away.
- Attack split occurs before variant generation: 40 canonical families produce
  200 Dev variants and 30 families produce 150 held-out Test variants.
- Each benign control stays in the same split as its matched attack family.
- Robustness canonicals are a frozen 50-task subset of the 100 clean held-out
  Test tasks, selected before Test sealing; five variants yield 250 variants.

## Dataset targets

| Dataset | Canonical | Variants | Dev/Test |
|---|---:|---:|---|
| Clean | 250 | — | 150 / 100 |
| Attack | 70 | 350 | 200 / 150 variants |
| Benign controls | 70 matched | 350 | paired with attack splits |
| Clean robustness | 50 | 250 | held-out evaluation only |

The root Word document remains the approved master scope; this contract makes
the four previously ambiguous implementation decisions explicit.

## Study 2 amendment (owner decision 2026-11-05)

Everything above is frozen and governs **Study 1** (rebuild A). Study 2 extends the scope as
follows and is governed by `rebuild_b_plan.md`:

- RQs for Study 2: capability across 5 backbones and VI vs EN (AgentDojo-VI); vulnerability by
  attack mechanism M1–M6 and by backbone; defense comparison (D2 vs published baselines) under
  static and adaptive attacks; Vietnamese surface effects on utility, ASR and detectors.
- The security experiment uses several backbones. Defenses are named, non-cumulative configurations,
  not the A0–A6 ladder.
- Besides the synthetic university environment, the AgentDojo Banking and Slack mock environments
  (EN and a Vietnamese translation) are used. They are still synthetic, with no real side effects.
- Dataset v3: Dev 48 / Test 72 attack families × 5 variants, each with its benign pair, plus a
  12-family pilot that never enters Dev or Test.
- Still no fine-tuning by the team. Meta-SecAlign-8B is an existing released model.
