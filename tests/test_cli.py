import pytest
import typer

from cli import select_theme, slugify
from tests.conftest import ROOT


@pytest.mark.parametrize("value, expected", [
    ("Elektron-Digitakt II", "elektron-digitakt-ii"),
    ("Thème  Éclairé!!", "theme-eclaire"),
])
def test_slugify(value, expected):
    assert slugify(value) == expected


@pytest.mark.parametrize("option", ["flat", "FLAT", "flat.json", "Elektron Dark Pro"])
def test_select_theme_by_name(option):
    assert select_theme(option) == ROOT / "themes" / "flat.json"


def test_select_theme_by_path():
    path = str(ROOT / "themes" / "dark_slate.json")
    assert str(select_theme(path)) == path


def test_select_unknown_theme():
    with pytest.raises(typer.BadParameter, match="Thème inconnu"):
        select_theme("does-not-exist")
