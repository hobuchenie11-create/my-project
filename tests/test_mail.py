"""Отправка реестра ОЭК ресурснику по электронной почте.

Письмо уходит только по кнопке председателя: отправленное ресурснику не
вернёшь, а ошибка в показаниях всплывает лишь через месяц.
"""
import asyncio
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from bot.config import config
from bot.services import mail_service


@pytest.fixture()
def mail(monkeypatch):
    """Почта «настроена» — но ничего никуда не уходит."""
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="dom@mail.ru",
                                smtp_password="секрет", smtp_from="dom@mail.ru",
                                mail_to=("oek@example.com",)))


def test_nothing_is_sent_until_the_mail_is_set_up():
    assert mail_service.is_configured() is False
    with pytest.raises(mail_service.MailNotConfigured) as exc:
        mail_service.check_configured()
    # Ошибка называет настройки, а не внутренние имена
    assert "SMTP_USER" in str(exc.value)
    assert "MAIL_TO" in str(exc.value)


def test_configured_mail_passes_the_check(mail):
    assert mail_service.is_configured() is True
    mail_service.check_configured()


def test_letter_carries_the_registry(mail, tmp_path):
    book = tmp_path / "reestr_oek_2026-09.xls"
    book.write_bytes(b"\xd0\xcf\x11\xe0")            # сигнатура .xls

    message = mail_service.build_message(
        "Реестр показаний", "Здравствуйте!", book)

    assert message["To"] == "oek@example.com"
    assert message["From"] == "dom@mail.ru"
    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "reestr_oek_2026-09.xls"
    assert attachments[0].get_content_type() == "application/vnd.ms-excel"


def test_xlsx_gets_its_own_content_type(mail, tmp_path):
    book = tmp_path / "reestr.xlsx"
    book.write_bytes(b"PK\x03\x04")

    attachment = next(mail_service.build_message("тема", "текст", book)
                      .iter_attachments())
    assert attachment.get_content_type() == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def test_several_recipients(monkeypatch, tmp_path):
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="dom@mail.ru",
                                smtp_password="секрет",
                                mail_to=("oek@example.com", "copy@example.com")))
    message = mail_service.build_message("тема", "текст")
    assert message["To"] == "oek@example.com, copy@example.com"


def test_letter_without_an_attachment_is_valid(mail):
    message = mail_service.build_message("тема", "текст")
    assert list(message.iter_attachments()) == []
    assert "текст" in message.get_content()


def test_send_logs_in_and_hands_the_letter_over(mail, monkeypatch, tmp_path):
    """Проверяем сам порядок: вход по паролю, затем отправка."""
    steps = []

    class FakeServer:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            steps.append("закрыл соединение")

        def login(self, user, password):
            steps.append(f"вход {user}")

        def send_message(self, message):
            steps.append(f"отправил «{message['Subject']}»")

    monkeypatch.setattr(mail_service.smtplib, "SMTP_SSL",
                        lambda *a, **kw: FakeServer())
    book = tmp_path / "reestr.xls"
    book.write_bytes(b"x")

    recipients = mail_service.send("Реестр", "Здравствуйте!", book)

    assert recipients == ["oek@example.com"]
    assert steps == ["вход dom@mail.ru", "отправил «Реестр»",
                     "закрыл соединение"]


def test_button_appears_only_with_configured_mail(monkeypatch):
    """Кнопка обещает то, что бот может сделать, — иначе её нет."""
    from bot.keyboards.admin_menu import oek_send_mail

    button = oek_send_mail("2026-09").inline_keyboard[0][0]
    assert button.callback_data == "oekmail:2026-09"
    assert "ОЭК" in button.text


def test_mail_password_is_not_in_the_repository():
    """Пароль живёт в .env, а .env под контроль версий не попадает."""
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore

    example = Path(".env.example").read_text(encoding="utf-8")
    assert "SMTP_PASSWORD=" in example
    assert example.count("SMTP_PASSWORD=\n") == 1, "образец должен быть пустым"


# ---------------------------------------------------------------------------
# Чужой сервер исходящей почты
# ---------------------------------------------------------------------------

def test_host_is_suggested_by_the_address():
    assert mail_service.expected_host("yavorsuk@yandex.ru") == "smtp.yandex.ru"
    assert mail_service.expected_host("dom@mail.ru") == "smtp.mail.ru"
    assert mail_service.expected_host("sovet@dom-2.ru") == ""   # незнакомый


def test_wrong_host_is_named_in_the_error(monkeypatch):
    """Логин с Яндекса на сервере Mail.ru — отказ, по которому не догадаться."""
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="yavorsuk@yandex.ru",
                                smtp_host="smtp.mail.ru"))

    hint = mail_service.login_failed_hint(Exception("535 auth failed"))

    assert "SMTP_HOST=smtp.yandex.ru" in hint
    assert "yavorsuk@yandex.ru" in hint


def test_right_host_leaves_the_password_as_the_suspect(monkeypatch):
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="yavorsuk@yandex.ru",
                                smtp_host="smtp.yandex.ru"))

    hint = mail_service.login_failed_hint(Exception("535 auth failed"))

    assert "пароль приложения" in hint
    assert "SMTP_HOST" not in hint


# ---------------------------------------------------------------------------
# Пробное письмо: проверяем почту, не беспокоя ресурсника
# ---------------------------------------------------------------------------

