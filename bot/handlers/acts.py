"""Приём актов поверки и опломбировки квартирных приборов учёта.

Жители сдают акты ресурснику по нескольку раз — через сайт и на личном
приёме, — а по части квартир сведения до базы начислений так и не доходят.
Эти квартиры выпадают из общедомового реестра приборов учёта, и расход на
ОДН считается неверно.

Бот собирает акты в одном месте: житель присылает фото или файл, документ
уходит председателю, а квартира попадает в список, из которого собирается
приложение к письму ресурсоснабжающей организации.

Цифры с акта бот не читает — как и с бумажного бланка показаний: рукописное
распознаётся ненадёжно, а ошибка здесь дороже ручного перепечатывания.

Роутер подключается раньше photos: тот забирает любую фотографию в личке,
а фотография акта должна попасть в этот сценарий.
"""
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from bot.config import config
from bot.keyboards.menu import BTN_METER_ACT, main_menu
from bot.services.act_service import ACT_KINDS, kind_title
from bot.services.apartment_service import find_apartment
from bot.states.acts import MeterAct
from database import repository

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")

CANCEL_WORDS = ("отмена", "❌ отмена", "стоп", "не сейчас", "позже")

INTRO = (
    "📄 <b>Акт поверки или опломбировки счётчика</b>\n\n"
    "Передам ваш акт председателю — он нужен, чтобы сведения о поверке "
    "дошли до базы начислений ресурсоснабжающей организации. Пришлите его, "
    "даже если уже сдавали через сайт или на личном приёме: именно это и "
    "проверяем.\n\n"
    "<b>Вопрос 1 из 3.</b> Номер вашей квартиры — цифрами: <code>15</code>.\n\n"
    "Чтобы выйти, отправьте «отмена»."
)


def _kind_keyboard() -> InlineKeyboardMarkup:
    labels = {"hws": "🔥 Горячая вода", "cws": "💧 Холодная вода",
              "power": "⚡ Электроэнергия", "all": "Все приборы"}
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels[code],
                              callback_data=f"act:kind:{code}")]
        for code in ACT_KINDS])


def _is_act_document(message: Message) -> bool:
    """Акт, присланный файлом: снимок без сжатия или PDF."""
    document = message.document
    if document is None:
        return False
    mime = (document.mime_type or "").lower()
    return mime.startswith("image/") or mime == "application/pdf"


async def _begin(message: Message, state: FSMContext) -> None:
    await state.set_state(MeterAct.apartment)
    await message.answer(INTRO)


@router.message(F.text == BTN_METER_ACT)
async def start_from_menu(message: Message, state: FSMContext) -> None:
    await _begin(message, state)


@router.callback_query(F.data == "start:meteract")
async def start_from_memo(callback: CallbackQuery, state: FSMContext) -> None:
    await _begin(callback.message, state)
    await callback.answer()


