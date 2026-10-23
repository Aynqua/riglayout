import pytest

from renderer.models import Scene
from renderer.scene.layout import compute_bounds, resolve_positions
from tests.conftest import make_device


def build(devices):
    """devices : liste de (id, position, (largeur, hauteur))."""
    scene = Scene(name="Test", devices=[{"id": i, "device": "unused.json", "position": pos} for i, pos, _ in devices])
    layouts = {i: make_device(width_mm=w, height_mm=h) for i, _, (w, h) in devices}
    return scene, layouts


def absolute(x, y):
    return {"type": "absolute", "x": x, "y": y}


def relative(target, anchor, spacing=10):
    return {"type": "relative", "target": target, "anchor": anchor, "spacing_mm": spacing}


def test_absolute_position():
    scene, layouts = build([("a", absolute(5, -20), (100, 50))])
    assert resolve_positions(scene, layouts) == {"a": (5, -20, 100, 50)}


@pytest.mark.parametrize("anchor, expected", [
    ("right", (110, 0)),
    ("left", (-40, 0)),     # 0 - largeur(30) - 10
    ("bottom", (0, 60)),
    ("top", (0, -30)),      # 0 - hauteur(20) - 10
])
def test_relative_anchors(anchor, expected):
    scene, layouts = build([("a", absolute(0, 0), (100, 50)), ("b", relative("a", anchor), (30, 20))])
    assert resolve_positions(scene, layouts)["b"][:2] == expected


def test_relative_default_spacing_and_anchor():
    scene, layouts = build([("a", absolute(0, 0), (100, 50)), ("b", {"type": "relative", "target": "a"}, (30, 20))])
    assert resolve_positions(scene, layouts)["b"][:2] == (115, 0)


def test_relative_chain_is_order_independent():
    scene, layouts = build([
        ("c", relative("b", "right"), (10, 10)),
        ("b", relative("a", "right"), (10, 10)),
        ("a", absolute(0, 0), (10, 10)),
    ])
    rects = resolve_positions(scene, layouts)
    assert rects["b"][0] == 20
    assert rects["c"][0] == 40


@pytest.mark.parametrize("devices", [
    [("a", relative("b", "right"), (10, 10)), ("b", relative("a", "right"), (10, 10))],
    [("a", relative("ghost", "right"), (10, 10))],
], ids=["circular", "unknown-target"])
def test_unresolvable_positions(devices):
    scene, layouts = build(devices)
    with pytest.raises(ValueError, match="dépendance circulaire"):
        resolve_positions(scene, layouts)


def test_bounds_include_padding_and_shift_negative_coordinates():
    bounds = compute_bounds({"a": (0, 0, 100, 50), "b": (-20, -30, 10, 10)}, padding_mm=5)
    assert bounds.width_mm == 120 + 10
    assert bounds.height_mm == 80 + 10
    assert (bounds.offset_x, bounds.offset_y) == (25, 35)
