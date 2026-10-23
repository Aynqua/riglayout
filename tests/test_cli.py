import pytest
import typer

import json

from cli import default_output_path, select_theme, slugify
from renderer.models import Theme
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


@pytest.mark.parametrize("detail, expected", [(False, "acme-box-elektron-dark-pro.svg"), (True, "acme-box-elektron-dark-pro-detail.svg")])
def test_default_output_path_differs_in_detail(detail, expected):
    theme = Theme(**json.loads((ROOT / "themes" / "flat.json").read_text(encoding="utf-8")))
    assert default_output_path("Acme Box", theme, detail).name == expected


def test_device_outputs_go_in_their_own_folder_and_scenes_at_root():
    theme = Theme(**json.loads((ROOT / "themes" / "flat.json").read_text(encoding="utf-8")))
    device = default_output_path("Roland TB-3", theme, False, in_own_folder=True)
    scene = default_output_path("scene-nays_2026", theme, True)
    assert device.as_posix() == "output/roland-tb-3/roland-tb-3-elektron-dark-pro.svg"
    assert scene.as_posix() == "output/scene-nays-2026-elektron-dark-pro-detail.svg"
