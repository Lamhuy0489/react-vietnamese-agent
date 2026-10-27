# Structured API Dev pilot v1

Updated 2026-09-28. This is a prospective Phase 5 Dev diagnostic for the
Qwen3-8B task agent and Llama3.2-3B guard served by the two private Kaggle
notebooks. It is not a Phase 5 acceptance receipt, a final A0–A6 comparison,
or a held-out Test result.

## Frozen scope and execution

- Manifest: `build/evaluation/structured_api_dev_v1/manifest.json`.
- Run: `build/evaluation/structured_api_dev_v1/pilot01/`.
- Manifest identity: `4bc1bca5309d0a8c459050102177d8fbde29da9028cb68da6745b68e64972f4b`.
- 21 public clean Dev tasks, selected before inference, with three tasks per
  clean category.
- 16 guard controls: eight attack and eight matched benign records from the
  public Dev release.
- 37/37 terminal task checkpoints; zero missing, failed or interrupted
  checkpoints after safe resume. A transient `started` marker was observed
  while the first invocation was still finishing; the final artifact contains
  no interrupted task and resume never issued a duplicate completed task.
- `test_tasks_loaded=0` and `private_ground_truth_loaded=0` in the runtime
  manifest. The private Dev oracle was read only by the evaluator after the
  run, outside prompts, policy and API requests.
- No notebook rebuild or resubmission was needed. The existing Qwen and Llama
  workers reported `RUNNING` and `READY` during admission.

## Results

The clean utility evaluator reports **3/21 successes (14.29%)**. Terminal
statuses were 10 completed, one max-steps and 10 model-error. The ten model
errors were retained as eight `HTTP_ERROR` and two `TIMEOUT` backend outcomes;
they were not retried. A completed
terminal state is not treated as semantic success; the evaluator checked final
facts, arguments, required evidence, tool sequence and error recovery against
the private Dev oracle after inference.

The agent made 50 bounded generation attempts and 40 successful structured API
responses across the 21 tasks. The guard made 16 attempts and returned 16 valid
structured verdicts.

The guard returned a valid structured result for all 16 controls. It marked
five of eight attacks as `SUSPICIOUS` (**62.5% attack detection**) and marked
three of eight benign controls as `SUSPICIOUS` (**37.5% benign flag rate**).
All other controls were `SAFE`; no malformed guard response or backend error
was observed in this pilot.

These numbers are diagnostic evidence for this API/model profile. They are not
directly comparable to historical runs until the same evaluator, task set,
decoding, source identity and audit protocol are bound in a comparison receipt.
The low utility and false-positive rate remain open issues; no prompt or policy
was tuned from held-out data.

## Integrity and limits

The runner binds source hashes, public-input hashes, model revisions, session
IDs, worker hashes, generation settings and A0 runtime bounds. Each task has a
durable state and trace hash; completed and semantic-error tasks are immutable,
and resume is missing-only. The API service performs constrained output
formatting; it does not provide the A6 host provenance, Pre/Post/Final gates or
tool authorization. Therefore this run does not close A2 quality, A6
integration, lifecycle, cumulative A0–A6 differential or formal Phase 5 freeze.

The full repository suite later reported 4,793 passed, one optional native-tqdm
skip and one expected xfail. Two historical document/shutdown pin tests fail
because their frozen wiring receipt hashes differ from the current working
tree; they are unrelated to this runner and were not repaired here.
