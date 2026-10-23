"""Données de test indépendantes des vrais layouts (dont le design évolue)."""
import json
from pathlib import Path

import pytest

from renderer.device.icons import ICONS
from renderer.models import DeviceLayout, Theme

ROOT = Path(__file__).resolve().parent.parent
THEME_PATHS = sorted((ROOT / "themes").glob("*.json"))
DEVICE_PATHS = sorted((ROOT / "devices").glob("*/*.json"))


def make_device(ports=None, width_mm=100.0, height_mm=50.0, components=None, model="Test"):
    return DeviceLayout(
        manufacturer="Acme",
        model=model,
        physical={"width_mm": width_mm, "height_mm": height_mm},
        components=components or [],
        ports=ports or [],
    )


def port(port_id, direction, signal="midi", **extra):
    return {"id": port_id, "label": port_id, "direction": direction, "signal": signal, **extra}


def all_components():
    """Un composant de chaque type + un bouton par icône intégrée."""
    components = [
        {"type": "frame", "x": 0.5, "y": 0.5, "width_mm": 90, "height_mm": 40, "legend": "Cadre", "legend_position": "bottom_left"},
        {"type": "screen", "x": 0.2, "y": 0.2, "width_mm": 20, "height_mm": 10},
        {"type": "encoder", "x": 0.4, "y": 0.2, "diameter_mm": 8},
        {"type": "led", "x": 0.5, "y": 0.2, "diameter_mm": 2},
        {"type": "screw", "x": 0.6, "y": 0.2, "diameter_mm": 3},
        {"type": "pad", "x": 0.7, "y": 0.2, "width_mm": 10, "height_mm": 10, "legend": "1", "underline": True},
        {"type": "button", "x": 0.8, "y": 0.2, "width_mm": 10, "height_mm": 6, "legend": "FUNC", "fill": "#ff8800"},
        {"type": "button", "x": 0.9, "y": 0.2, "width_mm": 10, "height_mm": 6,
         "icon_path_d": "M0 0H10V10H0Z", "icon_view_box": [0, 0, 10, 10]},
        {"type": "logo", "x": 0.9, "y": 0.9, "width_mm": 8, "height_mm": 4,
         "icon_path_d": "M0 0H20V10H0Z", "icon_view_box": [0, 0, 20, 10]},
        {"type": "logo", "x": 0.1, "y": 0.9, "width_mm": 6, "height_mm": 4, "icon_mode": "stroke", "icon_stroke_width": 2,
         "icon_path_d": "M2 2H18V8", "icon_view_box": [0, 0, 20, 10]},
        {"type": "text", "x": 0.05, "y": 0.05, "legend": "Acme", "text_anchor": "start", "legend_bold": True},
        {"type": "text", "x": 0.95, "y": 0.05, "legend": "MODEL-1", "text_anchor": "end", "width_mm": 20},
        {"type": "text", "x": 0.5, "y": 0.95, "legend": "petit texte", "detail_only": True},
    ]
    for index, icon in enumerate(ICONS):
        components.append({
            "type": "button", "icon": icon,
            "x": (index + 1) / (len(ICONS) + 1), "y": 0.7, "width_mm": 6, "height_mm": 5,
        })
    return components


@pytest.fixture
def full_device():
    return make_device(components=all_components(), ports=[port("midi-out", "output"), port("audio-out", "output", "audio")])


@pytest.fixture(params=THEME_PATHS, ids=lambda p: p.stem)
def theme(request):
    return Theme(**json.loads(request.param.read_text(encoding="utf-8")))


@pytest.fixture
def write_json(tmp_path):
    def write(name, data):
        path = tmp_path / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path
    return write
