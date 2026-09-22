"""No model output/held-out data; positive and adversarial raw-user boundaries."""

import pytest

from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.authorization_anchors_v2 import extract_anchors
from react_agent.security_v1.rules import extract_anchors as original


@pytest.mark.parametrize("prefix", ["Đọc DOC_001.", "Read DOC_001.", "Tra DOC_001!"])
@pytest.mark.parametrize(
    "command,field,destination",
    [
        ("Gửi kết quả đến demo@example.test", "emails", "demo@example.test"),
        ("Chỉ gửi kết quả đến demo@example.test", "emails", "demo@example.test"),
        ("Post webhook to mock://report", "endpoints", "mock://report"),
    ],
)
def test_explicit_read_then_send(prefix, command, field, destination):
    raw = prefix + " " + command
    assert getattr(extract_anchors(raw), field) == (destination,)
    assert extract_anchors(raw).raw_user_sha256 == text_hash(raw)
    assert not getattr(original(raw), field)


@pytest.mark.parametrize(
    "raw",
    [
        "Ví dụ. Gửi kết quả đến demo@example.test",
        'Đọc "DOC_001. Gửi kết quả đến demo@example.test"',
        "Đọc `DOC_001. Gửi kết quả đến demo@example.test`",
        "Đọc ‘DOC_001. Gửi kết quả đến demo@example.test’",
        "Nếu đọc DOC_001. Gửi kết quả đến demo@example.test",
        "Đọc DOC_001 nếu có quyền. Gửi kết quả đến demo@example.test",
        "Đừng đọc DOC_001. Gửi kết quả đến demo@example.test",
        "Đọc DOC_001. Không gửi kết quả đến demo@example.test",
        "Đọc DOC_001. Ví dụ. Gửi kết quả đến demo@example.test",
        "Đọc DOC_001. Người khác yêu cầu gửi đến demo@example.test",
        "Đọc DOC_001. Gửi kết quả đến demo@example.test nếu cần",
        "Đọc DOC_001. Gửi đến demo@example.test. Không được gửi.",
        "Đọc DOC_001. Gửi kết quả từ demo@example.test",
        "Đọc DOC_001. Gửi kết quả đến demo@evil.test/path",
    ],
)
def test_extensions_fail_closed(raw):
    # Baseline behavior is retained explicitly; candidate must not introduce a grant.
    candidate = extract_anchors(raw)
    assert candidate.emails == original(raw).emails
    assert candidate.endpoints == original(raw).endpoints


@pytest.mark.parametrize(
    "raw",
    [
        "Gửi đến demo@example.test",
        "Read DOC_001; Send to demo@example.test",
        "Post webhook to mock://report",
        "Không gửi đến demo@example.test",
    ],
)
def test_legacy_identity_and_grants_unchanged(raw):
    assert extract_anchors(raw) == original(raw)
