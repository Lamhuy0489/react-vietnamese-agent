# Runbook nhanh

## Kiểm tra local

```bash
make check
python -m pytest --cov=react_agent --cov-branch --cov-report=term-missing
```

## Chạy smoke deterministic

```bash
python scripts/build_smoke_environment.py
python scripts/run_smoke.py --backend replay
python scripts/validate_phase1_run.py results/phase1/<run_id>
```

## Chuẩn bị Kaggle bundle

Chỉ bundle từ worktree sạch và commit đã freeze:

```bash
make kaggle-bundle
make kaggle-bundle-validate
```

Trước khi tạo Dataset version mới, tăng `--dataset-version` trong target
`kaggle-bundle`. Không push kernel nếu mô phỏng bundle chưa pass.

## Tải lại authoritative artifacts

```bash
KAGGLE_CONFIG_DIR=<credential-dir> python -m kaggle kernels output \
  huylmhuhu/react-vietnamese-agent-phase-1-real-model-smoke \
  -p results/phase1/kaggle_v4 -o
```

Không commit credential hoặc raw results. Dùng hash trong
`experiments/manifests/phase1_kaggle_v4.json` để đối chiếu.
