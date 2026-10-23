"""Dessin SVG des câbles : tracé à coudes arrondis et pastille sur chaque prise."""
import math
from typing import Sequence

from svgwrite.container import Group
from svgwrite.path import Path
from svgwrite.shapes import Circle

from renderer.models.theme import CableStyle
from renderer.scene.cabling.geometry import Point

PLUG_RADIUS_FACTOR = 1.1   # rayon de la pastille de prise, relatif à l'épaisseur du câble


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def rounded_path(points: Sequence[Point], radius: float) -> str:
    """Path SVG d'une polyligne orthogonale dont chaque coude est arrondi (courbe quadratique)."""
    commands = [f"M {_fmt(points[0][0])} {_fmt(points[0][1])}"]
    for previous, corner, following in zip(points, points[1:], points[2:]):
        before = math.dist(previous, corner)
        after = math.dist(corner, following)
        r = min(radius, before / 2, after / 2)
        if r <= 0:
            commands.append(f"L {_fmt(corner[0])} {_fmt(corner[1])}")
            continue
        start = (corner[0] + (previous[0] - corner[0]) * r / before, corner[1] + (previous[1] - corner[1]) * r / before)
        end = (corner[0] + (following[0] - corner[0]) * r / after, corner[1] + (following[1] - corner[1]) * r / after)
        commands.append(f"L {_fmt(start[0])} {_fmt(start[1])}")
        commands.append(f"Q {_fmt(corner[0])} {_fmt(corner[1])} {_fmt(end[0])} {_fmt(end[1])}")
    commands.append(f"L {_fmt(points[-1][0])} {_fmt(points[-1][1])}")
    return " ".join(commands)


def draw_cable(container, points: Sequence[Point], color: str, signal: str, style: CableStyle):
    """Ajoute à `container` un groupe <g class="cable cable-<signal>"> : le tracé + une pastille par prise."""
    group = Group(class_=f"cable cable-{signal}", opacity=style.opacity)
    group.add(Path(
        d=rounded_path(points, style.corner_radius_mm),
        fill="none", stroke=color, stroke_width=style.width_mm,
        stroke_linecap="round", stroke_linejoin="round",
    ))
    for plug in (points[0], points[-1]):
        group.add(Circle(center=plug, r=style.width_mm * PLUG_RADIUS_FACTOR, fill=color, stroke="none"))
    container.add(group)
