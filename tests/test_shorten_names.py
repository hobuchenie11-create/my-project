"""Разовая чистка старых записей: в имени остаётся только имя.

Раньше бот просил ФИО. Фамилии и отчества системе не нужны, но записи
уже есть — и удалять их вслепую нельзя: сначала показываем председателю,
что именно изменится, и только по её команде правим.
"""
import pytest

from database import repository
from database.init_db import init_db
from scripts import shorten_names
from scripts.shorten_names import (is_ambiguous, main, planned_changes,
                                   short_name)


@pytest.mark.parametrize("stored, expected", [
    ("Иванова Мария Петровна", "Мария"),      # отчество последним — имя вторым
    ("Пётр Сергеевич", "Пётр"),
    ("Мария Иванова", "Мария"),               # без отчества — первое слово
    ("Елена", "Елена"),                       # уже одно слово
    ("  Ия  ", "Ия"),
    ("", ""),
])
def test_name_is_taken_out_of_any_form(stored, expected):
    assert short_name(stored) == expected


@pytest.mark.parametrize("stored, ambiguous", [
    ("Иванова Мария Петровна", False),
    ("Елена Викторовна", False),
    ("Мария Иванова", True),                  # где имя — не разобрать
    ("Петров Пётр", True),
    ("Елена", False),
])
def test_two_words_without_a_patronymic_are_flagged(stored, ambiguous):
    assert is_ambiguous(stored) is ambiguous


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "names.db"
    init_db(path, apartments_count=5, nonresidential_count=0)
    conn = repository.connect(path)
    for tg_id, number, name in ((1, "1", "Иванова Мария Петровна"),
                                (2, "2", "Елена"),
                                (3, "3", "Петров Пётр")):
        flat = repository.get_apartment_by_number(conn, number)
        repository.create_user(conn, tg_id, name, flat["id"])
    conn.commit()
    conn.close()

    real_connect = repository.connect
    monkeypatch.setattr(repository, "connect",
                        lambda db_path=None: real_connect(db_path or path))
    # Копию делаем с временной базы, а не с рабочей
    backup = tmp_path / "копия.db"
    monkeypatch.setattr(shorten_names, "make_backup",
                        lambda: (backup.write_bytes(path.read_bytes()), backup)[1])
    return path


def _names(db):
    conn = repository.connect(db)
    try:
        return {u["apartment_number"]: u["full_name"]
                for u in repository.list_users(conn)}
    finally:
        conn.close()


def test_preview_changes_nothing(db, capsys):
    """Без --apply база остаётся как была — это только просмотр."""
    assert main([]) == 0

    out = capsys.readouterr().out
    assert "«Иванова Мария Петровна» -> «Мария»" in out
    assert "база не изменена" in out
    assert "проверьте порядок слов" in out       # про «Петров Пётр»
    assert _names(db)["1"] == "Иванова Мария Петровна"


def test_apply_shortens_and_backs_up(db, capsys):
    assert main(["--apply"]) == 0

    out = capsys.readouterr().out
    assert "Резервная копия базы" in out
    assert "исправлено записей — 2" in out

    names = _names(db)
    assert names["1"] == "Мария"
    assert names["2"] == "Елена"      # одно слово — не трогали
    assert names["3"] == "Петров"     # спорный случай, первое слово


def test_second_run_finds_nothing(db, capsys):
    main(["--apply"])
    capsys.readouterr()

    assert main([]) == 0
    assert "Менять нечего" in capsys.readouterr().out


def test_planned_changes_skips_what_is_already_short(db):
    conn = repository.connect(db)
    try:
        flats = {c[1] for c in planned_changes(conn)}
    finally:
        conn.close()

    assert flats == {"1", "3"}
