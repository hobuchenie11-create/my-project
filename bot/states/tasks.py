"""Состояния сценариев модуля «Задачи»."""
from aiogram.fsm.state import State, StatesGroup


class NewTask(StatesGroup):
    title = State()
    category = State()
    due_date = State()


class CompleteTask(StatesGroup):
    """Завершение задачи, требующей суммы (например, оплата нежилого)."""
    amount = State()
    paid_at = State()
