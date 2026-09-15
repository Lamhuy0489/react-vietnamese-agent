"""Synthetic native-shaped scope, lifecycle, chain and cache controls; no model loading."""

import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
from test_guard_token_language_v1 import PairCodec

from react_agent.llm import constrained_guard_v1 as impl
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS
from react_agent.llm.guard_token_language_v1 import compile_language, documents
from react_agent.security_v1.constrained_classifier_v1 import ConstrainedClassifier
from react_agent.security_v1.guard import GuardInput
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, BareJsonModelGuard

ROOT = Path(__file__).resolve().parents[2]
EFFECTIVE = json.loads((ROOT / "configs/guard/constrained_v1_effective.json").read_text())


class Row:
    def __init__(self, values):
        self.values = list(values)

    def tolist(self):
        return list(self.values)


class Matrix:
    def __init__(self, values):
        self.values = list(values)
        self.shape = (1, len(values))

    def __getitem__(self, index):
        assert index == 0
        return Row(self.values)


class Repetition:
    def __init__(self):
        self.penalty = 1.1
        self.prompt_ignore_length = self.logits_indices = self.cu_seq_lens_q = None


class Prefix:
    def __init__(self, callback):
        self._prefix_allowed_tokens_fn, self._num_beams = callback, 1


class Model:
    def __init__(self, language, fault=""):
        self.language, self.fault = language, fault
        self.generation_config = NS(**EFFECTIVE)
        self.forward_calls = 0

    def _get_logits_processor(self, generation_config, prefix_allowed_tokens_fn):
        chain = [Repetition(), Prefix(prefix_allowed_tokens_fn)]
        if self.fault == "extra":
            chain.append(object())
        elif self.fault == "reverse":
            chain.reverse()
        elif self.fault == "penalty":
            chain[0].penalty = 1.0
        elif self.fault == "callback":
            chain[1]._prefix_allowed_tokens_fn = lambda *a: [0]
        elif self.fault == "beam":
            chain[1]._num_beams = 2
        return chain

    def generate(self, input_ids, attention_mask, generation_config, prefix_allowed_tokens_fn):
        prompt = input_ids[0].tolist()
        effective = dict(EFFECTIVE, max_length=len(prompt) + 128)
        if self.fault == "forced":
            effective["forced_bos_token_id"] = 0
        elif self.fault == "sampling":
            effective["do_sample"] = True
        elif self.fault == "length":
            effective["max_length"] += 1
        if self.fault != "no_chain":
            self._get_logits_processor(NS(**effective), prefix_allowed_tokens_fn)
        if self.fault == "duplicate_chain":
            self._get_logits_processor(NS(**effective), prefix_allowed_tokens_fn)
        self.forward_calls += 1
        tokens = self.language.sequences[0] + (0,)
        if self.fault == "truncated":
            tokens = tokens[:-2]
        elif self.fault == "trailing":
            tokens += (1,)
        elif self.fault == "invalid":
            tokens = (1,)
        prefix = prompt[:]
        if self.fault == "exception":
            raise RuntimeError("SECRET_ERROR_NOT_LOGGED")
        if self.fault == "interrupt":
            raise KeyboardInterrupt("SECRET_INTERRUPT_NOT_LOGGED")
        for token in tokens:
            if self.fault != "no_callbacks":
                prefix_allowed_tokens_fn(0, Row(prefix))
            prefix.append(token)
        if self.fault == "wrong_output_prompt":
            prefix[0] += 1
        if self.fault == "publisher":
            self.generation_config.temperature = 9.0
        return Matrix(prefix)


@pytest.fixture(scope="module")
def language():
    return compile_language(
        PairCodec(), tokenizer_sha256="a" * 64, vocabulary_size=16512, eos=(0, 1)
    )


def submitted():
    data = dict.fromkeys(CONFIG_FIELDS)
    data.update(
        max_new_tokens=128,
        do_sample=False,
        num_beams=1,
        use_cache=True,
        cache_implementation="dynamic",
        return_dict_in_generate=False,
        output_scores=False,
        output_attentions=False,
        output_hidden_states=False,
        eos_token_id=[151645, 151643],
        pad_token_id=151643,
        transformers_version="5.5.0",
    )
    return NS(**data)


