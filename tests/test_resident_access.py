"""Что видит и чего не видит житель: меню и доступ к панели председателя."""
import asyncio
from types import SimpleNamespace

from bot.config import config
from bot.handlers import admin, start, tasks
from bot.keyboards.admin_menu import BTN_ADMIN
from bot.keyboards.menu import (BTN_FAQ, BTN_HELP, BTN_HISTORY, BTN_LAST,
                                BTN_SUBMIT, main_menu)


def _buttons(markup) -> list[str]:
    return [b.text for row in markup.keyboard for b in row]


def test_resident_menu_is_limited_to_their_own_flat():
    assert _buttons(main_menu(is_admin=False)) == [
        BTN_SUBMIT, BTN_LAST, BTN_HISTORY, BTN_FAQ, BTN_HELP]


def test_chairman_menu_adds_the_admin_button():
    buttons = _buttons(main_menu(is_admin=True))
    assert buttons[:5] == _buttons(main_menu(is_admin=False))
    assert buttons[-1] == BTN_ADMIN


def test_admin_and_task_routers_are_closed_to_residents():
    """Панель председателя и задачи закрыты фильтром по ADMIN_IDS.

    Даже если житель наберёт название кнопки текстом, обработчик до него
    не дойдёт — фильтр стоит на самом роутере.
    """
    resident = SimpleNamespace(chat=SimpleNamespace(type="private"),
                               from_user=SimpleNamespace(id=999_999_999),
                               text=BTN_ADMIN)

    for router in (admin.router, tasks.router):
        passed, _ = asyncio.run(router.message.check_root_filters(resident))
        assert passed is False, router.name


def test_resident_texts_speak_as_domoved():
    """Жителю бот представляется Домоведом, а не служебным именем проекта."""
    assert "Домовед" in start.HELP_TEXT
    assert "DH OS" not in start.HELP_TEXT
    assert "15230" not in start.HELP_TEXT      # шаблон без чисел-примеров
    assert str(config.readings_day_end) in start.HELP_TEXT


# ---------------------------------------------------------------------------
# Регистрация: спрашиваем только имя
# ---------------------------------------------------------------------------

def test_registration_asks_for_a_name_not_a_full_name():
    """ФИО системе не нужны: показания привязаны к квартире, а не к человеку."""
    import inspect

    from bot.handlers import registration

    source = inspect.getsource(registration)
    assert "Фамилия Имя Отчество" not in source
    assert "Как к вам обращаться" in source
    assert "ФИО" not in source


def test_one_word_name_is_enough():
    """«Елена» — достаточно. Раньше требовалось не меньше трёх букв подряд."""
    import asyncio
    from types import SimpleNamespace

    from bot.handlers import registration

    class State:
        def __init__(self):
            self.data = {"apartment_number": "40", "apartment_id": 1}
            self.state = None

        async def get_data(self):
            return dict(self.data)

        async def update_data(self, **kwargs):
            self.data.update(kwargs)

        async def set_state(self, state):
            self.state = state

    class Msg:
        def __init__(self, text):
            self.text = text
            self.from_user = SimpleNamespace(id=1, username="u")
            self.chat = SimpleNamespace(id=1, type="private")
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

    state = State()
    message = Msg("Ия")
    asyncio.run(registration.process_name(message, state))

    assert state.data["name"] == "Ия"
    assert "Имя: Ия" in message.answers[0]
    assert state.state == registration.Registration.confirm

    short = Msg("Е")
    asyncio.run(registration.process_name(short, State()))
    assert "хотя бы две буквы" in short.answers[0]
