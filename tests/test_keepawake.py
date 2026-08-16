"""Запрет спящего режима: только Windows, и без падений на других системах."""
from bot import keepawake


def test_no_op_on_non_windows(monkeypatch):
    monkeypatch.setattr(keepawake.platform, "system", lambda: "Linux")
    assert keepawake.keep_awake() is False
    keepawake.allow_sleep()          # не должно ничего ломать


def test_asks_windows_not_to_sleep(monkeypatch):
    calls = []

    class FakeKernel:
        def SetThreadExecutionState(self, flags):
            calls.append(flags)
            return 1

    monkeypatch.setattr(keepawake.platform, "system", lambda: "Windows")
    monkeypatch.setitem(__import__("sys").modules, "ctypes",
                        type("ctypes", (), {"windll": type(
                            "windll", (), {"kernel32": FakeKernel()})()}))

    assert keepawake.keep_awake() is True
    # Просим не засыпать системе, но не запрещаем гасить экран
    assert calls == [keepawake.ES_CONTINUOUS | keepawake.ES_SYSTEM_REQUIRED]

    keepawake.allow_sleep()
    assert calls[-1] == keepawake.ES_CONTINUOUS      # состояние снято
