"""Typed negative controls and cross-category split regression fixtures."""

from collections import Counter

import pytest

from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.clean_task import (
    AnswerFact,
    ArgumentValidator,
    AuthoringRecord,
    CleanPublicTask,
)
from react_agent.tools.registry import ToolRegistry
from react_agent.validation.clean_comparators import argument_matches, compare, fact_in_text
from react_agent.validation.group_split import assign_groups


@pytest.mark.parametrize(
    ("answer", "expected", "valid"),
    [
        ("2024", 24, False),
        ("-24", 24, False),
        ("24.5", 24, False),
        ("24", 24, True),
        ("820.000 đồng", 820000, True),
        ("8,5", 8.5, True),
    ],
)
def test_numeric_fact_boundaries(answer: str, expected: int | float, valid: bool) -> None:
    fact = AnswerFact(
        fact_id="toy_number", type="number", value=expected, comparator="numeric_equal"
    )
    assert fact_in_text(answer, fact) is valid


def test_date_and_set_comparators() -> None:
    fact = AnswerFact(fact_id="toy_date", type="date", value="2026-09-06", comparator="date_equal")
    assert fact_in_text("Ngày 06/09/2026", fact)
    assert not fact_in_text("Ngày 06/09/2025", fact)
    assert compare(["a", "b"], ["b", "a"], "set_equal")
    assert not compare(["a", "b", "c"], ["a", "b"], "set_equal")
    assert not compare(float("nan"), 0, "numeric_equal")


def test_search_argument_matches_real_tool_contract(registry: ToolRegistry) -> None:
    broker = ToolBroker(registry, TraceLogger())
    args = {"query": "đăng ký học phần", "top_k": 5}
    result = broker.execute("doc_search", args, run_id="qa", task_id="toy", step=1)
    validator = ArgumentValidator(
        tool="doc_search",
        argument="query",
        comparator="retrieval_target",
        retrieval_targets=["DOC_001"],
    )
    assert argument_matches(validator, args, result, broker)
    validator.retrieval_targets = ["NONEXISTENT"]
    assert not argument_matches(validator, args, result, broker)


def test_sql_equivalence_accepts_alias_but_rejects_wrong_record(registry: ToolRegistry) -> None:
    broker = ToolBroker(registry, TraceLogger())
    validator = ArgumentValidator(
        tool="db_query",
        argument="query",
        comparator="db_result_equivalent",
        reference_sql="SELECT 24 AS expected",
    )
    for query, valid in [("SELECT 24 AS alternative", True), ("SELECT 2024", False)]:
        args = {"query": query}
        result = broker.execute("db_query", args, run_id="qa", task_id="toy", step=1)
        assert argument_matches(validator, args, result, broker) is valid


def test_calculator_uses_result_equivalence(registry: ToolRegistry) -> None:
    broker = ToolBroker(registry, TraceLogger())
    validator = ArgumentValidator(
        tool="calculator", argument="expression", comparator="exact_normalized", expected="4*6"
    )
    for expression, valid in [("6 * 4", True), ("4+6", False)]:
        args = {"expression": expression}
        result = broker.execute("calculator", args, run_id="qa", task_id="toy", step=1)
        assert argument_matches(validator, args, result, broker) is valid


def toy_task(index: int, category: str, group: str) -> CleanPublicTask:
    return CleanPublicTask.model_validate(
        {
            "task_id": f"clean_{index:04d}",
            "category": category,
            "scenario_family": "toy_scenario",
            "template_family": "toy_template",
            "instance_group_id": group,
            "domain": "synthetic",
            "difficulty": "easy",
            "instruction": f"Synthetic group fixture number {index}.",
            "authoring": AuthoringRecord(
                assigned_owner="huy", created_at="2026-09-06"
            ).model_dump(),
        }
    )


def test_cross_category_groups_are_indivisible_and_exact() -> None:
    tasks = [
        toy_task(1, "single_source", "SHARED"),
        toy_task(2, "error_recovery", "SHARED"),
        toy_task(3, "single_source", "SINGLE"),
        toy_task(4, "error_recovery", "RECOVERY"),
    ]
    quotas = {"single_source": 1, "error_recovery": 1}
    result = assign_groups(tasks, quotas, seed=2026)
    assert result["clean_0001"] == result["clean_0002"]
    assert Counter(t.category for t in tasks if result[t.task_id] == "dev") == Counter(quotas)
    assert assign_groups(tasks, quotas, seed=2026) == result


def test_impossible_group_quota_fails() -> None:
    tasks = [toy_task(1, "single_source", "SHARED"), toy_task(2, "single_source", "SHARED")]
    with pytest.raises(ValueError, match="no group-wise assignment"):
        assign_groups(tasks, {"single_source": 1}, seed=2026)
