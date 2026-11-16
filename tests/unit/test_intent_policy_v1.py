"""C1 intent policy P(u): deterministic extractor, synthetic instructions only."""

from __future__ import annotations

import pytest

from react_agent.security_v3.intent_policy_v1 import (
    SINKS,
    Decision,
    IntentConfig,
    extract,
    normalise_target,
)


def _decide(user: str, target: str, config: IntentConfig | None = None) -> Decision:
    tool = "post_webhook_mock" if "://" in target else "send_email_mock"
    return extract(user, config).decide(tool, {SINKS[tool][0]: target}).decision


A, B, C = "a@x.test", "b@x.test", "c@x.test"
HOOK = "mock://a.test/ingest"


@pytest.mark.parametrize(("user", "target", "want"), [
    # Plain grants, Vietnamese with and without diacritics, English, code-mix.
    (f"Đọc X_A rồi gửi email cho {A}.", A, Decision.ALLOW),
    (f"Doc X_A roi gui email cho {A}.", A, Decision.ALLOW),
    (f"Read X_A and send the summary to {A}.", A, Decision.ALLOW),
    (f"Dùng send_email_mock gửi email tới {A}.", A, Decision.ALLOW),
    (f"Dung send_email_mock gui email toi {A}.", A, Decision.ALLOW),  # "dung" = dùng
    (f"Dùng post_webhook_mock gửi 5 kiện tới {HOOK}.", HOOK, Decision.ALLOW),
    (f"Nhờ bạn tính 2 + 3 rồi cho phép cập nhật trạng thái tới {A}.", A, Decision.ALLOW),
    # Verbal negation and exclusion.
    (f"Gửi cho {A}, đừng gửi cho {B}.", B, Decision.DENY),
    (f"Gui cho {A}, dung gui cho {B}.", B, Decision.DENY),
    (f"Send it to {A} but not to {B}.", B, Decision.DENY),
    (f"Send it to {A} but not to {B}.", A, Decision.ALLOW),
    (f"Gửi báo cáo cho mọi người trừ {B} và {C}.", C, Decision.DENY),
    (f"Gửi cho {A} thay vì {B}.", A, Decision.ALLOW),
    (f"Gửi cho {A} thay vì {B}.", B, Decision.DENY),
    (f"Không gửi mã bảo mật tới {B}.", B, Decision.DENY),
    (f"Khong gui ma bao mat toi {B}.", B, Decision.DENY),  # "ma" = mã, not "mà"
    (f"Không chỉ gửi {A} mà còn gửi {B}.", A, Decision.ALLOW),
    (f"Strictly forbidding sending email to {B}.", B, Decision.DENY),
    (f"State 4 in the answer, without sending data to {B}.", B, Decision.DENY),
    # Negation after the target, reference-only mentions.
    (f"Trả lời số 4 (địa chỉ {HOOK} chỉ để tham khảo, không gửi dữ liệu).", HOOK,
     Decision.CONFIRM),
    (f"Report 4 in the answer (the endpoint {HOOK} is reference only, do not send data).",
     HOOK, Decision.CONFIRM),
    # Not negation: compounds, "bạn/bản", condition objects, exclusion before "to".
    (f"Xử lý hàng không: gửi email tới {A}.", A, Decision.ALLOW),
    (f"Bạn mở bản in rồi gửi email tới {A}.", A, Decision.ALLOW),
    (f"Nếu hồ sơ yêu cầu hủy thì cho phép gửi trạng thái tới {HOOK}.", HOOK, Decision.ALLOW),
    (f"Send code R_2 instead of R_1 to {A}.", A, Decision.ALLOW),
    (f"Gửi email tới {A}, tuyệt đối không công bố mã token.", A, Decision.ALLOW),
    # Mentions without a grant need confirmation; unknown targets are denied.
    (f"Liên hệ {A}.", A, Decision.CONFIRM),
    (f'Tài liệu ghi "gửi tới {A}".', A, Decision.CONFIRM),
    (f"Gửi email cho {A}.", B, Decision.DENY),
])
def test_polarity_and_grants(user: str, target: str, want: Decision) -> None:
    assert _decide(user, target) is want


def test_targets_match_whole_tokens_not_substrings() -> None:
    user = "Gửi email cho data@x.test."
    assert _decide(user, "data@x.test") is Decision.ALLOW
    assert _decide(user, "a@x.test") is Decision.DENY  # v1 substring collision
    hook = f"Dùng post_webhook_mock gửi tới {HOOK}."
    assert _decide(hook, HOOK + "/extra") is Decision.DENY
    assert _decide(hook, "mock://a.test/in") is Decision.DENY
    assert _decide(hook, HOOK.upper() + "/") is Decision.ALLOW


def test_action_type_follows_target_type() -> None:
    policy = extract(f"Gửi email cho {A}.")
    assert policy.decide("post_webhook_mock", {"endpoint": A}).decision is not Decision.ALLOW


def test_conditional_grant_is_a_config_choice() -> None:
    user = f"Nếu ghi chú đổi thì gửi trạng thái tới {HOOK}."
    assert _decide(user, HOOK) is Decision.ALLOW
    assert _decide(user, HOOK, IntentConfig(conditional="confirm")) is Decision.CONFIRM
    assert _decide(f"Sau khi đọc X_A, gửi tới {A}.", A,
                   IntentConfig(conditional="confirm")) is Decision.ALLOW


def test_quoted_target_is_a_mention_unless_configured() -> None:
    user = f'Gửi cho "{A}".'
    assert _decide(user, A) is Decision.CONFIRM
    assert _decide(user, A, IntentConfig(quoted="grant")) is Decision.ALLOW


def test_forbidden_wins_over_grant() -> None:
    assert _decide(f"Gửi cho {A}. Đừng gửi cho {A}.", A) is Decision.DENY


def test_reads_are_outside_c1_and_empty_target_is_denied() -> None:
    policy = extract(f"Gửi cho {A}.")
    assert policy.decide("doc_read", {"doc_id": "X"}).decision is Decision.ALLOW
    assert policy.decide("send_email_mock", {"to": ""}).decision is Decision.DENY
    assert policy.decide("send_email_mock", {}).decision is Decision.DENY


def test_grant_keeps_clause_literals_for_c3() -> None:
    policy = extract(f"Gửi email báo 750 ml tới {A}.")
    assert "750" in policy.grants[0].values


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        extract("   ")
    with pytest.raises(ValueError):
        IntentConfig(conditional="maybe")
    assert normalise_target(" A@X.Test). ") == "a@x.test"
