"""Tests de rendu « smoke » : le SVG est produit et bien formé, sans figer le design."""
import json
import xml.etree.ElementTree as ET

import pytest
import svgwrite

from renderer.device import draw_device_to_group, render_svg
from renderer.device.icons import ICONS, add_control_icon
from renderer.models import DeviceLayout, Theme
from renderer.scene import render_scene_svg
from tests.conftest import DEVICE_PATHS, ROOT, port

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
        return sum(1 for element in group.elements
                   if element.elementname == "text" and element.attribs.get("class") != "printed-text")

    assert text_count(False) == 0
    assert text_count(True) > 0


def test_printed_text_always_visible_and_stretched(full_device, theme):
    group = svgwrite.Drawing().g()
    draw_device_to_group(group, full_device, theme, show_labels=False)
    printed = {e.text: e for e in group.elements if e.attribs.get("class") == "printed-text"}
    assert set(printed) == {"Acme", "MODEL-1"}, "detail_only absent hors --detail"
    detailed = svgwrite.Drawing().g()
    draw_device_to_group(detailed, full_device, theme, show_labels=True)
    assert "petit texte" in {e.text for e in detailed.elements if e.attribs.get("class") == "printed-text"}
    assert printed["Acme"]["text-anchor"] == "start" and printed["Acme"]["font-weight"] == 700
    assert printed["MODEL-1"]["textLength"] == 20


def test_stroke_icon_width_in_view_box_units():
    from renderer.device.icons import draw_custom_icon
    dwg = svgwrite.Drawing()
    draw_custom_icon(dwg, "M0 0H100", (0, 0, 100, 50), 10, 10, 20, 10, "#fff", mode="stroke", stroke_width_view=8)
    draw_custom_icon(dwg, "M0 0H100", (0, 0, 100, 50), 10, 10, 20, 10, "#fff", mode="stroke")
    explicit, default = dwg.elements[1:]
    assert explicit["stroke-width"] == 8                 # unités du tracé, mises à l'échelle avec lui
    assert abs(default["stroke-width"] * 0.2 - 0.6) < 1e-9  # 6 % de 10 mm = 0.6 mm une fois l'échelle (0.2) appliquée


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
    _, _, width, height = (float(v) for v in root.get("viewBox").split())
    # Au moins : 2 appareils de 100 mm + 20 mm d'écart + 2 × 10 mm de marge ; les câbles peuvent agrandir la scène.
    assert width >= 240 and height >= 70
    cables = [g for g in root.iter(f"{SVG}g") if "cable" in (g.get("class") or "").split()]
    assert len(cables) == 2
    strokes = {g.get("class"): g.find(f"{SVG}path").get("stroke") for g in cables}
    assert strokes == {"cable cable-midi": theme.cables.colors.midi, "cable cable-audio": theme.cables.colors.audio}


def test_project_scene_renders_from_any_directory(tmp_path, monkeypatch):
    """Les chemins `device` sont relatifs au fichier de scène, pas au dossier courant."""
    monkeypatch.chdir(tmp_path)
    theme = Theme(**json.loads((ROOT / "themes" / "flat.json").read_text(encoding="utf-8")))

    def texts(show_labels):
        out = tmp_path / f"scene-{show_labels}.svg"
        render_scene_svg(str(ROOT / "scenes" / "nays_2026.json"), str(out), theme, show_labels=show_labels)
        return len(list(parse(out).iter(f"{SVG}text")))

    assert texts(True) > texts(False), "--detail ajoute légendes, ports et noms de câbles aux inscriptions imprimées"


def test_legend_always_is_visible_without_detail(theme):
    from tests.conftest import make_device
    device = make_device(components=[
        {"type": "frame", "x": 0.5, "y": 0.5, "width_mm": 50, "height_mm": 20, "legend": "Nom", "legend_always": True},
        {"type": "button", "x": 0.2, "y": 0.2, "width_mm": 8, "height_mm": 5, "legend": "FUNC"},
    ])
    group = svgwrite.Drawing().g()
    draw_device_to_group(group, device, theme, show_labels=False)
    assert [e.text for e in group.elements if e.elementname == "text"] == ["Nom"]


def test_scene_has_transparent_background(tmp_path, write_json, theme):
    device_path = write_json("box.json", {"manufacturer": "Acme", "model": "Box", "physical": {"width_mm": 50, "height_mm": 30}})
    scene_path = write_json("scene.json", {
        "name": "T", "devices": [{"id": "a", "device": "box.json", "position": {"type": "absolute", "x": 0, "y": 0}}],
    })
    out = tmp_path / "scene.svg"
    render_scene_svg(str(scene_path), str(out), theme)
    root = parse(out)
    assert root.find(f"{SVG}rect") is None, "aucun rectangle de fond à la racine du SVG"


def test_missing_scene_device_raises(tmp_path, write_json, theme):
    scene_path = write_json("scene.json", {
        "name": "T", "devices": [{"id": "a", "device": "absent.json", "position": {"type": "absolute", "x": 0, "y": 0}}],
    })
    with pytest.raises(ValueError, match="Layout introuvable"):
        render_scene_svg(str(scene_path), str(tmp_path / "out.svg"), theme)


def test_ports_drawn_only_in_detail(full_device, theme):
    def count(show_labels, css_class):
        group = svgwrite.Drawing().g()
        draw_device_to_group(group, full_device, theme, show_labels=show_labels)
        return sum(1 for e in group.elements if css_class in (e.attribs.get("class") or ""))

    assert count(False, "port") == 0
    assert count(True, "port-label") == len(full_device.ports)


