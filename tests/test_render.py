"""Tests de rendu « smoke » : le SVG est produit et bien formé, sans figer le design."""
import json
import xml.etree.ElementTree as ET

import pytest
import svgwrite

from renderer.device import draw_device_to_group, render_svg
from renderer.device.icons import ICONS, add_control_icon
from renderer.models import DeviceLayout
from renderer.scene import render_scene_svg
from tests.conftest import DEVICE_PATHS, port

SVG = "{http://www.w3.org/2000/svg}"


def parse(path):
    return ET.parse(path).getroot()


@pytest.mark.parametrize("icon", sorted(ICONS))
def test_every_builtin_icon_draws_something(icon):
    dwg = svgwrite.Drawing()
    add_control_icon(dwg, icon, 10, 10, 8, 6, "#fff")
    assert dwg.elements[1:], f"{icon} n'a rien dessiné"  # elements[0] = <defs>


def test_unknown_icon_raises():
    with pytest.raises(ValueError, match="Icône intégrée inconnue"):
        add_control_icon(svgwrite.Drawing(), "nope", 0, 0, 5, 5, "#fff")


@pytest.mark.parametrize("show_labels", [False, True], ids=["minimal", "detail"])
def test_full_device_renders_with_every_theme(tmp_path, full_device, theme, show_labels):
    out = tmp_path / "device.svg"
    render_svg(full_device, theme, str(out), show_labels=show_labels)
    root = parse(out)
    assert root.get("viewBox") == "0 0 100.0 50.0"
    assert root.get("width") == "100.0mm"


def test_legends_only_with_labels(full_device, theme):
    def text_count(show_labels):
        group = svgwrite.Drawing().g()
        draw_device_to_group(group, full_device, theme, show_labels=show_labels)
        return sum(1 for element in group.elements if element.elementname == "text")

    assert text_count(False) == 0
    assert text_count(True) > 0


@pytest.mark.parametrize("path", DEVICE_PATHS, ids=lambda p: p.stem)
def test_project_devices_render(tmp_path, path, theme):
    device = DeviceLayout(**json.loads(path.read_text(encoding="utf-8")))
    render_svg(device, theme, str(tmp_path / "out.svg"), show_labels=True)
    parse(tmp_path / "out.svg")


def test_scene_renders_one_cable_per_connection(tmp_path, write_json, theme):
    device = {
        "manufacturer": "Acme", "model": "Box", "physical": {"width_mm": 100, "height_mm": 50},
        "ports": [port("midi-out", "output", y=0.0), port("midi-in", "input", y=0.0),
                  port("audio-out", "output", "audio"), port("audio-in", "input", "audio")],
    }
    device_path = write_json("box.json", device)
    scene_path = write_json("scene.json", {
        "name": "Test",
        "devices": [
            {"id": "a", "device": str(device_path), "position": {"type": "absolute", "x": 0, "y": 0}},
            {"id": "b", "device": str(device_path), "position": {"type": "relative", "target": "a", "spacing_mm": 20}},
        ],
        "connections": [
            {"source": {"device_id": "a", "port_id": "midi-out"}, "target": {"device_id": "b", "port_id": "midi-in"}},
            {"source": {"device_id": "a", "port_id": "audio-out"}, "target": {"device_id": "b", "port_id": "audio-in"}},
        ],
    })
    out = tmp_path / "scene.svg"
    render_scene_svg(str(scene_path), str(out), theme, padding_mm=10)

    root = parse(out)
    # 2 appareils de 100 mm + 20 mm d'écart + 2 × 10 mm de marge
    assert root.get("viewBox") == "0 0 240.0 70.0"
    cables = [p for p in root.iter(f"{SVG}path") if p.get("opacity") == "0.9"]
    assert len(cables) == 2
    assert {c.get("stroke") for c in cables} == {"#e67e22", "#3498db"}


def test_empty_scene_raises(tmp_path, write_json, theme):
    scene_path = write_json("scene.json", {"name": "Vide"})
    with pytest.raises(ValueError, match="aucun appareil"):
        render_scene_svg(str(scene_path), str(tmp_path / "out.svg"), theme)
