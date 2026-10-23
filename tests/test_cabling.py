"""Câblage de scène : propriétés vérifiées sur des scènes de test (pas de rendu figé)."""
import json
from itertools import combinations

import pytest

from renderer.models import DevicePort, Scene, Theme
from renderer.models.theme import CableStyle
from renderer.scene.cabling import route_cables
from renderer.scene.cabling.anchors import port_side
from renderer.scene.cabling.geometry import DOWN, EPS, LEFT, RIGHT, UP, Box, is_horizontal, segment_crosses_box
from renderer.scene.layout import check_no_overlap, resolve_positions
from renderer.scene.render import load_scene, load_scene_layouts
from renderer.scene.validation import validate_scene_connections
from tests.conftest import ROOT, make_device, port

STYLE = CableStyle()


# --- Construction de scènes de test -----------------------------------------

def device(ports, width=100.0, height=50.0):
    return make_device(ports=ports, width_mm=width, height_mm=height)


def scene_of(placements, connections):
    """placements : {id: (x, y)} en mm ; connections : [(dev, port, dev, port)]."""
    return Scene(
        name="Test",
        devices=[{"id": i, "device": "unused.json", "position": {"type": "absolute", "x": x, "y": y}}
                 for i, (x, y) in placements.items()],
        connections=[{"source": {"device_id": a, "port_id": pa}, "target": {"device_id": b, "port_id": pb}}
                     for a, pa, b, pb in connections],
    )


def route(scene, layouts, style=STYLE):
    validate_scene_connections(scene, layouts)
    rects = resolve_positions(scene, layouts)
    check_no_overlap(rects)
    return route_cables(scene, layouts, rects, style), rects


# --- Propriétés ----------------------------------------------------------------

def assert_cabling_is_realistic(routes, rects, layouts, style=STYLE):
    boxes = {i: Box.from_rect(r) for i, r in rects.items()}
    for cable in routes:
        points = cable.points
        segments = list(zip(points, points[1:]))
        for a, b in segments:
            assert is_horizontal(a, b) or abs(a[0] - b[0]) < EPS, f"segment non orthogonal {a}->{b}"
            for device_id, box in boxes.items():
                assert not segment_crosses_box(a, b, box), f"câble sur la machine {device_id}"

        # Départ et arrivée : sur le bord de la machine, perpendiculairement.
        for endpoint, (a, b) in ((cable.connection.source, segments[0]), (cable.connection.target, segments[-1][::-1])):
            p = next(p for p in layouts[endpoint.device_id].ports if p.id == endpoint.port_id)
            direction = port_side(p)
            assert ((b[0] - a[0]) * direction[0] + (b[1] - a[1]) * direction[1]) > 0, "le câble doit sortir perpendiculairement"

    # Deux câbles ne se superposent jamais : segments parallèles proches et recouvrants interdits.
    min_gap = style.spacing_mm - 1e-6
    for first, second in combinations(routes, 2):
        for a1, b1 in zip(first.points, first.points[1:]):
            for a2, b2 in zip(second.points, second.points[1:]):
                h1, h2 = is_horizontal(a1, b1), is_horizontal(a2, b2)
                if h1 != h2:
                    continue
                track1, track2 = (a1[1], a2[1]) if h1 else (a1[0], a2[0])
                along1 = sorted((a1[0], b1[0]) if h1 else (a1[1], b1[1]))
                along2 = sorted((a2[0], b2[0]) if h1 else (a2[1], b2[1]))
                overlap = min(along1[1], along2[1]) - max(along1[0], along2[0])
                assert not (overlap > EPS and abs(track1 - track2) < min_gap), (
                    f"câbles superposés : {first.connection.source.port_id} et {second.connection.source.port_id}"
                )


# --- Scénarios -------------------------------------------------------------------

def test_parallel_cables_get_separate_lanes():
    ports_out = [port(f"o{i}", "output", "audio", x=0.1 + i * 0.1, y=0.0) for i in range(5)]
    ports_in = [port(f"i{i}", "input", "audio", x=0.1 + i * 0.1, y=0.0) for i in range(5)]
    layouts = {"a": device(ports_out), "b": device(ports_in)}
    scene = scene_of({"a": (0, 0), "b": (150, 0)}, [("a", f"o{i}", "b", f"i{i}") for i in range(5)])
    routes, rects = route(scene, layouts)
    assert len(routes) == 5
    assert_cabling_is_realistic(routes, rects, layouts)


