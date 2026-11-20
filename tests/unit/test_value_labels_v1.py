"""C2 value-level labels and R-Flow v2 (synthetic values only)."""

from __future__ import annotations

from react_agent.security_v3 import value_labels_v1 as vl


def test_labels_by_value_type_not_source() -> None:
    found = vl.label_values("Ghi chú công khai: mã KX7-QWERTY-2291, đặt 45 két, ngày 2026-11-15.")
    assert vl.compact("KX7-QWERTY-2291") in found
    assert "45" not in found and "20261115" not in found  # counts and dates are not values


def test_long_numbers_and_labelled_fields() -> None:
    found = vl.label_values("Số tài khoản: 0123 456 789. Mật khẩu là hunter22. OTP: 482913")
    assert found[vl.compact("0123 456 789")] in {"long_number", "field"}
    assert found["hunter22"] == "field" and found["482913"] == "field"
    js = vl.label_values('{"user": "an", "api_key": "abcd-efgh", "count": 3}')
    assert js.get("abcdefgh") == "field" and "3" not in js


def test_plain_words_are_never_values() -> None:
    assert vl.label_values("Thông báo tới phòng nhân sự về lịch họp tuần sau.") == {}


def test_flows_catch_light_transformations_and_user_values() -> None:
    protected = {vl.compact("KX7-QWERTY-2291"): "identifier"}
    for leaked in ("KX7-QWERTY-2291", "kx7 qwerty 2291", "K.X.7.Q.W.E.R.T.Y.2.2.9.1",
                   "KX7QWERTY2291"):
        assert vl.flows(f"gửi mã {leaked} nhé", protected, "Gửi báo cáo.")
    assert not vl.flows("gửi mã KX7-QWERTY-2291", protected, "Gửi mã KX7-QWERTY-2291 cho An.")


def test_redact_replaces_surface_forms() -> None:
    value = vl.compact("KX7-QWERTY-2291")
    out = vl.redact("Mã là kx7 qwerty-2291, hết.", [value])
    assert "qwerty" not in out.casefold() and vl.REDACTION in out and out.endswith("hết.")
