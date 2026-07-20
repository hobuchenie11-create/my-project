from bot.services.parser import parse_message


def test_full_message():
    text = """Кв. 12
Свет: 15230
ХВС кухня: 123,45
ХВС санузел: 89.1
ГВС кухня: 44.2
ГВС ванна: 51.0"""
    parsed = parse_message(text)
    assert parsed.apartment_number == "12"
    assert parsed.values == {
        "electricity": 15230.0,
        "cws_kitchen": 123.45,
        "cws_bathroom": 89.1,
        "hws_kitchen": 44.2,
        "hws_bathroom": 51.0,
    }
    assert not parsed.errors


def test_aliases():
    parsed = parse_message("квартира 5\nэлектроэнергия 1000\nхвс сан.узел 12")
    assert parsed.apartment_number == "5"
    assert parsed.values == {"electricity": 1000.0, "cws_bathroom": 12.0}


def test_nonresidential():
    parsed = parse_message("Нежилое помещение №1\nХВС: 500\nГВС: 300")
    assert parsed.apartment_number == "Нежилое помещение №1"
    assert parsed.values == {"cws": 500.0, "hws": 300.0}


def test_ordinary_chat_message_ignored():
    parsed = parse_message("Добрый день, соседи! Когда собрание?")
    assert parsed.is_empty


def test_no_apartment_number():
    parsed = parse_message("свет 100")
    assert parsed.apartment_number is None
    assert parsed.values == {"electricity": 100.0}