def test_cable_goes_around_a_machine_in_the_way():
    layouts = {
        "a": device([port("out", "output", x=0.9, y=0.5)]),
        "wall": device([], width=40, height=300),
        "b": device([port("in", "input", x=0.1, y=0.5)]),
    }
    scene = scene_of({"a": (0, 0), "wall": (130, -125), "b": (200, 0)}, [("a", "out", "b", "in")])
    routes, rects = route(scene, layouts)
    assert_cabling_is_realistic(routes, rects, layouts)
    ys = [y for _, y in routes[0].points]
    assert min(ys) < -125 or max(ys) > 175, "le câble doit contourner le mur"


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
def test_ports_on_every_side(side):
    position = {"top": (0.5, 0.0), "bottom": (0.5, 1.0), "left": (0.0, 0.5), "right": (1.0, 0.5)}[side]
    layouts = {
        "a": device([port("out", "output", x=position[0], y=position[1])]),
        "b": device([port("in", "input", x=1 - position[0], y=1 - position[1])]),
    }
    scene = scene_of({"a": (0, 0), "b": (60, 120)}, [("a", "out", "b", "in")])
    routes, rects = route(scene, layouts)
    assert_cabling_is_realistic(routes, rects, layouts)


@pytest.mark.parametrize("x, y, expected", [(0.3, 0.0, UP), (0.3, 1.0, DOWN), (0.0, 0.4, LEFT), (1.0, 0.4, RIGHT), (0.5, 0.1, UP)])
def test_port_side_detection(x, y, expected):
    assert port_side(DevicePort(**port("p", "input", x=x, y=y))) == expected


def test_project_scene_cabling(monkeypatch):
    monkeypatch.chdir(ROOT)
    scene = load_scene("scenes/nays_2026.json")
    layouts = load_scene_layouts(scene)
    routes, rects = route(scene, layouts)
    assert len(routes) == len(scene.connections)
    assert_cabling_is_realistic(routes, rects, layouts)


# --- Erreurs ---------------------------------------------------------------------

def test_overlapping_devices_raise():
    layouts = {"a": device([]), "b": device([])}
    with pytest.raises(ValueError, match="se superposent"):
        route(scene_of({"a": (0, 0), "b": (50, 10)}, []), layouts)


def test_touching_devices_are_allowed():
    layouts = {"a": device([]), "b": device([])}
    route(scene_of({"a": (0, 0), "b": (100, 0)}, []), layouts)


def test_port_used_twice_raises():
    layouts = {"a": device([port("out", "output", x=0.2, y=0)]),
               "b": device([port("in1", "input", x=0.2, y=0), port("in2", "input", x=0.4, y=0)])}
    scene = scene_of({"a": (0, 0), "b": (150, 0)}, [("a", "out", "b", "in1"), ("a", "out", "b", "in2")])
    with pytest.raises(ValueError, match="plusieurs câbles"):
        route(scene, layouts)


def test_ports_at_same_position_raise():
    layouts = {"a": device([port("o1", "output", x=0.2, y=0), port("o2", "output", x=0.2, y=0)]),
               "b": device([port("i1", "input", x=0.2, y=0), port("i2", "input", x=0.4, y=0)])}
    scene = scene_of({"a": (0, 0), "b": (150, 0)}, [("a", "o1", "b", "i1"), ("a", "o2", "b", "i2")])
    with pytest.raises(ValueError, match="même position"):
        route(scene, layouts)


def test_port_blocked_by_neighbour_raises():
    layouts = {"a": device([port("out", "output", x=1.0, y=0.5)]),
               "b": device([port("in", "input", x=0.5, y=0.0)])}
    scene = scene_of({"a": (0, 0), "b": (102, 0)}, [("a", "out", "b", "in")])
    with pytest.raises(ValueError, match="trop proche"):
        route(scene, layouts)


# --- Thème -----------------------------------------------------------------------

def test_theme_without_cables_uses_defaults():
    theme = Theme(name="t", background={}, components={})
    assert theme.cables.colors.midi == CableStyle().colors.midi


def test_partial_cable_colors_keep_other_defaults():
    style = CableStyle(colors={"audio": "#000000"})
    assert style.colors.audio == "#000000"
    assert style.colors.midi == CableStyle().colors.midi


def test_spacing_smaller_than_width_is_rejected():
    with pytest.raises(ValueError, match="spacing_mm"):
        CableStyle(width_mm=3, spacing_mm=2)


def test_project_themes_define_cables():
    for path in sorted((ROOT / "themes").glob("*.json")):
        assert "cables" in json.loads(path.read_text(encoding="utf-8")), path.name
