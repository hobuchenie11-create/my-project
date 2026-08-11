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


class Verification(StatesGroup):
    """Внесение проведённой поверки общедомового прибора."""
    verified_at = State()
    document = State()


class CouncilDigest(StatesGroup):
    """Выбор задач для сводки Совету дома и согласование перед отправкой."""
    choosing = State()
    confirming = State()


class MeterInterval(StatesGroup):
    """Изменение межповерочного интервала прибора."""
    years = State()
