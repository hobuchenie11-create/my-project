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


def test_everything_in_one_line_with_commas():
    """Реальное сообщение жителя: всё в строку, подписи со слешем."""
    parsed = parse_message("кв38,Х/В30,Г/В 42,Эл/э 15873")
    assert parsed.apartment_number == "38"
    assert parsed.values == {"cws": 30.0, "hws": 42.0, "electricity": 15873.0}


def test_apartment_number_without_space():
    """«кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются."""
    for text, number in (("кв38", "38"), ("Кв.7", "7"), ("квартира140", "140"),
                         ("кв 38", "38"), ("кв№38", "38")):
        assert parse_message(f"{text} хвс 10").apartment_number == number


def test_comma_inside_a_number_is_not_a_separator():
    """Запятая между цифрами — дробная часть, а не разделитель приборов."""
    parsed = parse_message("кв 5, хвс 56,78, гвс 12,5")
    assert parsed.values == {"cws": 56.78, "hws": 12.5}


def test_one_line_with_kitchen_and_bathroom():
    parsed = parse_message("Кв 53, хвс кух 36, хвс с/у 228, "
                           "гвс кух 114, гвс ванна 178")
    assert parsed.apartment_number == "53"
    assert parsed.values == {"cws_kitchen": 36.0, "cws_bathroom": 228.0,
                             "hws_kitchen": 114.0, "hws_bathroom": 178.0}


def test_semicolon_separator():
    parsed = parse_message("кв 12; х/в 30; г/в 42; эл/э 15873")
    assert parsed.values == {"cws": 30.0, "hws": 42.0, "electricity": 15873.0}


def test_repeated_separators_before_the_number():
    """«Кв,, 29» — жители ставят по две запятые, скобки, тире."""
    for text, number in (("Кв,, 29", "29"), ("Кв,,, 7", "7"), ("Кв - 12", "12"),
                         ("Кв: 5", "5"), ("кв (33)", "33"), ("Кв.. 41", "41")):
        assert parse_message(f"{text}\nХвс 30").apartment_number == number


def test_real_message_with_doubled_commas():
    """Сообщение жителя целиком: двойные запятые в каждой строке."""
    parsed = parse_message("Кв,, 29\nЭлектро 12254\nХв,кух,36\nСан,уз,,229\n"
                           "Гв,кух,,114\nГв, ванная, 179\nСум,,гв,,293")
    assert parsed.apartment_number == "29"
    assert parsed.values == {
        "electricity": 12254.0, "cws_kitchen": 36.0, "cws_bathroom": 229.0,
        "hws_kitchen": 114.0, "hws_bathroom": 179.0, "hws_total": 293.0,
    }


def test_unreadable_apartment_is_flagged():
    """Квартиру назвали, но номер не читается — это не «номер не указан»."""
    unreadable = parse_message("Кв.\nХвс 30")
    assert unreadable.apartment_number is None
    assert unreadable.apartment_unreadable is True

    # Номера нет вовсе — квартиру можно взять из регистрации отправителя
    no_mention = parse_message("Хвс 30\nГвс 42")
    assert no_mention.mentions_apartment is False
    assert no_mention.apartment_unreadable is False
