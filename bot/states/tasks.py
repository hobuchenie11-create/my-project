"""Состояния сценариев модуля «Задачи»."""
from aiogram.fsm.state import State, StatesGroup


class NewTask(StatesGroup):
    title = State()
    category = State()
    due_date = State()


class CompleteTask(StatesGroup):
    """Завершение задачи, требующей суммы (например, оплата нежилого).

    После коммуналки бот спрашивает про водоснабжение: платится оно не
    каждый месяц, поэтому шаг необязательный — «нет» его пропускает.
    """
    amount = State()
    paid_at = State()
    water = State()


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
