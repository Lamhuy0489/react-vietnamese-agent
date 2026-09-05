"""Phase 2 clean-benchmark contracts with public/private separation."""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

ToolName: TypeAlias = Literal[
    "doc_search",
    "doc_read",
    "db_query",
    "cached_search",
    "cached_fetch",
    "calculator",
    "send_email_mock",
    "post_webhook_mock",
]
Category: TypeAlias = Literal[
    "single_source",
    "parameter_extraction",
    "multi_step",
    "db_document",
    "ambiguous",
    "error_recovery",
    "no_tool",
]
Difficulty: TypeAlias = Literal["easy", "medium", "hard"]
Split: TypeAlias = Literal["pool", "dev", "test"]
ExpectedOutcome: TypeAlias = Literal["answer", "clarification", "acknowledgement"]
Comparator: TypeAlias = Literal[
    "exact_normalized",
    "case_insensitive",
    "date_equal",
    "numeric_equal",
    "numeric_tolerance",
    "set_equal",
    "set_contains",
    "boolean_equal",
    "substring_normalized",
    "entity_id_equal",
    "retrieval_target",
    "db_result_equivalent",
]
FactValue: TypeAlias = str | int | float | bool | list[str]


class EnvironmentRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["clean_env_v1"] = "clean_env_v1"


class AuthoringRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_by: Literal["codex"] = "codex"
    assigned_owner: Literal["huy", "minh"]
    created_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class CleanPublicTask(BaseModel):
    """Only this record may be adapted into a model-visible prompt."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(pattern=r"^clean_[0-9]{4}$")
    split: Split = "pool"
    category: Category
    scenario_family: str = Field(min_length=3)
    template_family: str = Field(min_length=3)
    instance_group_id: str = Field(pattern=r"^[A-Z0-9_]+$")
    domain: str = Field(min_length=3)
    difficulty: Difficulty
    instruction: str = Field(min_length=12)
    tags: list[str] = Field(default_factory=list)
    environment: EnvironmentRef = Field(default_factory=EnvironmentRef)
    authoring: AuthoringRecord
    schema_version: Literal["clean_task_v1"] = "clean_task_v1"

    def prompt_payload(self) -> dict[str, str]:
        """Return the deliberately minimal model-visible task payload."""

        return {"task_id": self.task_id, "instruction": self.instruction}


class AnswerFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=3)
    type: Literal["string", "date", "number", "money", "boolean", "entity", "set"]
    value: FactValue
    comparator: Comparator
    currency: Literal["VND"] | None = None
    tolerance: float | None = Field(default=None, ge=0)


class ArgumentValidator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ToolName
    argument: str = Field(min_length=1)
    comparator: Comparator
    expected: FactValue | None = None
    retrieval_targets: list[str] = Field(default_factory=list)
    reference_sql: str | None = None

    @model_validator(mode="after")
    def validate_comparator_inputs(self) -> ArgumentValidator:
        if self.comparator == "retrieval_target" and not self.retrieval_targets:
            raise ValueError("retrieval_target requires retrieval_targets")
        if self.comparator == "db_result_equivalent" and not self.reference_sql:
            raise ValueError("db_result_equivalent requires reference_sql")
        return self


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: Literal["document", "cached_page", "database", "user"]
    source_id: str = Field(min_length=2)


class OracleStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ToolName
    arguments: dict[str, str | int | float | bool]


class FaultSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ToolName
    occurrence: int = Field(ge=1)
    error_code: Literal[
        "TEMPORARY_UNAVAILABLE",
        "TIMEOUT_SIMULATED",
        "NOT_FOUND",
        "EMPTY_RESULT",
        "INVALID_QUERY",
        "RATE_LIMIT_SIMULATED",
    ]
    retryable: bool


class RecoveryRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    must_observe_error: bool = True
    must_recover: bool = True
    final_task_success: bool = True


class CleanGroundTruth(BaseModel):
    """Private evaluator-only record; never include it in model context."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(pattern=r"^clean_[0-9]{4}$")
    expected_outcome: ExpectedOutcome
    required_tools: list[ToolName]
    optional_tools: list[ToolName] = Field(default_factory=list)
    forbidden_tools: list[ToolName] = Field(default_factory=list)
    acceptable_sequences: list[list[ToolName]]
    order_constraints: list[tuple[ToolName, ToolName]] = Field(default_factory=list)
    argument_validators: list[ArgumentValidator] = Field(default_factory=list)
    required_answer_facts: list[AnswerFact]
    retrieval_targets: list[str] = Field(default_factory=list)
    required_evidence: list[EvidenceRef] = Field(default_factory=list)
    minimum_required_steps: int = Field(ge=0)
    missing_slots: list[str] = Field(default_factory=list)
    acceptable_clarification_terms: list[str] = Field(default_factory=list)
    fault_plan: list[FaultSpec] = Field(default_factory=list)
    recovery_requirement: RecoveryRequirement | None = None
    oracle_steps: list[OracleStep] = Field(default_factory=list)
    schema_version: Literal["clean_ground_truth_v1"] = "clean_ground_truth_v1"

    @model_validator(mode="after")
    def validate_outcome_contract(self) -> CleanGroundTruth:
        if not self.acceptable_sequences:
            raise ValueError("at least one acceptable sequence is required")
        if self.expected_outcome == "clarification":
            if not self.missing_slots or not self.acceptable_clarification_terms:
                raise ValueError("clarification requires slots and accepted terms")
            if self.required_tools:
                raise ValueError("clarification tasks must not require tools")
        if self.fault_plan and self.recovery_requirement is None:
            raise ValueError("fault plan requires a recovery requirement")
        if self.recovery_requirement is not None and not self.fault_plan:
            raise ValueError("recovery requirement requires a fault plan")
        if not self.required_tools and self.acceptable_sequences != [[]]:
            raise ValueError("no-tool ground truth must accept the empty sequence")
        return self


class ReviewChecks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clarity: bool
    solvability: bool
    ground_truth: bool
    tool_path: bool
    arguments: bool
    alternative_paths: bool
    distractors: bool
    category: bool
    leakage: bool
    synthetic_privacy: bool


class CleanReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(pattern=r"^clean_[0-9]{4}$")
    review_mode: Literal["automated_owner_accepted"] = "automated_owner_accepted"
    checks: ReviewChecks
    decision: Literal["approved", "rejected"]
    accepted_by: Literal["project_owner"] = "project_owner"
    reviewed_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: list[str] = Field(default_factory=list)
    schema_version: Literal["clean_review_v1"] = "clean_review_v1"
