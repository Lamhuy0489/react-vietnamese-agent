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
