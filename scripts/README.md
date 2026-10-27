# Scripts

Only the scripts below belong to the current workflow (roadmap v2, rebuild A).
The other ~280 files are historical Phase 1–5 runners, audits and package
builders. They stay at their paths because about 200 receipts in
`experiments/manifests/` and the Phase 5 wiring QA pin those paths and bytes;
moving them would break the audits that tag `phase5-closure` preserves. Do not
extend them; new work goes into a new script listed here.

## Serving (Kaggle, one model per notebook)

| Script | Use |
|---|---|
| `launch_vllm_serve_v1.py` | `prepare` a private vLLM notebook for a model key, `discover` its encrypted endpoint |

## Clean benchmark (RQ1)

| Script | Use |
|---|---|
| `run_smoke_api_v1.py` | A0 smoke, 20 tasks |
| `run_clean_dev_api_v1.py` | A0 clean Dev, 150 tasks, resumable |
| `evaluate_clean_rebuild_v1.py` | Score clean Dev (`--full-dev --numfix`) |
| `export_clean_dev_faults_v1.py` | Regenerate `configs/clean/dev_fault_plans_v1.json` |

## Adversarial benchmark (RQ2/RQ3)

| Script | Use |
|---|---|
| `run_adversarial_dev_api_v1.py` | A0–A6 on the 400 Dev fixtures, resumable |
| `evaluate_adversarial_dev_v1.py` | ASR, utility, false block, CIs and McNemar from saved runs |
| `run_guard_bakeoff_pg2_v1.py` | Guard bake-off (done 2026-10-26) |
| `assemble_adversarial_release.py --action check` | Verify the release seal |

## Repository checks

| Script | Use |
|---|---|
| `verify_setup.py` | Setup and credential guardrails |
| `validate_knowledge.py` | `make knowledge-check` |

Commands and environment variables: [rebuild runbook](../knowledge/rebuild_a_runbook.md).
