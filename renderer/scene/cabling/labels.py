"""Nom des câbles (mode détail) : placé le long du câble, là où il ne recouvre ni un autre câble ni une machine."""
import math
from typing import List, Mapping, NamedTuple, Optional, Sequence, Tuple

from svgwrite.text import Text

from renderer.models.theme import CableStyle
from renderer.scene.cabling.geometry import Box, Point, is_horizontal

LABEL_GAP_MM = 0.6           # espace entre le bord du câble et son nom
CHAR_WIDTH_FACTOR = 0.6      # largeur moyenne d'un caractère, relative à la taille de police
SLIDE_STEP_MM = 2.0          # pas de recherche d'une place libre le long d'un segment


class LabelPlacement(NamedTuple):
    insert: Point
    rotation: Optional[float]   # None (horizontal) ou -90 (le long d'un segment vertical)


def _segments(points: Sequence[Point]) -> List[Tuple[Point, Point]]:
    return list(zip(points, points[1:]))


def _segment_box(a: Point, b: Point, half_width: float) -> Box:
    return Box(min(a[0], b[0]) - half_width, min(a[1], b[1]) - half_width,
               max(a[0], b[0]) + half_width, max(a[1], b[1]) + half_width)


def _centers(a: Point, b: Point, text_width: float) -> List[Point]:
    """Positions possibles du centre du texte le long du segment, du milieu vers les extrémités."""
    length = math.dist(a, b)
    usable = (length - text_width) / 2
    if usable < 0:
        return []
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    shifts = [0.0]
    step = SLIDE_STEP_MM
    while step <= usable:
        shifts += [step, -step]
        step += SLIDE_STEP_MM
    return [(middle[0] + ux * s, middle[1] + uy * s) for s in shifts]


def _candidate(a: Point, b: Point, middle: Point, side: int, text_width: float, style: CableStyle) -> Tuple[Box, LabelPlacement]:
    """Boîte occupée par le texte centré sur `middle` et point d'insertion, du côté `side` (-1 : haut/gauche, +1 : bas/droite)."""
    gap = style.width_mm / 2 + LABEL_GAP_MM
    size = style.label_font_size_mm
    if is_horizontal(a, b):
        near, far = middle[1] + side * gap, middle[1] + side * (gap + size)
        box = Box(middle[0] - text_width / 2, min(near, far), middle[0] + text_width / 2, max(near, far))
        baseline = max(near, far) - size * 0.2   # la ligne de base est un peu au-dessus du bas de la boîte
        return box, LabelPlacement((middle[0], baseline), None)
    near, far = middle[0] + side * gap, middle[0] + side * (gap + size)
    box = Box(min(near, far), middle[1] - text_width / 2, max(near, far), middle[1] + text_width / 2)
    baseline = max(near, far) - size * 0.2
    return box, LabelPlacement((baseline, middle[1]), -90.0)


def place_label(
    points: Sequence[Point],
    text: str,
    other_routes: Sequence[Sequence[Point]],
    device_boxes: Sequence[Box],
    style: CableStyle,
) -> LabelPlacement:
    """Premier emplacement libre : segments du plus long au plus court, positions du milieu vers les bouts,
    des deux côtés du câble. À défaut, milieu du plus long segment, côté haut/gauche."""
    text_width = len(text) * style.label_font_size_mm * CHAR_WIDTH_FACTOR
    half = style.width_mm / 2
    obstacles = list(device_boxes) + [
        _segment_box(a, b, half) for route in other_routes for a, b in _segments(route)
    ]
    segments = sorted(_segments(points), key=lambda s: math.dist(*s), reverse=True)

    for a, b in segments:
        for middle in _centers(a, b, text_width):
            for side in (-1, 1):
                box, placement = _candidate(a, b, middle, side, text_width, style)
                if not any(box.overlaps(obstacle) for obstacle in obstacles):
                    return placement
    a, b = segments[0]
    return _candidate(a, b, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), -1, text_width, style)[1]


def draw_cable_label(container, text: str, placement: LabelPlacement, color: str, font_family: str, style: CableStyle):
    label = Text(
        text, insert=placement.insert, text_anchor="middle", fill=color,
        font_family=font_family, font_size=style.label_font_size_mm, class_="cable-label",
    )
    if placement.rotation is not None:
        label["transform"] = f"rotate({placement.rotation} {placement.insert[0]} {placement.insert[1]})"
    container.add(label)
