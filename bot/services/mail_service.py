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

    for name, value in (("SMTP_USER", config.smtp_user),
                        ("SMTP_FROM", config.smtp_from)):
        problem = address_problem(value)
        if problem:
            raise MailNotConfigured(
                f"Строка {name} в .env записана неверно: «{value}» — "
                f"{problem}.\n\nВ строке должен быть только адрес, без "
                "пояснений, стрелок и кавычек: "
                f"<code>{name}=имя@yandex.ru</code>")
    for address in config.mail_to:
        problem = address_problem(address)
        if problem:
            raise MailNotConfigured(
                f"Адрес получателя в MAIL_TO записан неверно: «{address}» — "
                f"{problem}.\n\nАдреса перечисляются через запятую, без "
                "пробелов и пояснений.")


def address_problem(address: str) -> str:
    """Почему этот адрес не адрес. Пусто — всё в порядке.

    Пояснение, дописанное в строку .env («почта ← отсюда шлём»), попадает
    в адрес целиком, и почтовая библиотека падает с «ascii codec can't
    encode character» — по такой ошибке причину не найти.
    """
    if not address:
        return ""
    if " " in address.strip():
        return "в нём есть пробел — похоже, рядом осталось пояснение"
    if not address.isascii():
        return "в нём есть русские буквы или стрелка"
    if address.count("@") != 1 or address.startswith("@") or address.endswith("@"):
        return "он не похож на адрес почты"
    return ""


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
    return ("Почта не приняла логин и пароль. Нужен «пароль приложения» из "
            "настроек почты, а не пароль, которым вы входите в ящик.\n\n"
            f"{credentials_hint()}\n\n"
            f"Ответ сервера: {exc}")


def credentials_hint() -> str:
    """Что бот прочитал из .env — без самого пароля.

    Половина отказов — не в самом пароле, а в том, как он попал в файл:
    прилипли пробелы при копировании, остались кавычки, адрес с опечаткой.
    Увидеть это можно только по тому, что прочитал бот, а показывать пароль
    в переписке нельзя — поэтому показываем длину и форму.
    """
    password = config.smtp_password
    quirks = []
    if password != password.strip():
        quirks.append("по краям есть пробелы")
    if " " in password.strip():
        quirks.append("внутри есть пробел")
    if password[:1] in "\"'" or password[-1:] in "\"'":
        quirks.append("есть кавычки")
    note = f" — {', '.join(quirks)}" if quirks else ""
    return (f"Бот прочитал из .env: логин <code>{config.smtp_user}</code>, "
            f"пароль из {len(password)} знаков{note}.\n"
            "У Яндекса пароль приложения — 16 букв без пробелов.")


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


def _login(server) -> None:
    """Вход на почтовый сервер. При отказе пробует логин без домена.

    У Яндекса ящик часто заведён на один логин, а адрес для переписки —
    алиас. Сервер тогда отвечает «Invalid user or password» на полный
    адрес, но пускает по самому логину. Разница незаметна, а выглядит как
    неверный пароль — и человек в третий раз создаёт новый.
    """
    try:
        server.login(config.smtp_user, config.smtp_password)
        return
    except smtplib.SMTPAuthenticationError:
        local = config.smtp_user.partition("@")[0]
        if not local or local == config.smtp_user:
            raise

    server.login(local, config.smtp_password)
    logger.warning(
        "Почта приняла вход по логину «%s» без домена. Впишите его в "
        "SMTP_USER — иначе бот каждый раз пробует дважды.", local)


def _send_message(server, message) -> None:
    """Отправка письма. Если сервер не принял отправителя — шлём от логина.

    Яндекс разрешает отправлять только с адресов своего аккаунта и отвечает
    «Sender address rejected: not owned by authorized user». Это не повод
    терять реестр: письмо то же, меняется только подпись отправителя, —
    и в журнале видно, какую строку .env поправить.
    """
    try:
        server.send_message(message)
        return
    except smtplib.SMTPSenderRefused as exc:
        sender = message["From"]
        if not config.smtp_user or sender == config.smtp_user:
            raise MailNotConfigured(sender_rejected_hint(sender, exc)) from exc

    del message["From"]
    message["From"] = config.smtp_user
    server.send_message(message)
    logger.warning(
        "Почта не приняла отправителя «%s» — письмо ушло от «%s». "
        "Впишите этот адрес в SMTP_FROM (или очистите строку).",
        config.smtp_from, config.smtp_user)


def sender_rejected_hint(sender: str, exc: Exception) -> str:
    return (f"Почта не разрешает отправлять с адреса {sender}: он не "
            f"принадлежит аккаунту {config.smtp_user}.\n\n"
            "В .env в строке SMTP_FROM должен стоять тот же адрес, что и в "
            "SMTP_USER, либо строку SMTP_FROM можно оставить пустой — тогда "
            "бот подставит адрес входа сам.\n\n"
            f"Ответ сервера: {exc}")


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
            _login(server)
        except smtplib.SMTPAuthenticationError as exc:
            raise MailNotConfigured(login_failed_hint(exc)) from exc
        _send_message(server, message)

    recipients = list(to or config.mail_to)
    logger.info("Письмо «%s» отправлено: %s", subject, ", ".join(recipients))
    return recipients
