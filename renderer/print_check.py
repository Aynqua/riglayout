"""Mode impression : taille finale d'un SVG imprimé à une largeur donnée, et contrôle des traits et textes trop fins."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple, Union

from renderer.export import DEFAULT_DPI

# Seuils courants des imprimeurs textile (DTF / DTG) ; à ajuster selon la fiche technique de l'atelier.
MIN_LINE_MM = 0.5
MIN_TEXT_MM = 2.1   # taille de police ≈ 6 pt
MIN_GAP_MM = 0.5    # espace minimal entre deux traits, une fois imprimé
MIN_AREA_PIXELS = 40   # en dessous (à 300 dpi), une « zone fine » n'est qu'un bord de forme

_SCALE = re.compile(r"scale\(\s*([-+\d.eE]+)(?:[\s,]+([-+\d.eE]+))?\s*\)")
_MM = re.compile(r"^\s*([\d.]+)\s*mm\s*$")


class PrintReport(NamedTuple):
    print_width_mm: float
    print_height_mm: float
    scale: float                 # taille imprimée / taille du SVG
    dpi: float                   # résolution à demander au rendu PNG pour obtenir DEFAULT_DPI à la taille imprimée
    pixels: Tuple[int, int]
    thinnest_line_mm: float
    smallest_text_mm: float
    thin_lines: int              # traits sous MIN_LINE_MM une fois imprimés
    small_texts: int             # textes sous MIN_TEXT_MM une fois imprimés


def svg_size_mm(svg_path: Union[str, Path]) -> Tuple[float, float]:
    root = ET.parse(svg_path).getroot()
    sizes = [_MM.match(root.get(attribute) or "") for attribute in ("width", "height")]
    if not all(sizes):
        raise ValueError(f"{svg_path} : largeur/hauteur en mm introuvables")
    return float(sizes[0].group(1)), float(sizes[1].group(1))


def _local_scale(element) -> float:
    match = _SCALE.search(element.get("transform") or "")
    if not match:
        return 1.0
    sx = float(match.group(1))
    sy = float(match.group(2)) if match.group(2) else sx
    return min(abs(sx), abs(sy))


def _measure(element, scale: float, inherited_font: float, lines: List[float], texts: List[float]):
    scale *= _local_scale(element)
    tag = element.tag.rsplit("}", 1)[-1]

    stroke = element.get("stroke")
    width = element.get("stroke-width")
    if stroke and stroke != "none" and width and float(width) > 0:
        lines.append(float(width) * scale)

    font = float(element.get("font-size")) if element.get("font-size") else inherited_font
    if tag in ("text", "tspan") and font and (element.text or "").strip():
        texts.append(font * scale)

    for child in element:
        _measure(child, scale, font, lines, texts)


def analyse_print(svg_path: Union[str, Path], print_width_mm: float) -> PrintReport:
    """Mesure traits et textes du SVG tels qu'ils seront une fois imprimés à `print_width_mm` de large."""
    width_mm, height_mm = svg_size_mm(svg_path)
    factor = print_width_mm / width_mm
    lines: List[float] = []
    texts: List[float] = []
    _measure(ET.parse(svg_path).getroot(), 1.0, 0.0, lines, texts)
    lines = [value * factor for value in lines]
    texts = [value * factor for value in texts]
    print_height_mm = height_mm * factor
    return PrintReport(
        print_width_mm=print_width_mm,
        print_height_mm=print_height_mm,
        scale=factor,
        dpi=DEFAULT_DPI * factor,
        pixels=(round(print_width_mm / 25.4 * DEFAULT_DPI), round(print_height_mm / 25.4 * DEFAULT_DPI)),
        thinnest_line_mm=min(lines, default=0.0),
        smallest_text_mm=min(texts, default=0.0),
        thin_lines=sum(1 for value in lines if value < MIN_LINE_MM),
        small_texts=sum(1 for value in texts if value < MIN_TEXT_MM),
    )


# --- Zones trop fines dans l'image finale (formes pleines : logos, pictogrammes) -------------------------------

class ThinArea(NamedTuple):
    x_cm: float          # coin haut-gauche, depuis le coin haut-gauche de l'impression
    y_cm: float
    width_mm: float
    height_mm: float
    pixels: int


class ThinReport(NamedTuple):
    thin_pixels: int
    areas: List[ThinArea]
    preview_path: Optional[Path]


def _without_text(svg_path: Union[str, Path]) -> bytes:
    """Le SVG sans ses textes : ils suivent la règle de taille de police, pas celle d'épaisseur de trait."""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    for parent in tree.getroot().iter():
        for child in list(parent):
            if child.tag.rsplit("}", 1)[-1] == "text":
                parent.remove(child)
    return ET.tostring(tree.getroot())


def _disk_offsets(radius: float):
    r = int(radius)
    return [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dx * dx + dy * dy <= radius * radius]


