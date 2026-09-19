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
