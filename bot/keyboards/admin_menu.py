"""Клавиатура администратора (председателя)."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.keyboards.tasks import BTN_TASKS

BTN_ADMIN = "🛠 Меню председателя"
BTN_REGISTRY = "📋 Реестр квартир"
BTN_STATEMENT = "📄 Ведомость передачи"
BTN_WORKBOOK = "📗 Книга Excel"
BTN_STATS = "📈 Статистика"
BTN_DEBTORS = "🔴 Должники"
BTN_DEBTORS_DOC = "📕 Ведомость непередавших"
BTN_REMIND = "🔔 Напомнить должникам"
BTN_INVITE = "📣 Памятка жителям"
BTN_CHAT_REMINDER = "🔔 Напоминание в чат"
BTN_TEMPLATES = "📋 Шаблоны в чат"
BTN_USERS = "👥 Пользователи"
BTN_SETTINGS = "⚙ Настройки"
BTN_BACKUP = "💾 Резервная копия"
BTN_BACK = "⬅️ Главное меню"


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TASKS)],
            [KeyboardButton(text=BTN_REGISTRY), KeyboardButton(text=BTN_STATEMENT)],
            [KeyboardButton(text=BTN_WORKBOOK), KeyboardButton(text=BTN_STATS)],
            [KeyboardButton(text=BTN_DEBTORS), KeyboardButton(text=BTN_DEBTORS_DOC)],
            [KeyboardButton(text=BTN_REMIND), KeyboardButton(text=BTN_INVITE)],
            [KeyboardButton(text=BTN_CHAT_REMINDER),
             KeyboardButton(text=BTN_TEMPLATES)],
            [KeyboardButton(text=BTN_USERS), KeyboardButton(text=BTN_SETTINGS)],
            [KeyboardButton(text=BTN_BACKUP)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )
