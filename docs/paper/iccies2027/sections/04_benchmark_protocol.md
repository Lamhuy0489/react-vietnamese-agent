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
