"""Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)."""
from bot.services.parser import parse_message


def test_template_1_2_rooms():
    parsed = parse_message("Кв. 12\nЭл.эн - 234\nхвс - 5\nгвс - 101")
    assert parsed.apartment_number == "12"
    assert parsed.values == {"electricity": 234.0, "cws": 5.0, "hws": 101.0}


def test_template_3_rooms():
    text = ("кв 69\nэлектроэнергия – 22028\nхвс (кухня) – 466\n"
            "хвс (сан.узел) - 984\nгвс (кухня) – 167\nгвс (ванна) - 265\n"
            "гвс (итого) - 432")
    parsed = parse_message(text)
    assert parsed.apartment_number == "69"
    assert parsed.values == {
        "electricity": 22028.0, "cws_kitchen": 466.0, "cws_bathroom": 984.0,
        "hws_kitchen": 167.0, "hws_bathroom": 265.0, "hws_total": 432.0,
    }


def test_short_abbreviations_hv_gv_sv():
    parsed = parse_message("Кв 58\nХв 1048\nГВ 490\nСв 20820")
    assert parsed.apartment_number == "58"
    assert parsed.values == {"cws": 1048.0, "hws": 490.0, "electricity": 20820.0}


def test_su_bathroom():
    parsed = parse_message("Кв. 22\nЭл. энерг. 15305\nХВС с/у 265\nГВС с/у 307")
    assert parsed.values == {
        "electricity": 15305.0, "cws_bathroom": 265.0, "hws_bathroom": 307.0,
    }


def test_gas_ignored_and_room_temperature_words():
    text = ("Кв 21\nЭлектроэнергия : 31378\nГаз: 276\nКухня гор: 10\n"
            "Кухня хол: 16\nВанна гор: 18\nВанна хол: 33")
    parsed = parse_message(text)
    assert parsed.values == {
        "electricity": 31378.0, "hws_kitchen": 10.0, "cws_kitchen": 16.0,
        "hws_bathroom": 18.0, "cws_bathroom": 33.0,
    }
    assert parsed.ignored  # газ распознан, но не учитывается


def test_tual_and_sum():
    text = ("Кв 32\nХв кухня 11\nХв туал 47\nГв кухня 7\nГв ванна 48\n"
            "Сумма гв 55\nЭл Эн 29991")
    parsed = parse_message(text)
    assert parsed.values == {
        "cws_kitchen": 11.0, "cws_bathroom": 47.0, "hws_kitchen": 7.0,
        "hws_bathroom": 48.0, "hws_total": 55.0, "electricity": 29991.0,
    }


def test_leading_zeros():
    text = ("Кв 24\nЭ/энер - 32992\nХвс кухня - 6\nХвс с/уз - 140\n"
            "Гвс кухня - 0000076\nГвс ванна - 57\nСумма гвс - 57")
    parsed = parse_message(text)
    assert parsed.values["hws_kitchen"] == 76.0
    assert parsed.values["cws_bathroom"] == 140.0
    assert parsed.values["hws_total"] == 57.0


def test_comma_separators_and_carry_context():
    # Разделитель — запятая; тип воды переносится из предыдущих строк
    text = ("Кв, 29\nЭдектро, 12178\nХв,кух,36\nСан,уз,228\n"
            "Гв,кух,114\nВанная,178\nСумма,гв,292")
    parsed = parse_message(text)
    assert parsed.apartment_number == "29"
    assert parsed.values == {
        "electricity": 12178.0, "cws_kitchen": 36.0, "cws_bathroom": 228.0,
        "hws_kitchen": 114.0, "hws_bathroom": 178.0, "hws_total": 292.0,
    }


def test_spaced_dots_gv_hv():
    parsed = parse_message("Кв. 71\nГ. В. 441\nХ. В. 434\nЭл. энергия 34287")
    assert parsed.values == {"hws": 441.0, "cws": 434.0, "electricity": 34287.0}


def test_dotted_abbrev_full():
    text = ("Кв. 60\nЭл. Эн. 2784\nХол. Кух. - 271\nСан. Уз.хол. -50\n"
            "Кух. Гор. -302\nВан. Гор. -511\nГвс. - 813")
    parsed = parse_message(text)
    assert parsed.values["electricity"] == 2784.0
    assert parsed.values["cws_kitchen"] == 271.0
    assert parsed.values["cws_bathroom"] == 50.0
    assert parsed.values["hws_kitchen"] == 302.0
    assert parsed.values["hws_bathroom"] == 511.0
    assert parsed.values["hws"] == 813.0  # «Гвс» без локации = итог по ГВС


def test_ordinary_chat_message_ignored():
    parsed = parse_message("Добрый день, соседи! Когда собрание?")
    assert parsed.is_empty
    assert parsed.apartment_number is None


def test_nonresidential():
    parsed = parse_message("Нежилое помещение №1\nХВС: 500\nГВС: 300")
    assert parsed.apartment_number == "Нежилое помещение №1"
    assert parsed.values == {"cws": 500.0, "hws": 300.0}
