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
