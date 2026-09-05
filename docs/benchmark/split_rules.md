# Split Rules

1. Assign canonical families first: 40 Dev and 30 held-out Test.
2. Generate all five variants after assignment.
3. Keep canonical, all variants, and the matched benign family in one split.
4. Enforce disjoint scenario/template/entity groups where the phase contract
   requires it.
5. Seal Test with a manifest covering data, environment, schemas, and hashes.
6. Never inspect Test failures to modify prompts, defenses, or thresholds.

The robustness set uses 50 canonicals selected from clean held-out Test before
sealing, with five meaning-preserving variants per canonical.
