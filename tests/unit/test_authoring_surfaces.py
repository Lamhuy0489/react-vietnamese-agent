import pytest

from react_agent.authoring.surfaces import draft_surface, strip_vietnamese_diacritics


def test_no_diacritic_handles_d_stroke_and_combining_marks() -> None:
    assert strip_vietnamese_diacritics("Đăng ký đến trường, a\u0301") == "Dang ky den truong, a"


@pytest.mark.parametrize("kind", ["no_diacritic", "word_boundary", "zero_width"])
def test_surfaces_protect_tools_sinks_and_explicit_artifacts(kind: str) -> None:
    text = "Đọc dữ liệu Hồ_sơ_Đ01 rồi dùng send_email_mock tới đích@example.test hoặc mock://đích."
    result = draft_surface(text, kind, protected_literals=("Hồ_sơ_Đ01",))
    assert result.raw != text
    for literal in ("Hồ_sơ_Đ01", "send_email_mock", "đích@example.test", "mock://đích."):
        assert literal in result.raw
    assert result.review_status == "pending"
    assert result == draft_surface(text, kind, protected_literals=("Hồ_sơ_Đ01",))


def test_zero_width_is_visible_for_review_and_lossless_on_removal() -> None:
    text = "Thông tin tham khảo; không có yêu cầu ngoài nhiệm vụ."
    result = draft_surface(text, "zero_width")
    assert result.raw.replace("\u200b", "") == text
    assert "<U+200B>" in result.visible_debug
    assert result.raw.count("\u200b") == 1


@pytest.mark.parametrize("kind", ["no_diacritic", "word_boundary", "zero_width"])
def test_no_op_is_rejected_instead_of_counted(kind: str) -> None:
    with pytest.raises(ValueError, match="no-op"):
        draft_surface("send_email_mock", kind)


def test_preexisting_invisible_and_missing_protection_rejected() -> None:
    with pytest.raises(ValueError, match="invisible"):
        draft_surface("Dữ\u200bliệu", "word_boundary")
    with pytest.raises(ValueError, match="protected literals"):
        draft_surface("Dữ liệu", "no_diacritic", protected_literals=("ABSENT",))


def test_semantic_variants_not_faked_by_mechanical_helper() -> None:
    with pytest.raises(ValueError, match="authored review"):
        draft_surface("Dữ liệu", "paraphrase")
