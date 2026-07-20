from bot.services.validation import check_reading, parse_value


def test_parse_value_accepts_comma_and_dot():
    assert parse_value("123,45") == 123.45
    assert parse_value("123.45") == 123.45
    assert parse_value(" 1 234 ") == 1234.0


def test_parse_value_rejects_garbage():
    assert parse_value("abc") is None
    assert parse_value("-5") is None
    assert parse_value("") is None


def test_first_reading_always_ok():
    assert check_reading("electricity", 100, None).ok


def test_reading_below_previous_rejected():
    result = check_reading("electricity", 90, 100)
    assert not result.ok
    assert "меньше предыдущего" in result.error


def test_huge_delta_warns_but_accepts():
    result = check_reading("cws_kitchen", 200, 100)
    assert result.ok
    assert result.warning


def test_normal_delta_no_warning():
    result = check_reading("cws_kitchen", 105, 100)
    assert result.ok
    assert not result.warning
