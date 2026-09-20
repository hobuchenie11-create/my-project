"""Клавиатуры раздела «Памятки»."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import FAQ_CATEGORIES


def faq_categories(categories: list[str]) -> InlineKeyboardMarkup:
    """Разделы, в которых есть памятки, — по одному в строке."""
    buttons = [[InlineKeyboardButton(
        text=FAQ_CATEGORIES.get(code, code), callback_data=f"faq:cat:{code}")]
        for code in categories]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def faq_memos(memos, back: bool = False) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=memo.title,
                                     callback_data=f"faq:memo:{memo.code}")]
               for memo in memos]
    if back:
        buttons.append([InlineKeyboardButton(text="⬅️ Разделы",
                                             callback_data="faq:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Сценарии, которые памятка может предложить начать. Ключ — поле `action`
# в заголовке файла памятки, значение — подпись кнопки под ней.
MEMO_ACTIONS = {
    "newcomer": "🔑 Оформиться — задать 4 вопроса",
}


def memo_action(action: str) -> InlineKeyboardMarkup | None:
    """Кнопка под памяткой: памятка объясняет, кнопка сразу начинает дело."""
    label = MEMO_ACTIONS.get(action)
    if not label:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=label, callback_data=f"start:{action}")]])