def test_cable_labels_in_detail(tmp_path, write_json, theme):
    device = {"manufacturer": "Acme", "model": "Box", "physical": {"width_mm": 100, "height_mm": 50},
              "ports": [port("out", "output", y=0.0), port("in", "input", y=0.0)]}
    write_json("box.json", device)
    scene_path = write_json("scene.json", {
        "name": "T",
        "devices": [{"id": "a", "device": "box.json", "position": {"type": "absolute", "x": 0, "y": 0}},
                    {"id": "b", "device": "box.json", "position": {"type": "relative", "target": "a", "spacing_mm": 30}}],
        "connections": [{"source": {"device_id": "a", "port_id": "out"}, "target": {"device_id": "b", "port_id": "in"},
                         "label": "Sync"}],
    })

    def labels(show_labels):
        out = tmp_path / f"s-{show_labels}.svg"
        render_scene_svg(str(scene_path), str(out), theme, show_labels=show_labels)
        return [t for t in parse(out).iter(f"{SVG}text") if t.get("class") == "cable-label"]

    assert labels(False) == []
    detail = labels(True)
    assert [t.text for t in detail] == ["Sync"]
    assert detail[0].get("fill") == theme.cables.colors.midi


def test_empty_scene_raises(tmp_path, write_json, theme):
    scene_path = write_json("scene.json", {"name": "Vide"})
    with pytest.raises(ValueError, match="aucun appareil"):
        render_scene_svg(str(scene_path), str(tmp_path / "out.svg"), theme)


def test_png_export_is_transparent_and_sized_by_dpi(tmp_path, full_device, theme):
    import struct
    from renderer.export import svg_to_png
    svg = tmp_path / "device.svg"
    render_svg(full_device, theme, str(svg))
    png = svg_to_png(svg, tmp_path / "device.png", dpi=254)   # 254 dpi = 10 px/mm
    data = png.read_bytes()
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (1000, 500)        # appareil de 100 × 50 mm
    assert data[25] == 6, "PNG RGBA (canal alpha pour la transparence)"


def test_legend_spans_mix_weights_and_keep_spaces(theme):
    from tests.conftest import make_device
    device = make_device(components=[{
        "type": "frame", "x": 0.5, "y": 0.5, "width_mm": 60, "height_mm": 30, "legend_always": True,
        "font_family": "Arial", "legend_spans": [{"text": "Digitakt", "weight": 700},
                                                 {"text": " II", "weight": 200, "font_family": "Segoe UI"}],
    }])
    assert device.components[0].legend == "Digitakt II"
    group = svgwrite.Drawing().g()
    draw_device_to_group(group, device, theme, show_labels=False)
    text = next(e for e in group.elements if e.elementname == "text")
    assert text["xml:space"] == "preserve"
    assert text["font-family"] == "Arial"
    spans = [(s.text, s["font-weight"], s.attribs.get("font-family")) for s in text.elements]
    thin = max(200, theme.labels.min_font_weight or 0)   # un thème d'impression peut imposer une graisse minimale
    assert spans == [("Digitakt", 700, None), (" II", thin, "Segoe UI")]


def test_icon_path_list_draws_each_path_as_is():
    from renderer.device.icons import draw_custom_icon
    paths = ["m0 0 10 0 0 10z", "m20 0 10 0 0 10z"]   # « m » initial + paires relatives implicites
    dwg = svgwrite.Drawing()
    draw_custom_icon(dwg, paths, (0, 0, 30, 10), 15, 5, 30, 10, "#fff")
    assert [e.commands for e in dwg.elements[1:]] == [[d] for d in paths]


def test_stroke_icon_linecap():
    from renderer.device.icons import draw_custom_icon
    dwg = svgwrite.Drawing()
    draw_custom_icon(dwg, "M0 0H10", (0, 0, 10, 10), 5, 5, 10, 10, "#fff", mode="stroke", stroke_width_view=1, linecap="butt")
    assert dwg.elements[1]["stroke-linecap"] == "butt"


def test_min_font_weight_thickens_thin_spans(theme):
    from tests.conftest import make_device
    device = make_device(components=[{
        "type": "text", "x": 0.5, "y": 0.5,
        "legend_spans": [{"text": "Octatrack", "weight": 700}, {"text": " MKII", "weight": 200}],
    }])
    thick = theme.copy(update={"labels": theme.labels.copy(update={"min_font_weight": 400})})
    group = svgwrite.Drawing().g()
    draw_device_to_group(group, device, thick)
    spans = next(e for e in group.elements if e.elementname == "text").elements
    assert [s["font-weight"] for s in spans] == [700, 400]


def test_theme_variant_hides_and_overrides_components():
    from renderer.device.draw import for_variant
    from tests.conftest import make_device
    device = make_device(components=[
        {"type": "text", "x": 0.2, "y": 0.5, "legend": "A", "variants": {"print": {"hidden": True}}},
        {"type": "text", "x": 0.5, "y": 0.5, "legend": "B", "variants": {"print": {"x": 0.1, "legend_font_size_mm": 7}}},
    ])
    hidden, moved = device.components
    assert for_variant(hidden, "screen") is hidden
    assert for_variant(hidden, "print") is None
    printed = for_variant(moved, "print")
    assert (printed.x, printed.legend_font_size_mm, moved.x) == (0.1, 7, 0.5)
