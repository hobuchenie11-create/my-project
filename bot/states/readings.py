"""Состояния сценария передачи показаний."""
from aiogram.fsm.state import State, StatesGroup


class SubmitReadings(StatesGroup):
    value = State()  # последовательный ввод показаний по каждому прибору