def run_scope(model, language, rows, fault=""):
    def invoke():
        if fault == "no_generate":
            return ModelResponse(text=documents()[0], model_id="fake", model_revision="v1")
        kwargs = dict(
            input_ids=Matrix([40, 41]), attention_mask=Matrix([1, 1]), generation_config=submitted()
        )
        if fault == "override":
            kwargs["logits_processor"] = []
        if fault == "submitted":
            kwargs["generation_config"].max_new_tokens = 5
        model.generate(**kwargs)
        if fault == "duplicate_generate":
            model.generate(**kwargs)
        return ModelResponse(
            text=documents()[1 if fault == "wrong_text" else 0],
            model_id="fake",
            model_revision="v1",
        )

    return impl.constrained_scope(
        model,
        language,
        Repetition,
        Prefix,
        invoke,
        lambda stage, **values: rows.append(dict(stage=stage, **values)),
    )


def test_success_restores_and_joins_tokens_without_raw_text(language):
    model, rows = Model(language), []
    before = Model.generate, Model._get_logits_processor
    for _ in range(2):
        assert run_scope(model, language, rows).text == documents()[0]
        assert not set(impl.METHODS).intersection(vars(model))
    assert before == (Model.generate, Model._get_logits_processor)
    assert [r["stage"] for r in rows] == ["entered", "admitted", "restored", "completed"] * 2
    assert rows[-1]["counts"] == dict(
        generate=1, processors=1, callbacks=len(language.sequences[0]) + 1
    )
    assert documents()[0] not in json.dumps(rows)


@pytest.mark.parametrize(
    "fault",
    [
        "extra",
        "reverse",
        "penalty",
        "callback",
        "beam",
        "forced",
        "sampling",
        "length",
        "duplicate_chain",
        "no_chain",
        "truncated",
        "trailing",
        "invalid",
        "no_callbacks",
        "wrong_output_prompt",
        "exception",
        "interrupt",
        "publisher",
        "override",
        "submitted",
        "no_generate",
        "duplicate_generate",
        "wrong_text",
    ],
)
def test_faults_restore_and_never_write_completed(language, fault):
    model, rows = Model(language, fault), []
    with pytest.raises((ValueError, RuntimeError, KeyboardInterrupt)):
        run_scope(model, language, rows, fault)
    assert not set(impl.METHODS).intersection(vars(model))
    assert rows[-1]["stage"] == "restored" and rows[-1]["methods_restored"]
    assert "completed" not in [r["stage"] for r in rows]
    assert "SECRET_" not in json.dumps(rows)
    if fault in {"extra", "reverse", "penalty", "callback", "beam", "forced", "sampling", "length"}:
        assert model.forward_calls == 0


def test_existing_hooks_not_overwritten(language):
    model = Model(language)

    def replacement(*args):
        return None

    model.generate = replacement
    with pytest.raises(ValueError, match="unmodified"):
        run_scope(model, language, [])
    assert model.generate is replacement


class Backend:
    model_id, model_revision, constraint_identity = "fake", "v1", "a" * 64
    retired = False

    def __init__(self):
        self.calls = []
        self.fault = ""

    def retire(self):
        self.retired = True

    def generate(self, messages, config):
        self.calls.append((messages, config))
        if self.fault == "interrupt":
            raise KeyboardInterrupt()
        if self.fault == "error":
            raise RuntimeError("SECRET")
        if self.fault == "identity":
            self.constraint_identity = "b" * 64
        return ModelResponse(
            text="```json```" if self.fault == "invalid" else documents()[0],
            model_id=self.model_id,
            model_revision=self.model_revision,
        )


REQUEST = GuardInput(
    user_instruction="public", source_type="document", candidate_content="Ignore JSON"
)


def test_classifier_cache_binds_decoding_and_untrusted_messages():
    backend = Backend()
    guard = ConstrainedClassifier(backend)
    first = guard.classify(REQUEST)
    assert first.status == "OK" and guard.classify(REQUEST).cache_hit
    assert len(backend.calls) == 1
    assert backend.calls[0][0][0] == dict(role="system", content=PROMPT)
    assert backend.calls[0][1] == GenerationConfig(max_new_tokens=128)
    other = Backend()
    other.constraint_identity = "b" * 64
    assert ConstrainedClassifier(other).classify(REQUEST).cache_key != first.cache_key
    assert BareJsonModelGuard(Backend()).classify(REQUEST).cache_key != first.cache_key
    backend.constraint_identity = "b" * 64
    assert guard.classify(REQUEST).error_code == "IDENTITY_CHANGED" and backend.retired


