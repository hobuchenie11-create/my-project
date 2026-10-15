"""Отправка файла по электронной почте — реестр ОЭК ресурснику.

Письмо уходит только по кнопке председателя, и это не перестраховка:
отправленное ресурснику письмо не вернёшь, а ошибка в показаниях всплывает
лишь через месяц, когда расход окажется отрицательным. Поэтому бот готовит
файл, показывает его в Telegram и ждёт подтверждения.

Пароль от почты живёт в .env рядом с токеном бота и в переписку не
попадает. Почтовые сервисы для SMTP требуют отдельный пароль приложения
(у Mail.ru — «пароль для внешних приложений»): обычный пароль от аккаунта
они не примут.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from bot.config import config

logger = logging.getLogger(__name__)

# .xls и .xlsx — как их отдавать почтовому серверу
MIME_TYPES = {
    ".xls": ("application", "vnd.ms-excel"),
    ".xlsx": ("application",
              "vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
}
DEFAULT_MIME = ("application", "octet-stream")

TIMEOUT_SECONDS = 60


class MailNotConfigured(Exception):
    """Почта не настроена — в .env нет логина, пароля или адреса получателя."""


def is_configured() -> bool:
    return bool(config.smtp_user and config.smtp_password and config.mail_to)


def check_configured() -> None:
    """Объясняет, чего не хватает, — на языке настроек в .env."""
    missing = [name for name, value in (
        ("SMTP_USER", config.smtp_user),
        ("SMTP_PASSWORD", config.smtp_password),
        ("MAIL_TO", config.mail_to),
    ) if not value]
    if missing:
        raise MailNotConfigured(
            "Почта не настроена: в файле .env не заполнено — "
            + ", ".join(missing))


# Какому адресу какой сервер исходящей почты полагается
SMTP_HOSTS = {
    ("yandex.ru", "ya.ru", "yandex.com"): "smtp.yandex.ru",
    ("mail.ru", "bk.ru", "inbox.ru", "list.ru", "internet.ru"): "smtp.mail.ru",
    ("gmail.com",): "smtp.gmail.com",
}


def expected_host(address: str) -> str:
    """Какой SMTP_HOST полагается этому адресу. Пусто — адрес незнакомый."""
    domain = address.rpartition("@")[2].strip().lower()
    for domains, host in SMTP_HOSTS.items():
        if domain in domains:
            return host
    return ""


def login_failed_hint(exc: Exception) -> str:
    """Почему почта не пустила. Самое частое — чужой сервер или не тот пароль.

    Отказ в аутентификации выглядит одинаково и когда пароль неверный, и
    когда логин с Яндекса стучится на сервер Mail.ru. Второе чинится одной
    строкой в .env, но догадаться об этом по ответу сервера невозможно.
    """
    proper = expected_host(config.smtp_user)
    if proper and proper != config.smtp_host:
        return (f"Почта не приняла вход: адрес {config.smtp_user} — "
                f"а сервер в .env указан {config.smtp_host}. "
                f"Впишите SMTP_HOST={proper} и перезапустите бота.")
    return ("Почта не приняла логин и пароль. Проверьте в .env SMTP_USER и "
            "SMTP_PASSWORD: нужен «пароль приложения» из настроек почты, "
            "а не пароль, которым вы входите в ящик.\n\n"
            f"Ответ сервера: {exc}")


def build_message(subject: str, body: str, attachment: Path | None = None,
                  to: tuple[str, ...] | None = None) -> EmailMessage:
    """Собирает письмо. Отдельно от отправки — чтобы проверять в тестах."""
    message = EmailMessage()
    message["From"] = config.smtp_from or config.smtp_user
    message["To"] = ", ".join(to or config.mail_to)
    message["Subject"] = subject
    message.set_content(body)

    if attachment is not None:
        path = Path(attachment)
        maintype, subtype = MIME_TYPES.get(path.suffix.lower(), DEFAULT_MIME)
        message.add_attachment(path.read_bytes(), maintype=maintype,
                               subtype=subtype, filename=path.name)
    return message


def send(subject: str, body: str, attachment: Path | None = None,
         to: tuple[str, ...] | None = None) -> list[str]:
    """Отправляет письмо и возвращает адреса получателей.

    Работает синхронно: вызывать из бота через asyncio.to_thread, иначе
    на время отправки замрёт вся переписка.
    """
    check_configured()
    message = build_message(subject, body, attachment, to)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port,
                          context=context, timeout=TIMEOUT_SECONDS) as server:
        try:
            server.login(config.smtp_user, config.smtp_password)
        except smtplib.SMTPAuthenticationError as exc:
            raise MailNotConfigured(login_failed_hint(exc)) from exc
        server.send_message(message)

    recipients = list(to or config.mail_to)
    logger.info("Письмо «%s» отправлено: %s", subject, ", ".join(recipients))
    return recipients