def _shift(mask, dy: int, dx: int, fill: bool):
    import numpy as np
    out = np.full_like(mask, fill)
    h, w = mask.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = mask[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def _ink_mask(svg_path: Union[str, Path], print_width_mm: float, dpi: float, keep_text: bool):
    """Masque booléen de l'encre à la taille imprimée."""
    import io
    import tempfile
    import numpy as np
    import resvg_py
    from PIL import Image

    width_mm, _ = svg_size_mm(svg_path)
    source = ET.tostring(ET.parse(svg_path).getroot()) if keep_text else _without_text(svg_path)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as handle:
        handle.write(source)
        temporary = handle.name
    try:
        png = bytes(resvg_py.svg_to_bytes(svg_path=temporary, dpi=dpi * print_width_mm / width_mm))
    finally:
        Path(temporary).unlink(missing_ok=True)
    Image.MAX_IMAGE_PIXELS = None
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGBA").getchannel("A")) >= 128


def _erode(mask, offsets):
    import numpy as np
    out = np.ones_like(mask)
    for dy, dx in offsets:
        out &= _shift(mask, dy, dx, False)
    return out


def _dilate(mask, offsets):
    import numpy as np
    out = np.zeros_like(mask)
    for dy, dx in offsets:
        out |= _shift(mask, dy, dx, False)
    return out


def _areas(flagged, dpi: float) -> List[ThinArea]:
    """Regroupe les pixels signalés en zones (cellules de 2 mm adjacentes) ; ignore les zones minuscules."""
    import numpy as np
    px_per_mm = dpi / 25.4
    cell = max(int(2 * px_per_mm), 1)
    h, w = flagged.shape
    grid_h, grid_w = -(-h // cell), -(-w // cell)
    padded = np.zeros((grid_h * cell, grid_w * cell), dtype=bool)
    padded[:h, :w] = flagged
    counts = padded.reshape(grid_h, cell, grid_w, cell).sum(axis=(1, 3))
    MIN_PIXELS = 4                                  # par cellule : ignore les pixels isolés d'anticrénelage
    seen = np.zeros_like(counts, dtype=bool)
    areas: List[ThinArea] = []
    for gy, gx in zip(*np.nonzero(counts >= MIN_PIXELS)):
        if seen[gy, gx]:
            continue
        stack, cells = [(gy, gx)], []
        seen[gy, gx] = True
        while stack:
            cy, cx = stack.pop(); cells.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < grid_h and 0 <= nx < grid_w and not seen[ny, nx] and counts[ny, nx] >= MIN_PIXELS:
                    seen[ny, nx] = True; stack.append((ny, nx))
        ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys) * cell, (max(ys) + 1) * cell, min(xs) * cell, (max(xs) + 1) * cell
        areas.append(ThinArea(float(round(x0 / px_per_mm / 10, 1)), float(round(y0 / px_per_mm / 10, 1)),
                              float(round((x1 - x0) / px_per_mm, 1)), float(round((y1 - y0) / px_per_mm, 1)),
                              int(counts[ys, xs].sum())))
    areas = [a for a in areas if a.pixels >= MIN_AREA_PIXELS]   # bords de formes : quelques pixels sans conséquence
    areas.sort(key=lambda a: a.pixels, reverse=True)
    return areas


def _preview(ink, flagged, path, color):
    import numpy as np
    from PIL import Image
    picture = np.zeros(ink.shape + (3,), dtype=np.uint8)
    picture[ink] = (110, 110, 110)
    picture[flagged] = color
    image = Image.fromarray(picture)
    image.thumbnail((1600, 1600))
    image.save(path)
    return Path(path)


def find_thin_areas(
    svg_path: Union[str, Path], print_width_mm: float, min_mm: float = MIN_LINE_MM,
    preview_path: Optional[Union[str, Path]] = None, dpi: float = DEFAULT_DPI,
) -> ThinReport:
    """Rasterise le SVG (sans textes) à la taille imprimée et repère l'encre où un disque de `min_mm` ne tient pas :
    ce sont les parties qui risquent de ne pas s'imprimer (ex. lignes d'un logo trop petit)."""
    ink = _ink_mask(svg_path, print_width_mm, dpi, keep_text=False)
    offsets = _disk_offsets((min_mm / 25.4 * dpi) / 2)
    thin = ink & ~_dilate(_erode(ink, offsets), offsets)          # ouverture : ce qui disparaît est trop fin
    areas = _areas(thin, dpi)
    written = _preview(ink, thin, preview_path, (255, 40, 40)) if preview_path and areas else None
    return ThinReport(int(thin.sum()), areas, written)


def find_narrow_gaps(
    svg_path: Union[str, Path], print_width_mm: float, min_mm: float = MIN_GAP_MM, keep_text: bool = False,
    preview_path: Optional[Union[str, Path]] = None, dpi: float = DEFAULT_DPI,
) -> ThinReport:
    """Repère les espaces vides plus étroits que `min_mm` entre deux zones d'encre : à l'impression, l'encre
    s'étale et ces espaces risquent de se boucher (traits qui se confondent)."""
    ink = _ink_mask(svg_path, print_width_mm, dpi, keep_text=keep_text)
    offsets = _disk_offsets((min_mm / 25.4 * dpi) / 2)
    narrow = _erode(_dilate(ink, offsets), offsets) & ~ink        # fermeture : ce qui se bouche est trop étroit
    areas = _areas(narrow, dpi)
    written = _preview(ink, narrow, preview_path, (60, 160, 255)) if preview_path and areas else None
    return ThinReport(int(narrow.sum()), areas, written)