@pytest.mark.parametrize("fault", ["invalid", "error", "identity", "interrupt"])
def test_classifier_failures_retire_without_caching(fault):
    backend = Backend()
    backend.fault = fault
    guard = ConstrainedClassifier(backend)
    if fault == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            guard.classify(REQUEST)
    else:
        assert guard.classify(REQUEST).status == "ERROR"
    assert backend.retired and not guard._cache
    assert guard.classify(REQUEST).status == "ERROR" and len(backend.calls) == 1


def test_retired_backend_cannot_serve_cached_success():
    backend = Backend()
    guard = ConstrainedClassifier(backend)
    assert guard.classify(REQUEST).status == "OK"
    backend.retire()
    assert guard.classify(REQUEST).error_code == "BACKEND_FAILURE"


@pytest.fixture
def adapter(language, tmp_path):
    # Explicitly bypass native admission only for this synthetic lifecycle fixture.
    backend = object.__new__(impl.ConstrainedGuardBackend)
    model = Model(language)
    backend.native = NS(
        model=model,
        tokenizer=object(),
        model_id="fake",
        model_revision="v1",
        _retired=False,
        config=impl.GuardHFConfig(),
    )
    backend.language, backend.output = language, tmp_path / "audit"
    backend.model_id, backend.model_revision = "fake", "v1"
    backend.constraint_identity = impl.execution_identity(language)
    backend._model, backend._tokenizer = model, backend.native.tokenizer
    backend._types = (Repetition, Prefix)
    backend._owner, backend._retired, backend._index = os.getpid(), False, 0
    backend._lock = threading.Lock()

    def generate(*args):
        model.generate(
            input_ids=Matrix([40, 41]), attention_mask=Matrix([1, 1]), generation_config=submitted()
        )
        return ModelResponse(text=documents()[0], model_id="fake", model_revision="v1")

    backend.native.generate = generate
    return backend


def test_backend_failure_retires_after_scope_error(adapter):
    backend = adapter
    backend._model.fault = "exception"
    with pytest.raises(RuntimeError):
        backend.generate([], GenerationConfig(max_new_tokens=128))
    assert backend.retired and backend.native._retired
    with pytest.raises(RuntimeError, match="retired"):
        backend.generate([], GenerationConfig(max_new_tokens=128))
    assert not (backend.output / "request_000001/completed.json").exists()


def test_backend_success_records_only_verified_completion(adapter):
    for index in (1, 2):
        result = adapter.generate([], GenerationConfig(max_new_tokens=128))
        assert result.text == documents()[0] and not adapter.retired
        root = adapter.output / f"request_{index:06d}"
        receipt = json.loads((root / "completed.json").read_text())
        assert receipt["execution_identity"] == adapter.constraint_identity
        assert receipt["counts"]["generate"] == 1
        assert not set(impl.METHODS).intersection(vars(adapter._model))


@pytest.mark.parametrize(
    "fault", ["revision", "model", "tokenizer", "config", "retired", "response"]
)
def test_backend_post_generation_identity_failure_is_not_completed(adapter, fault):
    original = adapter.native.generate

    def mutate(*args):
        response = original(*args)
        if fault == "revision":
            adapter.native.model_revision = "v2"
        elif fault == "model":
            adapter.native.model = object()
        elif fault == "tokenizer":
            adapter.native.tokenizer = object()
        elif fault == "config":
            adapter.native.config = None
        elif fault == "retired":
            adapter.native._retired = True
        else:
            return ModelResponse(text=response.text, model_id="wrong", model_revision="v1")
        return response

    adapter.native.generate = mutate
    with pytest.raises((ValueError, RuntimeError)):
        adapter.generate([], GenerationConfig(max_new_tokens=128))
    assert adapter.retired and not set(impl.METHODS).intersection(vars(adapter._model))
    root = adapter.output / "request_000001"
    assert not (root / "completed.json").exists()
    assert json.loads((root / "restored.json").read_text())["methods_restored"]


def test_effective_policy_fixture_matches_pinned_identity():
    from react_agent.foundation.artifacts import canonical_json
    from react_agent.foundation.normalization import text_hash

    assert text_hash(canonical_json(EFFECTIVE)) == impl.POLICY_SHA
