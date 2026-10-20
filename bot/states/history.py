"""Состояния сценария «История квартиры»."""
from aiogram.fsm.state import State, StatesGroup


class ApartmentHistory(StatesGroup):
    """Бот ждёт номер квартиры, историю показаний которой нужно показать."""
    number = State()
