"""Состояния сценария регистрации жителя."""
from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    apartment = State()
    full_name = State()
    confirm = State()