@router.message(MeterAct.apartment, F.text)
async def take_apartment(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text.lower() in CANCEL_WORDS:
        await _cancel(message, state)
        return

    conn = repository.connect()
    try:
        apartment = find_apartment(conn, text)
    finally:
        conn.close()

    if apartment is None:
        await message.answer(
            "Такой квартиры нет в реестре дома. Напишите номер цифрами — "
            "например, <code>15</code>.")
        return

    await state.update_data(apartment_id=apartment["id"],
                            apartment=apartment["number"])
    await state.set_state(MeterAct.kind)
    await message.answer(
        f"Записала: <b>кв. {apartment['number']}</b>.\n\n"
        "<b>Вопрос 2 из 3.</b> По какому прибору акт?",
        reply_markup=_kind_keyboard())


@router.callback_query(MeterAct.kind, F.data.startswith("act:kind:"))
async def take_kind(callback: CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":")[-1]
    await state.update_data(kind=kind_title(code))
    await state.set_state(MeterAct.document)
    await callback.message.answer(
        "<b>Вопрос 3 из 3.</b> Пришлите фото акта или файл PDF.\n\n"
        "Снимайте так, чтобы читались номер счётчика и дата поверки. "
        "Если актов несколько — присылайте по одному, я приму все.")
    await callback.answer()


@router.message(MeterAct.kind, F.text)
async def kind_by_text(message: Message, state: FSMContext) -> None:
    """Вместо кнопки написали словом — не заставляем искать кнопку."""
    text = (message.text or "").strip().lower()
    if text in CANCEL_WORDS:
        await _cancel(message, state)
        return

    known = {"гвс": "hws", "горячая": "hws", "горячей": "hws",
             "хвс": "cws", "холодная": "cws", "холодной": "cws",
             "электро": "power", "электроэнергия": "power", "свет": "power",
             "все": "all"}
    code = next((c for word, c in known.items() if word in text), None)
    if code is None:
        await message.answer("Выберите прибор кнопкой ниже 👇",
                             reply_markup=_kind_keyboard())
        return

    await state.update_data(kind=kind_title(code))
    await state.set_state(MeterAct.document)
    await message.answer(
        "<b>Вопрос 3 из 3.</b> Пришлите фото акта или файл PDF.\n\n"
        "Снимайте так, чтобы читались номер счётчика и дата поверки.")


@router.message(MeterAct.document, F.photo)
@router.message(MeterAct.document, F.document, _is_act_document)
async def take_document(message: Message, state: FSMContext) -> None:
    """Сам акт. Бот его не читает — сохраняет и передаёт председателю."""
    data = await state.get_data()
    await state.clear()

    file_id = (message.photo[-1].file_id if message.photo
               else message.document.file_id)

    conn = repository.connect()
    try:
        repository.add_meter_act(conn, data["apartment_id"],
                                 data.get("kind", ""), message.from_user.id,
                                 file_id)
    finally:
        conn.close()
    logger.info("Акт поверки: кв. %s (%s)", data.get("apartment"),
                data.get("kind", "—"))

    await _hand_over(message, data)

    is_admin = message.from_user.id in config.admin_ids
    await message.answer(
        "✅ <b>Акт принят и передан председателю.</b>\n\n"
        f"Квартира: {data.get('apartment', '—')}\n"
        f"Прибор: {data.get('kind') or '—'}\n\n"
        "Ваша квартира включена в список для обращения в ресурсоснабжающую "
        "организацию. Если актов несколько — присылайте, нажав кнопку "
        f"«{BTN_METER_ACT}» ещё раз.",
        reply_markup=main_menu(is_admin))


@router.message(MeterAct.document, F.text)
async def document_expected(message: Message, state: FSMContext) -> None:
    if (message.text or "").strip().lower() in CANCEL_WORDS:
        await _cancel(message, state)
        return
    await message.answer(
        "Жду фото акта или файл PDF. Нет под рукой — напишите «отмена», "
        "вернётесь к этому позже.")


async def _cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    is_admin = message.from_user.id in config.admin_ids
    await message.answer(
        "Хорошо, остановились. Прислать акт можно в любой момент — "
        f"кнопка «{BTN_METER_ACT}» в меню.",
        reply_markup=main_menu(is_admin))


async def _hand_over(message: Message, data: dict) -> None:
    """Председателю: сводка, следом сам документ.

    Запись в базу уже сделана: если в личку председателю сообщение не дошло
    (бот у неё не запущен, нет связи), акт не должен пропасть — квартира
    останется в списке, а документ житель пришлёт повторно.
    """
    user = message.from_user
    summary = (
        "📄 <b>Акт поверки</b>\n\n"
        f"Квартира: <b>{data.get('apartment', '—')}</b>\n"
        f"Прибор: {data.get('kind') or '—'}\n\n"
        f"Telegram: {user.full_name}"
        + (f" (@{user.username})" if user.username else "")
    )

    for admin_id in config.admin_ids:
        if not await _send(message.bot, admin_id, summary):
            continue
        try:
            await message.bot.forward_message(admin_id, message.chat.id,
                                              message.message_id)
        except TelegramAPIError as exc:
            logger.warning("Не удалось переслать акт: %s", exc)
            await _send(message.bot, admin_id,
                        "⚠️ Сам документ переслать не удалось — "
                        "попросите жителя прислать его ещё раз.")


async def _send(bot: Bot, chat_id: int, text: str) -> bool:
    try:
        await bot.send_message(chat_id, text)
        return True
    except TelegramAPIError as exc:
        logger.warning("Не удалось сообщить председателю %s об акте: %s",
                       chat_id, exc)
        return False
