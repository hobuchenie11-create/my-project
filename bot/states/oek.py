"""Состояния сценария «Шаблон реестра ОЭК»."""
from aiogram.fsm.state import State, StatesGroup


class OekTemplate(StatesGroup):
    """Бот ждёт файл шаблона, который прислал ресурсник."""
    waiting = State()
