"""Клавиатуры модуля «Задачи председателя»."""
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

BTN_TASKS = "🗂 Задачи"
BTN_MONTH_PLAN = "📅 План на месяц"
BTN_URGENT = "⏰ Текущие и просроченные"
BTN_ONE_OFF = "📌 Мои задачи"
BTN_NEW_TASK = "➕ Новая задача"
BTN_YEAR_PLAN = "📊 Годовой план (Excel)"
BTN_COUNCIL = "📤 Сводка для Совета дома"
BTN_TASKS_BACK = "⬅️ Меню председателя"


def tasks_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_URGENT), KeyboardButton(text=BTN_MONTH_PLAN)],
            [KeyboardButton(text=BTN_ONE_OFF), KeyboardButton(text=BTN_NEW_TASK)],
            [KeyboardButton(text=BTN_YEAR_PLAN)],
            [KeyboardButton(text=BTN_COUNCIL)],
            [KeyboardButton(text=BTN_TASKS_BACK)],
        ],
        resize_keyboard=True,
    )


def task_actions(task_id: int, status: str) -> InlineKeyboardMarkup:
    """Кнопки под конкретной задачей."""
    rows = []
    if status != "in_progress":
        rows.append(InlineKeyboardButton(text="▶️ В работу",
                                         callback_data=f"task:{task_id}:in_progress"))
    rows.append(InlineKeyboardButton(text="✅ Выполнено",
                                     callback_data=f"task:{task_id}:done"))
    second = [
        InlineKeyboardButton(text="⏳ Ожидает",
                             callback_data=f"task:{task_id}:waiting"),
        InlineKeyboardButton(text="🚫 Отменить",
                             callback_data=f"task:{task_id}:cancelled"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[rows, second])


def categories_keyboard(categories: dict[str, str]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"newtask:cat:{code}")]
               for code, label in categories.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
