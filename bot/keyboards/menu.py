"""Клавиатуры для жителей."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_SUBMIT = "🏠 Передать показания"
BTN_LAST = "📄 Мои последние показания"
BTN_HISTORY = "📊 История передач"
BTN_HELP = "ℹ️ Помощь"


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_SUBMIT)],
        [KeyboardButton(text=BTN_LAST), KeyboardButton(text=BTN_HISTORY)],
        [KeyboardButton(text=BTN_HELP)],
    ]
    if is_admin:
        from bot.keyboards.admin_menu import BTN_ADMIN
        rows.append([KeyboardButton(text=BTN_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
    )