def test_test_letter_goes_to_our_own_address(mail, monkeypatch):
    """Проверять почту на живом реестре нельзя — ОЭК его уже не вернёт."""
    from bot.handlers import admin

    sent = {}

    def fake_send(subject, body, attachment=None, to=None):
        sent.update(subject=subject, attachment=attachment, to=to)
        return list(to)

    monkeypatch.setattr(mail_service, "send", fake_send)
    monkeypatch.setattr(admin, "config",
                        replace(config, smtp_user="dom@mail.ru",
                                mail_to=("oek_orc@omesc.ru",)))

    class Msg:
        def __init__(self):
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

    message = Msg()
    asyncio.run(admin.test_mail(message))

    assert sent["to"] == ("dom@mail.ru",)        # себе, не ресурснику
    assert sent["attachment"] is None            # реестр не прикладываем
    assert "Проверка связи" in sent["subject"]
    assert any("Спам" in text for text in message.answers)
    assert any("oek_orc@omesc.ru" in text for text in message.answers)


def test_test_letter_explains_what_is_missing(monkeypatch):
    """Почта не настроена — кнопка объясняет, а не падает молча."""
    from bot.handlers import admin

    class Msg:
        def __init__(self):
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

    message = Msg()
    asyncio.run(admin.test_mail(message))

    assert "SMTP_USER" in message.answers[0]
    assert "Настройки" in message.answers[0]


def test_hint_shows_what_was_read_without_the_password(monkeypatch):
    """Половина отказов — прилипшие пробелы, а не сам пароль."""
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="dom@yandex.ru",
                                smtp_host="smtp.yandex.ru",
                                smtp_password="abcd efgh ijkl mnop"))

    hint = mail_service.credentials_hint()

    assert "dom@yandex.ru" in hint
    assert "19 знаков" in hint
    assert "внутри есть пробел" in hint
    assert "abcd" not in hint                 # сам пароль не показываем


def test_hint_notices_quotes(monkeypatch):
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="dom@yandex.ru",
                                smtp_password='"abcdefghijklmnop"'))

    assert "есть кавычки" in mail_service.credentials_hint()


def test_clean_password_gets_no_remarks(monkeypatch):
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="dom@yandex.ru",
                                smtp_password="abcdefghijklmnop"))

    hint = mail_service.credentials_hint()

    assert "16 знаков" in hint
    # Замечаний нет: строка о прочитанном заканчивается точкой после «знаков»
    assert "16 знаков." in hint
    assert "есть пробел" not in hint and "есть кавычки" not in hint


# ---------------------------------------------------------------------------
# Вход по логину без домена: ящик на логине, адрес — алиас
# ---------------------------------------------------------------------------

class FakeServer:
    """Почтовый сервер, который пускает только по логину без домена."""

    def __init__(self, accepts: str):
        self.accepts = accepts
        self.tried: list[str] = []

    def login(self, user, password):
        self.tried.append(user)
        if user != self.accepts:
            import smtplib
            raise smtplib.SMTPAuthenticationError(535, b"Invalid user")


def test_login_falls_back_to_the_bare_login(mail, monkeypatch):
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="yavorsuk@yandex.ru",
                                smtp_password="секрет"))
    server = FakeServer(accepts="yavorsuk")

    mail_service._login(server)

    assert server.tried == ["yavorsuk@yandex.ru", "yavorsuk"]


def test_login_does_not_hide_a_real_refusal(mail, monkeypatch):
    import smtplib

    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="yavorsuk@yandex.ru",
                                smtp_password="неверный"))
    server = FakeServer(accepts="никто")

    with pytest.raises(smtplib.SMTPAuthenticationError):
        mail_service._login(server)

    assert server.tried == ["yavorsuk@yandex.ru", "yavorsuk"]


def test_login_without_at_sign_is_tried_once(mail, monkeypatch):
    import smtplib

    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="yavorsuk",
                                smtp_password="неверный"))
    server = FakeServer(accepts="никто")

    with pytest.raises(smtplib.SMTPAuthenticationError):
        mail_service._login(server)

    assert server.tried == ["yavorsuk"]


# ---------------------------------------------------------------------------
# Пояснение, дописанное в строку .env
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value, mark", [
    ("dom@yandex.ru    ← чем бот входит", "пробел"),
    ("дом@яндекс.рф", "русские буквы"),
    ("dom.yandex.ru", "не похож на адрес"),
    ("dom@@yandex.ru", "не похож на адрес"),
])
def test_annotated_address_is_named_before_sending(value, mark):
    assert mark in mail_service.address_problem(value)


def test_clean_address_passes():
    assert mail_service.address_problem("dom@yandex.ru") == ""


def test_check_points_at_the_broken_line(monkeypatch):
    """Прежде ошибка выглядела как «ascii codec can't encode character»."""
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="dom@yandex.ru ← вход",
                                smtp_password="секрет",
                                mail_to=("oek@omesc.ru",)))

    with pytest.raises(mail_service.MailNotConfigured) as exc:
        mail_service.check_configured()

    assert "SMTP_USER" in str(exc.value)
    assert "только адрес" in str(exc.value)


def test_check_points_at_a_broken_recipient(monkeypatch):
    monkeypatch.setattr(mail_service, "config",
                        replace(config, smtp_user="dom@yandex.ru",
                                smtp_password="секрет",
                                mail_to=("oek@omesc.ru", "копия себе")))

    with pytest.raises(mail_service.MailNotConfigured) as exc:
        mail_service.check_configured()

    assert "MAIL_TO" in str(exc.value)
