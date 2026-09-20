"""Памятки Домоведа: разделы, тексты и ответы на вопросы жителей."""
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.keyboards.faq import faq_categories, faq_memos, memo_buttons
from bot.keyboards.menu import BTN_FAQ
from bot.services import faq_service
from database import repository
from database.models import FAQ_CATEGORIES

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")

# Подпись к картинке Телеграм принимает не длиннее 1024 символов. Памятки
# про ворота и GSM-модуль длиннее — целиком в подпись они не помещаются, и
# без разделения житель не получил бы плакат совсем
CAPTION_LIMIT = 1024


@router.message(F.text == BTN_FAQ)
async def show_categories(message: Message) -> None:
    conn = repository.connect()
    try:
        categories = faq_service.categories(conn)
    finally:
        conn.close()

    if not categories:
        await message.answer("Памятки пока не заполнены. Загляните позже.")
        return

    await message.answer(
        "❓ <b>Памятки по дому</b>\n\n"
        "Выберите раздел — или просто задайте вопрос своими словами, "
        "я поищу ответ.",
        reply_markup=faq_categories(categories))


@router.callback_query(F.data.startswith("faq:cat:"))
async def show_category(callback: CallbackQuery) -> None:
    category = callback.data.split(":")[-1]
    conn = repository.connect()
    try:
        memos = faq_service.by_category(conn, category)
    finally:
        conn.close()

    title = FAQ_CATEGORIES.get(category, category)
    await callback.message.edit_text(
        f"{title}\n\nВыберите памятку:",
        reply_markup=faq_memos(memos, back=True))
    await callback.answer()


@router.callback_query(F.data == "faq:back")
async def back_to_categories(callback: CallbackQuery) -> None:
    conn = repository.connect()
    try:
        categories = faq_service.categories(conn)
    finally:
        conn.close()

    await callback.message.edit_text(
        "❓ <b>Памятки по дому</b>\n\nВыберите раздел:",
        reply_markup=faq_categories(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("faq:memo:"))
async def show_memo(callback: CallbackQuery) -> None:
    code = callback.data.split(":", 2)[-1]
    conn = repository.connect()
    try:
        memo = faq_service.by_code(conn, code)
    finally:
        conn.close()

    if memo is None:
        await callback.answer("Памятка не найдена")
        return

    await send_memo(callback.message, memo)
    await callback.answer()


@router.callback_query(F.data.startswith("faq:poster:"))
async def send_poster(callback: CallbackQuery) -> None:
    """Плакат файлом: Телеграм не сжимает его, мелкий шрифт остаётся читаемым.

    Такой файл житель сохраняет в телефон и открывает потом сам — у ворот,
    где интернета может и не быть.
    """
    code = callback.data.split(":", 2)[-1]
    conn = repository.connect()
    try:
        memo = faq_service.by_code(conn, code)
    finally:
        conn.close()

    image = memo.image_path if memo else None
    if image is None:
        await callback.answer("Плакат не найден")
        return

    try:
        await callback.message.answer_document(
            FSInputFile(image),
            caption=f"<b>{memo.title}</b>\n\n"
                    "Это плакат из подъезда. Файл можно сохранить в телефон "
                    "и открыть без интернета.")
    except TelegramAPIError as exc:
        logger.warning("Не удалось отправить плакат «%s»: %s", code, exc)
        await callback.answer("Не удалось отправить файл, попробуйте позже")
        return

    await callback.answer()


async def send_memo(message: Message, memo: faq_service.Memo,
                    with_action: bool = True) -> None:
    """Отправляет памятку — с плакатом и кнопками, если они есть.

    Памятка объясняет, что нужно сделать, а кнопка сразу это начинает:
    прочитать и тут же оформиться удобнее, чем искать нужный пункт меню.
    Внутри чужого сценария кнопка не нужна — `with_action=False`: нажав её,
    житель бросит начатое и уйдёт в начало другого разговора.

    Длинную памятку шлём двумя сообщениями: плакат с заголовком в подписи,
    следом текст. Кнопки — под последним сообщением, чтобы житель нажимал
    их, дочитав до конца.
    """
    keyboard = memo_buttons(memo, with_action)
    text = memo.text()
    image = memo.image_path
    if image is None:
        await message.answer(text, reply_markup=keyboard)
        return

    if len(text) <= CAPTION_LIMIT:
        caption, follow_up = text, ""
    else:
        caption, follow_up = f"<b>{memo.title}</b>", memo.body

    try:
        await message.answer_photo(
            FSInputFile(image), caption=caption,
            reply_markup=None if follow_up else keyboard)
    except Exception:                       # noqa: BLE001 — картинка не критична
        logger.warning("Не удалось отправить картинку %s", image)
        await message.answer(text, reply_markup=keyboard)
        return

    if follow_up:
        await message.answer(follow_up, reply_markup=keyboard)


async def send_memo_by_code(message: Message, code: str,
                            with_action: bool = False) -> bool:
    """Памятка по коду — для сценариев, которые шлют её по ходу разговора.

    Памятку могли переименовать или удалить: разговор из-за этого прерываться
    не должен, данные жителя важнее. False — памятка не ушла.
    """
    conn = repository.connect()
    try:
        memo = faq_service.by_code(conn, code)
    finally:
        conn.close()

    if memo is None:
        logger.warning("Памятка «%s» не найдена — пропускаю", code)
        return False
    try:
        await send_memo(message, memo, with_action=with_action)
    except TelegramAPIError as exc:
        logger.warning("Не удалось отправить памятку «%s»: %s", code, exc)
        return False
    return True


async def answer_question(message: Message, tg_id: int | None,
                          apartment: str = "") -> bool:
    """Ищет ответ на вопрос жителя. False — вопрос остался без ответа.

    Вызывается из обработчика свободного текста: сначала бот пробует
    прочитать сообщение как показания, и только потом — как вопрос.
    """
    conn = repository.connect()
    try:
        found = faq_service.search(conn, message.text or "")
        if not found:
            faq_service.remember_gap(conn, tg_id, apartment, message.text or "")
    finally:
        conn.close()

    if not found:
        logger.info("Вопрос без ответа: %s", (message.text or "")[:80])
        await message.answer(faq_service.NOT_FOUND)
        return False

    await send_memo(message, found[0])
    if len(found) > 1:
        await message.answer("Возможно, пригодится и это:",
                             reply_markup=faq_memos(found[1:]))
    return True
