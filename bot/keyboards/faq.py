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
    "newcomer": "🔑 Оформиться — задать 3 вопроса",
    "gatephone": "📱 Оставить заявку на смену номера",
}


def memo_action(action: str) -> InlineKeyboardMarkup | None:
    """Кнопка под памяткой: памятка объясняет, кнопка сразу начинает дело."""
    label = MEMO_ACTIONS.get(action)
    if not label:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=label, callback_data=f"start:{action}")]])


BTN_SAVE_POSTER = "💾 Сохранить плакат файлом"


def memo_buttons(memo,
                 with_action: bool = True) -> InlineKeyboardMarkup | None:
    """Кнопки под памяткой: начать сценарий и сохранить плакат себе.

    Картинкой Телеграм присылает сжатую копию — мелкий шрифт на плакате в
    ней плывёт. Поэтому под памяткой с плакатом всегда есть кнопка «файлом»:
    её житель сохраняет в телефон и читает потом, даже без интернета.

    Кнопка плаката остаётся и внутри чужого сценария (`with_action=False`):
    файл приходит отдельным сообщением и разговор не прерывает, в отличие
    от кнопки, которая увела бы жителя в начало другого разговора.
    """
    rows = []
    label = MEMO_ACTIONS.get(memo.action) if with_action else None
    if label:
        rows.append([InlineKeyboardButton(
            text=label, callback_data=f"start:{memo.action}")])
    if memo.image_path is not None:
        rows.append([InlineKeyboardButton(
            text=BTN_SAVE_POSTER, callback_data=f"faq:poster:{memo.code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
