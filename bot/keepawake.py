"""Не даём компьютеру уснуть, пока бот работает.

Показания приходят в чат весь день, и если ноутбук уходит в спящий режим,
бот перестаёт их получать: Telegram подержит сообщения около суток, но
квитанцию житель увидит только после пробуждения.

Windows умеет держать систему бодрой по просьбе программы —
SetThreadExecutionState с флагом ES_SYSTEM_REQUIRED. Просим только не
засыпать; экран пусть гаснет как обычно, это не мешает.

Запрет действует, пока живёт процесс бота: закрыли бота (Ctrl + C) —
ноутбук снова засыпает сам, ничего возвращать вручную не нужно.

Чего это НЕ отменяет:
  • закрытие крышки — это отдельная настройка Windows;
  • ручной перевод в сон и выключение;
  • перезагрузку после обновлений Windows.
"""
import logging
import platform

logger = logging.getLogger(__name__)

# Флаги Windows API (winbase.h)
ES_CONTINUOUS = 0x80000000        # состояние действует до отмены
ES_SYSTEM_REQUIRED = 0x00000001   # системе нельзя засыпать


def keep_awake() -> bool:
    """Просит систему не уходить в спящий режим. True — просьба принята."""
    if platform.system() != "Windows":
        logger.debug("Запрет сна поддерживается только в Windows — пропускаем")
        return False

    try:
        import ctypes

        result = ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    except (AttributeError, OSError) as exc:      # pragma: no cover — только Windows
        logger.warning("Не удалось запретить спящий режим: %s", exc)
        return False

    if not result:                                # pragma: no cover — только Windows
        logger.warning("Windows отклонила запрет спящего режима")
        return False

    logger.info("Спящий режим отключён на время работы бота "
                "(экран может гаснуть — это не мешает)")
    return True


def allow_sleep() -> None:
    """Возвращает обычное поведение — вызывается при остановке бота."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes

        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except (AttributeError, OSError):             # pragma: no cover — только Windows
        pass
