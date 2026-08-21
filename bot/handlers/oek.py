"""Реестр ОЭК: приём шаблона от ресурсника и выгрузка заполненного файла.

Раз в месяц ОЭК присылает книгу «Реестр индивидуальных приборов учета».
Председатель пересылает её боту — бот кладёт файл в папку шаблонов и дальше,
20 числа в 14:30, сам возвращает его заполненным (см. bot/scheduler.py).

Роутер подключается раньше tasks.router: тот забирает любой присланный
документ как правки годового плана, а .xls к нему отношения не имеет.
"""
import asyncio
import logging
from datetime import date
from pathlib import Path

from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import config
from bot.keyboards.admin_menu import BTN_OEK, BTN_OEK_TEMPLATE, admin_menu
from bot.scheduler import deliver_oek_registry
from bot.services.reading_service import current_period, period_title
from bot.states.oek import OekTemplate
from excel.oek_registry import OekFormatError

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private",
                      F.from_user.id.in_(config.admin_ids))


def _is_registry_file(name: str) -> bool:
    return name.lower().endswith((".xls", ".xlsx", ".xlsm"))


def _is_xls(message: Message) -> bool:
    """Старый .xls присылает только ОЭК — правки годового плана бот ждёт в .xlsx."""
    document = message.document
    return bool(document and (document.file_name or "").lower().endswith(".xls"))


@router.message(OekTemplate.waiting, F.text)
async def leave_waiting(message: Message, state: FSMContext) -> None:
    """Прислали текст вместо файла — снимаем ожидание и пропускаем дальше.

    Иначе состояние висело бы до следующего документа, и правки годового
    плана бот однажды принял бы за шаблон ОЭК.
    """
    await state.clear()
    raise SkipHandler


@router.message(F.text == BTN_OEK)
async def send_registry(message: Message) -> None:
    """Заполнить реестр ОЭК прямо сейчас — теми же показаниями, что в ведомости."""
    from reports.oek_registry import NoTemplateError, generate_oek_registry

    period = current_period()
    await message.answer("Заполняю реестр ОЭК…")
    try:
        result = await asyncio.to_thread(generate_oek_registry, period)
    except (NoTemplateError, OekFormatError) as exc:
        await message.answer(f"{exc}\n\nПришлите файл сюда — я его сохраню.")
        return
    except Exception as exc:                       # noqa: BLE001 — покажем причину
        logger.exception("Не удалось заполнить реестр ОЭК")
        await message.answer(f"Не удалось заполнить реестр: {exc}")
        return

    if result.template_period and result.template_period != period:
        await message.answer(
            f"⚠️ Шаблон помечен периодом {period_title(result.template_period)}, "
            f"а показания взяты за {period_title(period)}. "
            "Если ресурсник прислал новый файл — пришлите его сюда.")
    await deliver_oek_registry(message.bot, message.chat.id, result,
                               period_title(period))


@router.message(F.text == BTN_OEK_TEMPLATE)
async def ask_template(message: Message, state: FSMContext) -> None:
    from reports.oek_registry import find_template, templates_dir

    current = find_template()
    known = (f"Сейчас лежит: <b>{current.name}</b>\n\n" if current
             else "Шаблона пока нет.\n\n")
    await state.set_state(OekTemplate.waiting)
    await message.answer(
        "📨 <b>Шаблон реестра ОЭК</b>\n\n" + known +
        "Пришлите файл, который прислал ресурсник (.xls или .xlsx) — "
        "я сохраню его и буду заполнять этим шаблоном.\n\n"
        "Заполняется только лист по электроэнергии, колонка «Текущие "
        "показания — день»; листы по горячей и холодной воде бот убирает.\n\n"
        f"Папка шаблонов: <code>{templates_dir()}</code>")


@router.message(OekTemplate.waiting, F.document)
@router.message(F.document, _is_xls)
async def save_registry_template(message: Message, state: FSMContext) -> None:
    """Присланный .xls (или любой файл в режиме ожидания) — новый шаблон ОЭК."""
    from reports.oek_registry import find_template, save_template

    from excel.oek_registry import inspect_template

    name = message.document.file_name or ""
    if not _is_registry_file(name):
        await message.answer("Жду книгу Excel: .xls или .xlsx.")
        return

    inbox = config.reports_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    downloaded = inbox / f"{date.today().isoformat()}_{name}"
    await message.bot.download(message.document, destination=downloaded)
    await state.clear()

    # Разбираем до того, как трогать папку шаблонов: негодный файл не должен
    # вытеснить рабочий — иначе 20 числа заполнять будет нечем
    try:
        info = await asyncio.to_thread(inspect_template, downloaded)
    except OekFormatError as exc:
        await message.answer(
            f"Файл не похож на реестр ОЭК, прежний шаблон оставил на месте.\n\n{exc}",
            reply_markup=admin_menu())
        return
    except Exception as exc:                       # noqa: BLE001 — покажем причину
        logger.exception("Не удалось разобрать шаблон ОЭК %s", downloaded)
        await message.answer(
            f"Не удалось прочитать файл ({exc}). Прежний шаблон оставил на месте.",
            reply_markup=admin_menu())
        return

    # Старый шаблон убираем: заполняем всегда по самому свежему, и два файла
    # в папке — верный способ однажды сдать реестр прошлого месяца
    previous = find_template()
    saved = await asyncio.to_thread(save_template, downloaded)
    if previous and previous.resolve() != saved.resolve():
        previous.unlink(missing_ok=True)

    await _describe_template(message, saved, info, replaced=previous)


async def _describe_template(message: Message, saved: Path, info,
                             replaced: Path | None = None) -> None:
    """Показываем председателю, что бот в шаблоне разобрал."""
    from reports.oek_registry import templates_dir

    lines = [f"✅ Шаблон ОЭК принят: <b>{saved.name}</b>", ""]
    if info.period:
        lines.append(f"Период в шапке: {period_title(info.period)}")
    lines.append(f"Заполняемый лист: {info.sheet}")
    lines.append(f"Строк с квартирами: {info.rows}")
    lines.append(f"Колонка показаний: «{info.reading_header}»")
    if info.date_header:
        lines.append(f"Колонка даты: «{info.date_header}»")
    if info.dropped_sheets:
        lines.append("При выгрузке уберу листы: " + ", ".join(info.dropped_sheets))
    if replaced and replaced.name != saved.name:
        lines.append(f"Прежний шаблон удалён: {replaced.name}")
    lines += ["", f"Папка: <code>{templates_dir()}</code>",
              f"Реестр уйдёт {config.oek_day} числа в "
              f"{config.oek_hour:02d}:{config.oek_minute:02d}."]
    await message.answer("\n".join(lines), reply_markup=admin_menu())
