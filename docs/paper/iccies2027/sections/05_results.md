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
