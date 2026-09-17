"""Все обработчики должны быть подключены к боту.

Модуль обработчиков легко написать, покрыть тестами — и забыть строчку
``dp.include_router``. Тесты при этом зелёные (они зовут функции напрямую),
а бот в ответ молчит, и по коду это никак не видно. Ровно так и вышло с
фотографиями бланков: обработчик был, роутер не подключён.
"""
import importlib
import pkgutil
from datetime import datetime

import pytest
from aiogram.types import Chat, Message, PhotoSize, User

import bot.handlers
from bot.main import build_dispatcher


def _handler_modules() -> list[str]:
    """Все модули bot/handlers, в которых объявлен роутер."""
    names = []
    for info in pkgutil.iter_modules(bot.handlers.__path__):
        module = importlib.import_module(f"bot.handlers.{info.name}")
        if hasattr(module, "router"):
            names.append(info.name)
    return sorted(names)


@pytest.fixture(scope="module")
def attached() -> list:
    """Роутер подключается к диспетчеру только один раз — собираем его один раз."""
    return build_dispatcher().sub_routers


@pytest.mark.parametrize("name", _handler_modules())
def test_every_handler_module_is_wired_into_the_bot(name, attached):
    module = importlib.import_module(f"bot.handlers.{name}")
    assert module.router in attached, (
        f"bot/handlers/{name}.py написан, но не подключён в build_dispatcher() — "
        "бот будет молчать на такие сообщения")


def test_photos_are_handled_before_tasks(attached):
    """Снимок «файлом» приходит документом, а его забирает модуль задач."""
    from bot.handlers import photos, tasks

    assert attached.index(photos.router) < attached.index(tasks.router)


def test_a_photo_finds_its_handler():
    """Фильтры обработчика действительно совпадают с сообщением-фотографией."""
    from bot.handlers import photos

    message = Message(
        message_id=1, date=datetime.now(),
        chat=Chat(id=555, type="private"),
        from_user=User(id=555, is_bot=False, first_name="Елена"),
        photo=[PhotoSize(file_id="a", file_unique_id="u",
                         width=100, height=100)])

    matched = [h for h in photos.router.message.handlers
               if all(f.callback(message) for f in (h.filters or [])
                      if not callable(getattr(f.callback, "__self__", None)))]
    assert matched, "фотография не подходит ни под один обработчик"
    assert matched[0].callback.__name__ == "handle_photo"
