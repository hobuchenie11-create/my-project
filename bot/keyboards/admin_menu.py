"""Клавиатура администратора (председателя)."""
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from bot.keyboards.tasks import BTN_TASKS

BTN_ADMIN = "🛠 Меню председателя"
BTN_REGISTRY = "📋 Реестр квартир"
BTN_STATEMENT = "📄 Ведомость передачи"
BTN_OEK = "📨 Реестр ОЭК"
BTN_OEK_TEMPLATE = "📥 Шаблон ОЭК"
BTN_WORKBOOK = "📗 Книга Excel"
BTN_STATS = "📈 Статистика"
BTN_DEBTORS = "🔴 Должники"
BTN_DEBTORS_DOC = "📕 Ведомость непередавших"
BTN_REMIND = "🔔 Напомнить должникам"
BTN_INVITE = "📣 Памятка жителям"
BTN_CHAT_REMINDER = "🔔 Напоминание в чат"
BTN_TEMPLATES = "📋 Шаблоны в чат"
BTN_SPECIAL = "🏢 Нежилые и ОДПУ"
BTN_METERS = "🔧 Счётчики квартиры"
BTN_CORRECTION = "✏️ Исправить показание"
BTN_BLANKS = "🖨 Бланки для печати"
BTN_RSO_LETTER = "✉️ Письмо в Росводоканал"
BTN_RESIDENT_REPLY = "💬 Ответ жителю"
BTN_FAQ_GAPS = "❓ Вопросы без ответа"
BTN_USERS = "👥 Пользователи"
BTN_SETTINGS = "⚙ Настройки"
BTN_BACKUP = "💾 Резервная копия"
BTN_BACK = "⬅️ Главное меню"


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TASKS)],
            [KeyboardButton(text=BTN_REGISTRY), KeyboardButton(text=BTN_SPECIAL)],
            [KeyboardButton(text=BTN_METERS)],
            [KeyboardButton(text=BTN_STATEMENT),
             KeyboardButton(text=BTN_CORRECTION)],
            [KeyboardButton(text=BTN_OEK), KeyboardButton(text=BTN_OEK_TEMPLATE)],
            [KeyboardButton(text=BTN_WORKBOOK), KeyboardButton(text=BTN_STATS)],
            [KeyboardButton(text=BTN_BLANKS)],
            [KeyboardButton(text=BTN_RSO_LETTER),
             KeyboardButton(text=BTN_RESIDENT_REPLY)],
            [KeyboardButton(text=BTN_DEBTORS), KeyboardButton(text=BTN_DEBTORS_DOC)],
            [KeyboardButton(text=BTN_REMIND), KeyboardButton(text=BTN_INVITE)],
            [KeyboardButton(text=BTN_CHAT_REMINDER),
             KeyboardButton(text=BTN_TEMPLATES)],
            [KeyboardButton(text=BTN_FAQ_GAPS)],
            [KeyboardButton(text=BTN_USERS), KeyboardButton(text=BTN_SETTINGS)],
            [KeyboardButton(text=BTN_BACKUP)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def apartment_layouts(apartment_id: int) -> InlineKeyboardMarkup:
    """Сколько счётчиков воды в квартире — выбор для правки реестра.

    В доме всего два набора: два счётчика воды на квартиру или четыре —
    в трёхкомнатных, где кухня и санузел разведены. Смешанные варианты
    из списка убраны, чтобы не путать.
    """
    labels = {
        "1-1": "2 счётчика воды · ХВС и ГВС",
        "2-2": "4 счётчика воды · кухня и санузел",
    }
    rows = [[InlineKeyboardButton(text=text,
                                  callback_data=f"layout:{apartment_id}:{key}")]
            for key, text in labels.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)
