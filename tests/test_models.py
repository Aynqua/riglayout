import json

import pytest
from pydantic import ValidationError

from renderer.models import DeviceLayout, Theme
from tests.conftest import DEVICE_PATHS, THEME_PATHS, make_device, port


def test_components_and_ports_default_to_empty():
    device = DeviceLayout(manufacturer="Acme", model="X", physical={"width_mm": 10, "height_mm": 10})
    assert device.components == []
    assert device.ports == []


def test_unknown_fields_are_ignored():
    device = DeviceLayout(manufacturer="Acme", model="X", name="Nom libre", physical={"width_mm": 10, "height_mm": 10})
    assert device.model == "X"


@pytest.mark.parametrize("physical", [{"width_mm": 0, "height_mm": 10}, {"width_mm": 10, "height_mm": -1}])
def test_physical_dimensions_must_be_positive(physical):
    with pytest.raises(ValidationError):
        DeviceLayout(manufacturer="Acme", model="X", physical=physical)


def test_component_position_must_be_normalized():
    with pytest.raises(ValidationError):
        make_device(components=[{"type": "led", "x": 1.2, "y": 0.5, "diameter_mm": 2}])


def test_component_type_selects_model():
    device = make_device(components=[
        {"type": "encoder", "x": 0.5, "y": 0.5, "diameter_mm": 8},
        {"type": "button", "x": 0.5, "y": 0.5, "width_mm": 5, "height_mm": 5},
    ])
    assert [type(c).__name__ for c in device.components] == ["EncoderComponent", "ButtonComponent"]


def test_custom_icon_requires_path_and_view_box_together():
    with pytest.raises(ValidationError, match="ensemble"):
        make_device(components=[{"type": "button", "x": 0.5, "y": 0.5, "width_mm": 5, "height_mm": 5, "icon_path_d": "M0 0Z"}])


def test_custom_icon_view_box_must_be_positive():
    with pytest.raises(ValidationError, match="positives"):
        make_device(components=[{
            "type": "button", "x": 0.5, "y": 0.5, "width_mm": 5, "height_mm": 5,
            "icon_path_d": "M0 0Z", "icon_view_box": [0, 0, 0, 10],
        }])


def test_logo_requires_icon_path():
    with pytest.raises(ValidationError):
        make_device(components=[{"type": "logo", "x": 0.5, "y": 0.5, "width_mm": 5, "height_mm": 5}])


def test_port_defaults():
    device = make_device(ports=[port("midi-in", "input")])
    assert (device.ports[0].x, device.ports[0].y) == (0.5, 1.0)
    assert device.ports[0].capabilities == []


@pytest.mark.parametrize("field, value", [("direction", "sideways"), ("signal", "cv")])
def test_port_enums_are_closed(field, value):
    with pytest.raises(ValidationError):
        make_device(ports=[{**port("p", "input"), field: value}])


@pytest.mark.parametrize("path", DEVICE_PATHS, ids=lambda p: p.stem)
def test_project_devices_are_valid(path):
    DeviceLayout(**json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("path", THEME_PATHS, ids=lambda p: p.stem)
def test_project_themes_are_valid(path):
    Theme(**json.loads(path.read_text(encoding="utf-8")))
