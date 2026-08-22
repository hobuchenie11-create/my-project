"""Письма в ресурсоснабжающие организации: шаблон должен оставаться готовым
к отправке — с прочерками под заполнение и без лишнего."""
from bot.texts import (HOUSE_ADDRESS, HOUSE_SHORT, RESIDENT_REPLY_BODY,
                       RSO_LETTER_BODY, RSO_LETTER_SUBJECT,
                       resident_reply_text, rso_letter_text)


def test_letter_has_blanks_for_what_changes():
    """Квартира, прибор, месяц и показание меняются от письма к письму."""
    assert RSO_LETTER_BODY.count("____") == 4
    assert "кв. ____" in RSO_LETTER_BODY
    assert "____" in RSO_LETTER_SUBJECT


def test_letter_names_the_house_and_the_signature():
    assert HOUSE_ADDRESS in RSO_LETTER_SUBJECT
    assert HOUSE_ADDRESS in RSO_LETTER_BODY
    # Подпись — как в объявлениях по дому, без «ул.»
    assert RSO_LETTER_BODY.rstrip().endswith(f"Председатель МКД {HOUSE_SHORT}")


def test_letter_asks_for_the_recalculation():
    """Принять показания мало — по ним ещё должны пересчитать начисление."""
    assert "перерасчёт по фактическому расходу" in RSO_LETTER_BODY


def test_letter_goes_without_a_letterhead():
    """Письмо уходит лично сотруднику абонентского отдела — шапки нет."""
    for word in ("Кому:", "От кого:", "Исх. №", "Директору"):
        assert word not in RSO_LETTER_BODY


def test_letter_reminds_about_the_photo():
    assert "фото" in RSO_LETTER_BODY.lower()
    assert "фото" in rso_letter_text().lower()


def test_bot_message_carries_subject_and_body_ready_to_copy():
    text = rso_letter_text()
    assert f"<code>{RSO_LETTER_SUBJECT}</code>" in text
    assert f"<code>{RSO_LETTER_BODY}</code>" in text


def test_resident_reply_has_blanks_for_name_and_period():
    assert RESIDENT_REPLY_BODY.count("____") == 2
    assert RESIDENT_REPLY_BODY.startswith("Здравствуйте, ____")


def test_resident_reply_says_when_to_expect_the_recalculation():
    """Житель ждёт результата в квитанции — текст обязан назвать сроки."""
    assert "после 25 числа" in RESIDENT_REPLY_BODY
    assert "в следующем" in RESIDENT_REPLY_BODY
    assert "квитанции за ____" in RESIDENT_REPLY_BODY


def test_resident_reply_promises_to_come_back():
    """Житель не должен гадать, чем всё кончилось — председатель ответит сама."""
    assert RESIDENT_REPLY_BODY.rstrip().endswith(
        "О результате сообщу дополнительно.")


def test_resident_reply_is_ready_to_copy():
    assert f"<code>{RESIDENT_REPLY_BODY}</code>" in resident_reply_text()
