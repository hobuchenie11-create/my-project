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
