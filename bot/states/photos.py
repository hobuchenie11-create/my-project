"""Состояния сценария «Фото бумажного бланка»."""
from aiogram.fsm.state import State, StatesGroup


class BlankPhoto(StatesGroup):
    """Бот ждёт номер квартиры, чей бланк сфотографировали."""
    number = State()
