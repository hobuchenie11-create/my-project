"""Готовые документы ложатся в папку председателя на компьютере."""
from dataclasses import replace
from pathlib import Path

import pytest

from bot.config import config
from bot.services import archive_service


@pytest.fixture()
def docs(tmp_path, monkeypatch):
    folder = tmp_path / "МАГИСТРАЛЬНАЯ" / "Показания за 2026 год"
    monkeypatch.setattr(archive_service, "config",
                        replace(config, docs_dir=folder))
    return folder


@pytest.fixture()
def made(tmp_path):
    def make(name: str) -> Path:
        path = tmp_path / "generated" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("отчёт", encoding="utf-8")
        return path
    return make


def test_nothing_is_copied_until_the_folder_is_set(made):
    """Файлы не должны появляться там, где председатель их не ждёт."""
    assert archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10") is None


def test_statement_lands_straight_in_the_folder(docs, made):
    """Месяц уже в имени файла — подпапка только мешала бы."""
    target = archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10")

    assert target == docs / "vedomost_2026-10.xlsx"
    assert target.read_text(encoding="utf-8") == "отчёт"


def test_registry_keeps_its_name_in_a_month_folder(docs, made):
    """Имя реестра задаёт ресурсник, и каждый месяц оно одно и то же."""
    october = archive_service.archive(made("ОЭК реестр.xls"), "2026-10")
    november = archive_service.archive(made("ОЭК реестр.xls"), "2026-11")

    assert october == docs / "2026-10" / "ОЭК реестр.xls"
    assert november == docs / "2026-11" / "ОЭК реестр.xls"
    assert october.exists() and november.exists()   # прошлый не затёрт


def test_missing_folder_is_created(docs, made):
    assert not docs.exists()

    archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10")

    assert docs.is_dir()


def test_a_closed_drive_does_not_lose_the_document(docs, made, monkeypatch):
    """Флешку вынули — документ всё равно уйдёт в чат, ошибка только в журнал."""
    def boom(*args, **kwargs):
        raise OSError(2, "No such device")

    monkeypatch.setattr(archive_service.shutil, "copy2", boom)

    assert archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10") is None


def test_note_names_the_path_for_the_message(docs, made):
    target = archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10")

    note = archive_service.archive_note(target)

    assert "Сохранено" in note and str(target) in note
    assert archive_service.archive_note(None) == ""


def test_saved_path_finds_the_copy(docs, made):
    source = made("vedomost_2026-10.xlsx")
    assert archive_service.saved_path(source, "2026-10") is None   # ещё не копировали

    archive_service.archive(source, "2026-10")

    assert archive_service.saved_path(source, "2026-10") == docs / source.name


# ---------------------------------------------------------------------------
# Две стопки: ведомости дома и реестры ресурсника
# ---------------------------------------------------------------------------

@pytest.fixture()
def two_folders(tmp_path, monkeypatch):
    statements = tmp_path / "ВЕДОМОСТИ показаний автосбор"
    registries = tmp_path / "Омскэнерго" / "Показания за 2026 год"
    monkeypatch.setattr(archive_service, "config",
                        replace(config, statements_dir=statements,
                                docs_dir=registries))
    return statements, registries


def test_statements_and_registries_go_to_their_own_folders(two_folders, made):
    statements, registries = two_folders

    vedomost = archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10")
    debtors = archive_service.archive(made("ne_peredali_2026-10.xlsx"), "2026-10")
    registry = archive_service.archive(made("ОЭК реестр.xls"), "2026-10",
                                       kind=archive_service.REGISTRY)

    assert vedomost == statements / "vedomost_2026-10.xlsx"
    assert debtors == statements / "ne_peredali_2026-10.xlsx"
    assert registry == registries / "2026-10" / "ОЭК реестр.xls"


def test_statements_fall_back_to_the_common_folder(tmp_path, monkeypatch, made):
    """STATEMENTS_DIR не заполнен — ведомости идут туда же, куда реестры."""
    common = tmp_path / "Документы дома"
    monkeypatch.setattr(archive_service, "config",
                        replace(config, statements_dir=None, docs_dir=common))

    target = archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10")

    assert target == common / "vedomost_2026-10.xlsx"


def test_registry_folder_alone_does_not_catch_statements(tmp_path, monkeypatch,
                                                         made):
    """Задана только папка ведомостей — реестр остаётся только в чате."""
    monkeypatch.setattr(archive_service, "config",
                        replace(config, statements_dir=tmp_path / "ved",
                                docs_dir=None))

    assert archive_service.archive(made("ОЭК реестр.xls"), "2026-10",
                                   kind=archive_service.REGISTRY) is None
    assert archive_service.archive(made("vedomost_2026-10.xlsx"), "2026-10")
