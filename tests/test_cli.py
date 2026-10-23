import pytest
import typer

import json
from pathlib import Path

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
    assert default_output_path("Acme Box", theme, detail, Path("output")).name == expected


def test_outputs_are_grouped_by_machine_and_by_scene():
    from cli import device_output_folder, scene_output_folder
    from tests.conftest import make_device
    device = make_device(model="TB-3").copy(update={"manufacturer": "Roland"})
    assert device_output_folder(device).as_posix() == "output/roland-tb-3"
    assert scene_output_folder(Path("scenes/nays_2026_carre.json")).as_posix() == "output/scenes/nays-2026-carre"


def test_render_all_generates_every_device_and_scene(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from cli import DEVICES_DIR, SCENES_DIR, app
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["render-all", "--theme", "flat"])
    assert result.exit_code == 0, result.output
    svgs = list((tmp_path / "output").rglob("*.svg"))
    expected = (len(list(DEVICES_DIR.glob("*/*.json"))) + len(list(SCENES_DIR.glob("*.json")))) * 2
    assert len(svgs) == expected
    assert sum(1 for p in svgs if p.stem.endswith("-detail")) == expected // 2
