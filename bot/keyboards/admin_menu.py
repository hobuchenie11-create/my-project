"""Клавиатура администратора (председателя)."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_ADMIN = "🛠 Меню председателя"
BTN_REGISTRY = "📋 Реестр квартир"
BTN_STATEMENT = "📄 Ведомость передачи"
BTN_STATS = "📈 Статистика"
BTN_DEBTORS = "🔴 Должники"
BTN_REMIND = "🔔 Напомнить должникам"
BTN_USERS = "👥 Пользователи"
BTN_SETTINGS = "⚙ Настройки"
BTN_BACKUP = "💾 Резервная копия"
BTN_BACK = "⬅️ Главное меню"


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_REGISTRY), KeyboardButton(text=BTN_STATEMENT)],
            [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_DEBTORS)],
            [KeyboardButton(text=BTN_REMIND), KeyboardButton(text=BTN_USERS)],
            [KeyboardButton(text=BTN_SETTINGS), KeyboardButton(text=BTN_BACKUP)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )
