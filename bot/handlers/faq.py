"""Памятки Домоведа: разделы, тексты и ответы на вопросы жителей."""
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.keyboards.faq import faq_categories, faq_memos
from bot.keyboards.menu import BTN_FAQ
from bot.services import faq_service
from database import repository
from database.models import FAQ_CATEGORIES

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")


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


async def send_memo(message: Message, memo: faq_service.Memo) -> None:
    """Отправляет памятку — с картинкой, если она к ней приложена."""
    image = memo.image_path
    if image is None:
        await message.answer(memo.text())
        return
    try:
        await message.answer_photo(FSInputFile(image), caption=memo.text())
    except Exception:                       # noqa: BLE001 — картинка не критична
        logger.warning("Не удалось отправить картинку %s", image)
        await message.answer(memo.text())


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
