"""Клавиатуры модуля «Задачи председателя»."""
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

BTN_TASKS = "🗂 Задачи"
BTN_MONTH_PLAN = "📅 План на месяц"
BTN_URGENT = "⏰ Текущие и просроченные"
BTN_ONE_OFF = "📌 Мои задачи"
BTN_NEW_TASK = "➕ Новая задача"
BTN_VERIFICATION = "🔧 Поверка приборов"
BTN_YEAR_PLAN = "📊 Годовой план (Excel)"
BTN_IMPORT_PLAN = "📥 Загрузить правки"
BTN_COUNCIL = "📤 Сводка для Совета дома"
BTN_TASKS_BACK = "⬅️ Меню председателя"


def tasks_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_URGENT), KeyboardButton(text=BTN_MONTH_PLAN)],
            [KeyboardButton(text=BTN_ONE_OFF), KeyboardButton(text=BTN_NEW_TASK)],
            [KeyboardButton(text=BTN_VERIFICATION)],
            [KeyboardButton(text=BTN_YEAR_PLAN), KeyboardButton(text=BTN_IMPORT_PLAN)],
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


def council_selection(rows, selected: set[int]) -> InlineKeyboardMarkup:
    """Список задач с отметками: что именно уйдёт Совету дома."""
    buttons = []
    for row in rows:
        mark = "☑️" if row["id"] in selected else "⬜️"
        title = row["title"]
        if len(title) > 45:
            title = title[:44].rstrip() + "…"
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {title}", callback_data=f"council:toggle:{row['id']}")])

    buttons.append([
        InlineKeyboardButton(text="Выбрать все", callback_data="council:all"),
        InlineKeyboardButton(text="Снять все", callback_data="council:none"),
    ])
    buttons.append([InlineKeyboardButton(
        text=f"👁 Показать сводку ({len(selected)})",
        callback_data="council:preview")])
    buttons.append([InlineKeyboardButton(text="🚫 Отмена",
                                         callback_data="council:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def council_confirm() -> InlineKeyboardMarkup:
    """Согласование: отправлять ли эту сводку Совету дома."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Отправить Совету",
                              callback_data="council:send")],
        [InlineKeyboardButton(text="✏️ Изменить выбор",
                              callback_data="council:back")],
        [InlineKeyboardButton(text="🚫 Отмена", callback_data="council:cancel")],
    ])


def meter_actions(meter_id: int) -> InlineKeyboardMarkup:
    """Кнопки под общедомовым прибором."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📅 Внести поверку",
                             callback_data=f"meter:{meter_id}:verify"),
        InlineKeyboardButton(text="⚙️ Интервал",
                             callback_data=f"meter:{meter_id}:interval"),
    ]])
