from __future__ import annotations

from pathlib import Path

import pytest

from react_agent.adversarial_release import ReleasedFixture, load_split
from react_agent.authoring.selected_runtime import SelectedCase, load_selected
from react_agent.authoring.workbench_qa import RecordingReplay
from react_agent.evaluation.adversarial_v1 import prepare_registry, score_execution, summarize
from react_agent.evaluation.statistics_v1 import mcnemar_exact, rate_with_ci
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.phase5_closure_runtime_v1 import Phase5ClosureRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog

ROOT = Path(__file__).resolve().parents[2]


class SafeGuard:
    model_id, model_revision = "fake/guard", "r1"

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        return ModelResponse(text='{"risk":"SAFE","labels":[],"confidence":"HIGH"}',
                             model_id=self.model_id, model_revision=self.model_revision)


class SafeGuardFactory:  # module level: the warm guard pickles it into a child process
    def __call__(self) -> LLMBackend:
        return SafeGuard()


@pytest.fixture(scope="module")
def inputs() -> tuple[dict[str, ReleasedFixture], dict[str, SelectedCase]]:
    rows = {row.variant_id: row for row in load_split(ROOT / "data/adversarial/release_v2")}
    return rows, load_selected(ROOT)[1]


def execute(tmp_path: Path, row: ReleasedFixture, case: SelectedCase, level: Level,
            fixture: str) -> dict[str, object]:
    oracle = case.candidate.oracle
    actions, final = ((oracle.negative_actions, oracle.negative_final) if fixture == "negative"
                      else (oracle.safe_actions, oracle.safe_final))
    config = configuration(level)
    runtime = Phase5ClosureRuntime(
        RecordingReplay(actions, final),
        prepare_registry(row, ROOT / "data/clean/v1_1/environment", tmp_path / "environment"))
    runtime.run_instrumented(
        row.task, output=tmp_path / "execution", source_catalog=fixture_catalog(row),
        security_config=config, guard_factory=SafeGuardFactory() if config.llm_guard else None,
        guard_execution=WarmGuardConfig("fake/guard", "r1", 30) if config.llm_guard else None)
    return score_execution(case, tmp_path / "execution",
                           tmp_path / "environment/database/university.db")


def test_a0_negative_attack_is_harmful_and_a1_blocks_it(tmp_path: Path, inputs) -> None:
    rows, cases = inputs
    row = rows["ATK_CAND_AGGREGATE_CODE_MIX"]
    a0 = execute(tmp_path / "a0", row, cases[row.task.task_id], "A0", "negative")
    assert a0["harmful"] and a0["executed_violations"] == 1 and a0["status"] == "completed"
    a1 = execute(tmp_path / "a1", row, cases[row.task.task_id], "A1", "negative")
    assert not a1["harmful"] and a1["denied"]


def test_safe_benign_keeps_utility_and_overlaid_calculator_runs_at_a6(
    tmp_path: Path, inputs
) -> None:
    rows, cases = inputs
    row = rows["BEN_CAND_AGGREGATE_CODE_MIX"]
    assert execute(tmp_path / "a0", row, cases[row.task.task_id], "A0", "safe")["utility"]
    calculator = rows["BEN_CAND_AUDITFLAG_CODE_MIX"]  # overlay wraps calculator
    a6 = execute(tmp_path / "a6", calculator, cases[calculator.task.task_id], "A6", "safe")
    assert a6["status"] == "completed" and not a6["harmful"]


def test_summary_rates_and_paired_test() -> None:
    def record(level: str, variant: str, branch: str, harmful: bool, utility: bool) -> dict:
        return {"level": level, "variant_id": variant, "branch": branch,
                "family_id": "F" + variant[-1], "score": {
                    "status": "completed", "harmful": harmful, "utility": utility,
                    "executed_violations": int(harmful), "leaked": False, "denied": not utility}}
    records = [record("A0", f"ATK_{i}", "attack", True, False) for i in range(4)] + [
        record("A1", f"ATK_{i}", "attack", i == 0, True) for i in range(4)] + [
        record("A1", f"BEN_{i}", "benign", False, i != 0) for i in range(4)]
    report = summarize(records)
    assert report["levels"]["A0"]["asr"]["k"] == 4
    assert report["levels"]["A1"]["asr"]["k"] == 1
    assert report["levels"]["A1"]["utility_under_attack"]["k"] == 3
    assert report["levels"]["A1"]["false_block"]["k"] == 1
    assert report["asr_mcnemar"]["A0->A1"] == {"b": 3, "c": 0, "p_value": 0.25}


def test_statistics_helpers() -> None:
    result = rate_with_ci([True, False, True, True], ["a", "a", "b", "c"])
    assert result["k"] == 3 and 0 <= result["ci95"][0] <= result["rate"] <= result["ci95"][1]
    assert mcnemar_exact([True] * 10, [False] * 10)["p_value"] == pytest.approx(2 / 1024)
    assert mcnemar_exact([True], [True])["p_value"] == 1.0


def test_attributable_asr_discounts_harm_the_benign_pair_also_shows() -> None:
    def record(level: str, variant: str, harmful: bool, utility: bool = False) -> dict:
        return {"level": level, "variant_id": variant,
                "branch": "attack" if variant.startswith("ATK_") else "benign",
                "family_id": "F" + variant[-1], "score": {
                    "status": "completed", "harmful": harmful, "utility": utility,
                    "executed_violations": int(harmful), "leaked": False, "denied": False}}
    records = [record("A0", "ATK_F_1", True), record("A0", "BEN_F_1", True),
               record("A0", "ATK_F_2", True), record("A0", "BEN_F_2", False),
               record("A1", "ATK_F_1", True), record("A1", "BEN_F_1", True),
               record("A1", "ATK_F_2", False), record("A1", "BEN_F_2", False, True)]
    report = summarize(records)
    assert report["levels"]["A0"]["asr"]["k"] == 2
    assert report["levels"]["A0"]["attributable_asr"]["k"] == 1
    assert report["levels"]["A1"]["attributable_asr"]["k"] == 0
    assert report["attributable_asr_mcnemar"]["A0->A1"]["b"] == 1
    assert report["benign_utility_mcnemar"]["A0->A1"] == {"b": 0, "c": 1, "p_value": 1.0}
