"""Перенос столбцов готового реестра ОЭК в другой файл."""
from dataclasses import replace
from datetime import date

import pytest

from bot.config import config
from excel.oek_registry import FilledRow, fill_registry, read_filled
from reports import oek_columns
from tests.test_oek_registry import (DATE_COL, FIRST_DATA_ROW, READING_COL,
                                     make_xls)


@pytest.fixture()
def registry(tmp_path, monkeypatch):
    """Собранный реестр за август: кв. 1 сдала, кв. 2 — нет."""
    template = make_xls(tmp_path / "oek.xls", flats=("1", "2"))
    out_dir = tmp_path / "generated"
    out_dir.mkdir()
    fill_registry(template, {"1": 31668.0}, out_dir / "reestr_oek_2026-08.xls",
                  taken_on=date(2026, 8, 20), known_apartments={"1", "2"})
    monkeypatch.setattr(oek_columns, "config",
                        replace(config, reports_dir=out_dir))
    return out_dir


def test_reads_back_what_was_written(registry):
    rows, layout = read_filled(registry / "reestr_oek_2026-08.xls")

    assert [row.apartment for row in rows] == ["1", "2"]
    assert rows[0].reading == 31668
    assert rows[0].taken_on == date(2026, 8, 20)
    # У непередавшей квартиры пусто и в показаниях, и в дате
    assert rows[1].reading is None
    assert rows[1].taken_on is None
    assert (layout.reading_col, layout.date_col) == (READING_COL, DATE_COL)


def test_table_is_ready_for_any_spreadsheet(registry):
    rows, _ = read_filled(registry / "reestr_oek_2026-08.xls")
    lines = oek_columns.as_table(rows).split("\n")

    assert lines[0] == "Квартира\tПоказания\tДата снятия"
    assert lines[1] == "1\t31668\t20.08.2026"
    assert lines[2] == "2\t\t"           # не сдала — обе ячейки пустые


def test_paste_block_keeps_the_gap_between_columns(registry):
    """Между показаниями и датой у ОЭК ночь и полупик — их отдаём пустыми.

    Иначе при вставке в другой файл колонки съезжают на две влево.
    """
    rows, layout = read_filled(registry / "reestr_oek_2026-08.xls")
    width = layout.date_col - layout.reading_col + 1
    lines = oek_columns.as_paste_block(rows, width).split("\n")

    assert width == 4                              # K, L, M, N
    assert lines[0].split("\t") == ["31668", "", "", "20.08.2026"]
    assert lines[1].split("\t") == ["", "", "", ""]


def test_finds_the_fallback_file_when_the_main_one_was_busy(registry):
    """Основной файл был открыт в Excel — берём тот, что бот положил рядом."""
    (registry / "reestr_oek_2026-08_2008_1430.xls").write_bytes(
        (registry / "reestr_oek_2026-08.xls").read_bytes())

    found = oek_columns.find_registry("2026-08")
    assert found.name.startswith("reestr_oek_2026-08")


def test_missing_registry_says_how_to_build_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(oek_columns, "config",
                        replace(config, reports_dir=tmp_path / "empty"))

    assert oek_columns.main(["2026-08"]) == 1
    assert "python -m reports.oek_registry" in capsys.readouterr().out


def test_values_are_printed_without_a_trailing_zero():
    row = FilledRow(apartment="1", reading=31668.0, taken_on=None)
    assert oek_columns._reading(row) == "31668"
    assert oek_columns._date(row) == ""
