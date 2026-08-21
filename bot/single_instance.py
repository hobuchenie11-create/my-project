"""Один Домовед на компьютер: второй запуск не должен драться за Telegram.

Бот стартует сам при входе в систему (задание «DH OS (Домовед)» в
Планировщике заданий) — и его же по привычке запускают руками из терминала.
Двух процессов на одном токене Telegram не разводит: getUpdates отдаёт
Conflict то одному, то другому, и показания жителей теряются.

Сторож — именованный мьютекс Windows. Он живёт ровно столько, сколько живёт
процесс: даже если бота убили насмерть (taskkill, синий экран), «застрявшего
замка» не останется и следующий запуск пройдёт нормально. Файл-замок так не
умеет — его пришлось бы чистить руками.
"""
import logging
import platform

logger = logging.getLogger(__name__)

# Без префикса Global\ — мьютекс виден в пределах сеанса пользователя, а оба
# запуска бота (автозапуск и терминал) идут именно в нём. Global\ потребовал
# бы отдельной привилегии и прав администратора.
MUTEX_NAME = "DH_OS_bot_single_instance"
ERROR_ALREADY_EXISTS = 183

# Держим ручку до конца работы процесса: закроется — мьютекс освободится
_handle = None


def acquire(name: str = MUTEX_NAME) -> bool:
    """True — мы единственный экземпляр; False — бот уже работает.

    Если проверить не удалось (не Windows, отказ WinAPI), возвращаем True:
    сторож не должен мешать запуску, когда сам сломался.
    """
    global _handle

    if platform.system() != "Windows":
        return True
    if _handle is not None:
        return True                      # уже заняли в этом же процессе

    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CreateMutexW.argtypes = [wintypes.LPCVOID, wintypes.BOOL,
                                          wintypes.LPCWSTR]
        handle = kernel32.CreateMutexW(None, True, name)
        error = ctypes.get_last_error()
    except (AttributeError, OSError) as exc:   # pragma: no cover — только Windows
        logger.warning("Не удалось проверить, не запущен ли бот уже: %s", exc)
        return True

    if not handle:                             # pragma: no cover — только Windows
        logger.warning("Windows не дала создать сторож запуска (код %s)", error)
        return True

    if error == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False

    _handle = handle
    return True
