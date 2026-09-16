"""Состояния сценария «Счётчики квартиры»."""
from aiogram.fsm.state import State, StatesGroup


class ApartmentMeters(StatesGroup):
    """Бот ждёт номер квартиры, набор приборов которой нужно поправить."""
    number = State()
