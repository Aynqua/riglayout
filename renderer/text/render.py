"""Dessin et mesure des blocs de texte.

Chaque ligne est mesurée sur son rendu réel (resvg) : l'alignement (centre, gauche, droite) et le recadrage sont
donc exacts quels que soient la police, l'espacement des lettres ou les graisses, sans table de métriques.
"""
import io
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple, Union

import svgwrite
from svgwrite.container import Group
from svgwrite.text import TSpan, Text

from renderer.models.theme import Theme
from renderer.device.legends import label_color
from renderer.models.text import TextBlock, TextLine, parse_markup

CAP_HEIGHT_EM = 0.72          # hauteur des capitales (Helvetica / Arial) : sert à espacer les lignes
MEASURE_PX_PER_EM = 120     # précision de mesure : ~1 % de la taille de police
_ANCHOR = {"left": "start", "center": "middle", "right": "end"}

# (x0, y0, x1, y1) en mm
BBox = Tuple[float, float, float, float]


class BlockLayout(NamedTuple):
    """Placement mesuré : décalage horizontal et ligne de base de chaque ligne, boîte encrée du bloc.
    Tout est relatif à l'origine du bloc (point d'alignement, haut des capitales de la 1re ligne)."""
    x_offsets: List[float]
    baselines: List[float]
    bbox: BBox


def _line_text(line: TextLine, block: TextBlock, x: float, baseline: float, color: str) -> Text:
    size = line.size_mm or block.size_mm
    spacing = (block.letter_spacing_em if line.letter_spacing_em is None else line.letter_spacing_em) * size
    text = Text("", insert=(x, baseline), text_anchor=_ANCHOR[block.align],
                font_family=line.font_family or block.font_family, font_size=size,
                fill=line.color or color, letter_spacing=spacing)
    text.attribs["xml:space"] = "preserve"
    for run in parse_markup(line.text):
        weight = (line.bold_weight or block.bold_weight) if run.bold else (line.regular_weight or block.regular_weight)
        text.add(TSpan(run.text.upper() if block.uppercase else run.text, font_weight=weight))
    return text


def _ink_box(elements, half_width: float, height: float, dpi: float) -> Optional[BBox]:
    """Boîte encrée (mm) d'éléments placés dans un canevas [-half_width, half_width] × [-height, height]."""
    import numpy as np
    import resvg_py
    from PIL import Image

    dwg = svgwrite.Drawing(size=(f"{2 * half_width}mm", f"{2 * height}mm"),
                           viewBox=f"{-half_width} {-height} {2 * half_width} {2 * height}")
    for element in elements:
        dwg.add(element)
    png = bytes(resvg_py.svg_to_bytes(svg_string=dwg.tostring(), dpi=dpi))
    alpha = np.asarray(Image.open(io.BytesIO(png)).getchannel("A")) > 0
    rows, cols = np.nonzero(alpha)
    if not len(rows):
        return None
    px = dpi / 25.4
    return (float(cols.min() / px - half_width), float(rows.min() / px - height),
            float((cols.max() + 1) / px - half_width), float((rows.max() + 1) / px - height))


def layout_text_block(block: TextBlock) -> BlockLayout:
    x_offsets, baselines, boxes = [], [], []
    baseline = 0.0
    for index, line in enumerate(block.lines):
        size = line.size_mm or block.size_mm
        if index:
            baseline += block.line_gap_em * size
        baseline += CAP_HEIGHT_EM * size

        spacing_em = block.letter_spacing_em if line.letter_spacing_em is None else line.letter_spacing_em
        half_width = len(line.text) * size * (0.9 + abs(spacing_em)) / 2 + size   # assez large même centré
        dpi = MEASURE_PX_PER_EM / size * 25.4
        box = _ink_box([_line_text(line, block, 0.0, 0.0, "#000")], half_width, size * 2, dpi)
        while box is not None and (box[0] <= -half_width + 1e-3 or box[2] >= half_width - 1e-3):
            half_width *= 2                                   # le texte touche le bord : canevas trop étroit
            box = _ink_box([_line_text(line, block, 0.0, 0.0, "#000")], half_width, size * 2, dpi)
        if box is None:
            raise ValueError(f"La ligne « {line.text} » n'a rien produit (police introuvable ?)")
        x0, y0, x1, y1 = box
        offset = {"left": -x0, "center": -(x0 + x1) / 2, "right": -x1}[block.align]
        x_offsets.append(offset)
        baselines.append(baseline)
        boxes.append((x0 + offset, y0 + baseline, x1 + offset, y1 + baseline))
    bbox = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    return BlockLayout(x_offsets, baselines, bbox)


def draw_text_block(container, block: TextBlock, origin: Tuple[float, float], theme: Optional[Theme] = None,
                    layout: Optional[BlockLayout] = None) -> BlockLayout:
    """Ajoute le bloc à `container` à `origin` (point d'alignement, haut des capitales de la 1re ligne)."""
    layout = layout or layout_text_block(block)
    color = block.color or (label_color(theme) if theme else "#ffffff")
    group = Group(class_="text-block")
    x, top = origin
    for line, offset, baseline in zip(block.lines, layout.x_offsets, layout.baselines):
        group.add(_line_text(line, block, x + offset, top + baseline, color))
    container.add(group)
    return layout


def render_text_svg(block: TextBlock, output_path: Union[str, Path], theme: Optional[Theme] = None,
                    padding_mm: float = 2.0) -> Path:
    """SVG autonome recadré au plus juste sur le texte (+ marge), fond transparent."""
    layout = layout_text_block(block)
    x0, y0, x1, y1 = layout.bbox
    width, height = x1 - x0 + 2 * padding_mm, y1 - y0 + 2 * padding_mm
    dwg = svgwrite.Drawing(str(output_path), size=(f"{width:.2f}mm", f"{height:.2f}mm"),
                           viewBox=f"{x0 - padding_mm:.3f} {y0 - padding_mm:.3f} {width:.3f} {height:.3f}")
    draw_text_block(dwg, block, (0.0, 0.0), theme, layout)
    dwg.save()
    return Path(output_path)
