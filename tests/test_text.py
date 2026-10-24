import json
import xml.etree.ElementTree as ET

import pytest

from renderer.models.text import TextBlock, parse_markup
from renderer.text import layout_text_block, render_text_svg
from tests.conftest import ROOT

SVG = "{http://www.w3.org/2000/svg}"


def test_markup_bold_and_regular_runs():
    runs = parse_markup("**NAYS** LIVE **SETUP**!")
    assert [(r.text, r.bold) for r in runs] == [("NAYS", True), (" LIVE ", False), ("SETUP", True), ("!", False)]


def test_lines_accept_plain_strings():
    block = TextBlock(lines=["**A** b", {"text": "c", "size_mm": 4}])
    assert block.lines[0].text == "**A** b" and block.lines[1].size_mm == 4


@pytest.mark.parametrize("align", ["left", "center", "right"])
def test_alignment_is_exact(align):
    block = TextBlock(lines=["**NAYS** LIVE SETUP", "short"], align=align, letter_spacing_em=0.3, size_mm=10)
    layout = layout_text_block(block)
    x0, _, x1, _ = layout.bbox
    if align == "center":
        assert abs(x0 + x1) < 0.2            # centré au dixième de mm, malgré l'espacement des lettres
    elif align == "left":
        assert abs(x0) < 0.2
    else:
        assert abs(x1) < 0.2


def test_long_text_is_not_clipped():
    block = TextBlock(lines=["W" * 6], size_mm=20, letter_spacing_em=2.0)   # bien plus large que l'estimation
    x0, _, x1, _ = layout_text_block(block).bbox
    assert x1 - x0 > 6 * 20 * 2.0 * 0.8


def test_render_text_svg_mixes_weights_and_crops(tmp_path):
    out = render_text_svg(TextBlock(lines=["**NAYS** LIVE"], size_mm=10), tmp_path / "t.svg")
    root = ET.parse(out).getroot()
    weights = [span.get("font-weight") for span in root.iter(f"{SVG}tspan")]
    assert weights == ["700", "200"]
    width_mm = float(root.get("width").removesuffix("mm"))
    assert 30 < width_mm < 120                     # recadré sur le texte, pas un grand canevas


def test_scene_title_sits_above_the_scene(tmp_path, write_json, theme):
    from renderer.scene import render_scene_svg
    write_json("box.json", {"manufacturer": "Acme", "model": "Box", "physical": {"width_mm": 100, "height_mm": 50}})
    scene_path = write_json("scene.json", {
        "name": "T", "devices": [{"id": "a", "device": "box.json", "position": {"type": "absolute", "x": 0, "y": 0}}],
        "title": {"lines": ["**TITRE**"], "size_mm": 10}, "title_gap_mm": 15,
    })
    out = tmp_path / "s.svg"
    render_scene_svg(str(scene_path), str(out), theme, padding_mm=10)
    root = ET.parse(out).getroot()
    _, _, _, height = (float(v) for v in root.get("viewBox").split())
    assert height > 50 + 15 + 7 + 2 * 10 - 1        # machine + écart + capitales du titre + marges
    assert root.find(f".//{SVG}g[@class='text-block']") is not None


def test_project_text_files_are_valid():
    for path in sorted((ROOT / "texts").glob("*.json")):
        TextBlock(**json.loads(path.read_text(encoding="utf-8")))
