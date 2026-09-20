"""Сценарий «Новый собственник»: три вопроса по очереди.

Список из нескольких пунктов человек выполняет наполовину — отвечает на
первое и забывает про телефон. Поэтому бот спрашивает по одному и в конце
одним сообщением передаёт всё председателю: квартиру, ФИО с телефоном,
номер авто.

Копию выписки из ЕГРН бот не принимает. Это документ с персональными
данными, и житель отправляет его председателю напрямую: в переписке с
ботом он только лишний раз хранится, а на воротах всё равно оформляет
человек. Бот лишь напоминает, что без копии доступ не оформляется.

Сценарий начинается кнопкой под памяткой «Новому собственнику». Памятку
житель находит обычным вопросом («купил квартиру», «как оформиться»),
так что отдельной кнопки в меню не нужно.
"""
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import config
from bot.handlers.faq import send_memo
from bot.keyboards.menu import main_menu
from bot.services import faq_service
from bot.services.apartment_service import find_apartment
from bot.states.newcomer import Newcomer
from database import repository

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")

CANCEL_WORDS = ("отмена", "стоп", "позже", "не сейчас")
NO_CAR_WORDS = ("нет", "нету", "без авто", "без машины", "не нужно", "-")

# Повторяется и в памятке, и в конце разговора: житель должен уйти,
# помня про выписку, иначе ворота ему не откроются
EGRN_NOTE = ("Копию выписки из ЕГРН отправьте председателю напрямую — "
             "в Телеграм, в WhatsApp или передайте при встрече. Мне, боту, "
             "её присылать не нужно.")


@router.callback_query(F.data == "start:newcomer")
async def start(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка под памяткой «Новому собственнику»."""
    await state.set_state(Newcomer.apartment)
    await callback.message.answer(
        "🔑 <b>Оформление нового собственника</b>\n\n"
        "Задам три вопроса по очереди. Прервётесь — начнём заново, "
        "ничего страшного.\n\n"
        "<b>Вопрос 1 из 3.</b> Какая у вас квартира? Напишите номер: "
        "<code>15</code>.\n\n"
        "Чтобы выйти, отправьте «отмена».")
    await callback.answer()


@router.message(Newcomer.apartment, F.text)
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

    await state.update_data(apartment=apartment["number"])
    await message.answer(f"Записала: <b>кв. {apartment['number']}</b>.")
    await _ask_contacts(message, state)


async def _ask_contacts(message: Message, state: FSMContext) -> None:
    await state.set_state(Newcomer.contacts)
    await message.answer(
        "<b>Вопрос 2 из 3.</b> ФИО собственника и контактный телефон — "
        "одним сообщением.\n\n"
        "Например:\n<code>Иванова Мария Петровна, +7 902 676-78-81</code>\n\n"
        "Телефон программируется в GSM-модуль ворот: с него ворота "
        "открываются звонком, бесплатно.")
    # Про 10 ₽ на каждые ворота человек узнаёт до того, как назовёт номер:
    # иначе номер запишут, а ворота не откроются — и виноватым окажется бот
    await _send_memo(message, "gsm-modul")


@router.message(Newcomer.contacts, F.text)
async def take_contacts(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text.lower() in CANCEL_WORDS:
        await _cancel(message, state)
        return
    if len(text) < 6 or not any(ch.isdigit() for ch in text):
        await message.answer(
            "Нужны и ФИО, и телефон — иначе номер не записать в ворота. "
            "Пример: <code>Иванова Мария Петровна, +7 902 676-78-81</code>")
        return

    await state.update_data(contacts=text)
    await state.set_state(Newcomer.car)
    await message.answer(
        "<b>Вопрос 3 из 3.</b> Номер автомобиля — например "
        "<code>1234 АВ-55</code>.\n\n"
        "Машины нет — напишите «нет».")


@router.message(Newcomer.car, F.text)
async def take_car(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text.lower() in CANCEL_WORDS and text.lower() not in NO_CAR_WORDS:
        await _cancel(message, state)
        return

    car = "" if text.lower() in NO_CAR_WORDS else text
    data = await state.get_data()
    await state.clear()

    await _hand_over(message, data, car)

    is_admin = message.from_user.id in config.admin_ids
    await message.answer(
        "✅ <b>Готово, данные переданы председателю.</b>\n\n"
        f"Квартира: {data.get('apartment', '—')}\n"
        f"Собственник: {data.get('contacts', '—')}\n"
        f"Автомобиль: {car or 'нет'}\n\n"
        "Председатель запишет ваш номер в модуль ворот и свяжется с вами, "
        "если что-то понадобится уточнить.\n\n"
        f"❗ Остался один шаг. {EGRN_NOTE} Без неё доступ к воротам "
        "не оформляется: так никто не получит въезд по чужой квартире.",
        reply_markup=main_menu(is_admin))

    # То, что новосёлу понадобится в первый же день: как заехать во двор и
    # как попасть в него пешком. Искать эти памятки в меню он ещё не умеет
    await message.answer("Чтобы вы освоились, вот две памятки по дому 👇")
    for code in ("vorota", "dostup-vo-dvor"):
        await _send_memo(message, code)


async def _send_memo(message: Message, code: str) -> None:
    """Отправляет памятку по ходу разговора — тем же видом, что и в меню.

    Памятку могли переименовать или удалить: сценарий из-за этого прерываться
    не должен, данные жителя важнее.
    """
    conn = repository.connect()
    try:
        memo = faq_service.by_code(conn, code)
    finally:
        conn.close()

    if memo is None:
        logger.warning("Памятка «%s» не найдена — пропускаю", code)
        return
    try:
        await send_memo(message, memo)
    except TelegramAPIError as exc:
        logger.warning("Не удалось отправить памятку «%s»: %s", code, exc)


async def _cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    is_admin = message.from_user.id in config.admin_ids
    await message.answer(
        "Хорошо, остановились. Вернуться можно в любой момент — "
        "напишите «новый собственник».", reply_markup=main_menu(is_admin))


async def _hand_over(message: Message, data: dict, car: str) -> None:
    """Передаёт собранное председателю.

    Пишем в журнал в любом случае: если в личку председателю сообщение не
    дошло (бот у неё не запущен, нет связи), данные жителя не должны
    пропасть бесследно.
    """
    user = message.from_user
    summary = (
        "🔑 <b>Новый собственник</b>\n\n"
        f"Квартира: <b>{data.get('apartment', '—')}</b>\n"
        f"Собственник: {data.get('contacts', '—')}\n"
        f"Автомобиль: {car or 'нет'}\n\n"
        f"Telegram: {user.full_name}"
        + (f" (@{user.username})" if user.username else "")
        + "\n\nКопию выписки из ЕГРН житель отправит вам напрямую — "
          "я попросила об этом."
    )

    conn = repository.connect()
    try:
        repository.log_event(
            conn, user.id, "newcomer",
            f"кв. {data.get('apartment', '?')}: {data.get('contacts', '')}; "
            f"авто: {car or 'нет'}")
    finally:
        conn.close()
    logger.info("Новый собственник: кв. %s", data.get("apartment"))

    for admin_id in config.admin_ids:
        await _send(message.bot, admin_id, summary)


async def _send(bot: Bot, chat_id: int, text: str) -> bool:
    try:
        await bot.send_message(chat_id, text)
        return True
    except TelegramAPIError as exc:
        logger.warning("Не удалось сообщить председателю %s о новом "
                       "собственнике: %s", chat_id, exc)
        return False
