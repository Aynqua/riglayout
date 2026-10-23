"""Placement des appareils d'une scène : positions absolues/relatives, chevauchements et encombrement total."""
from typing import Dict, Iterable, Mapping, NamedTuple, Tuple

from renderer.models.device import DeviceLayout
from renderer.models.scene import Scene

# id d'instance -> (x haut-gauche, y haut-gauche, largeur, hauteur), en mm
Rect = Tuple[float, float, float, float]
Point = Tuple[float, float]

MAX_RESOLUTION_PASSES = 10
OVERLAP_TOLERANCE_MM = 1e-6


class SceneBounds(NamedTuple):
    width_mm: float
    height_mm: float
    offset_x: float  # à ajouter aux coordonnées de scène pour obtenir celles du SVG
    offset_y: float


def resolve_positions(scene: Scene, layouts_by_instance: Mapping[str, DeviceLayout]) -> Dict[str, Rect]:
    """Résout les positions absolues puis relatives en cascade (une relative attend que sa cible soit placée)."""
    resolved_rects: Dict[str, Rect] = {}
    unresolved = list(scene.devices)
    iterations = 0

    while unresolved and iterations < MAX_RESOLUTION_PASSES:
        next_unresolved = []
        for dev_ref in unresolved:
            layout = layouts_by_instance[dev_ref.id]
            dev_w = layout.physical.width_mm
            dev_h = layout.physical.height_mm
            pos = dev_ref.position

            if pos.type == "absolute":
                resolved_rects[dev_ref.id] = (pos.x, pos.y, dev_w, dev_h)
            elif pos.type == "relative":
                if pos.target not in resolved_rects:
                    next_unresolved.append(dev_ref)
                    continue
                t_x, t_y, t_w, t_h = resolved_rects[pos.target]
                spacing = pos.spacing_mm

                if pos.anchor == "right":
                    x, y = t_x + t_w + spacing, t_y
                elif pos.anchor == "left":
                    x, y = t_x - dev_w - spacing, t_y
                elif pos.anchor == "bottom":
                    x, y = t_x, t_y + t_h + spacing
                elif pos.anchor == "top":
                    x, y = t_x, t_y - dev_h - spacing
                else:
                    x, y = t_x + t_w + spacing, t_y

                resolved_rects[dev_ref.id] = (x, y, dev_w, dev_h)

        if len(unresolved) == len(next_unresolved):
            raise ValueError("Erreur de dépendance circulaire ou cible introuvable dans les positions relatives.")
        unresolved = next_unresolved
        iterations += 1

    return resolved_rects


def check_no_overlap(resolved_rects: Mapping[str, Rect]) -> None:
    """Deux machines ne peuvent pas occuper la même place (se toucher est permis)."""
    items = list(resolved_rects.items())
    for i, (id_a, (ax, ay, aw, ah)) in enumerate(items):
        for id_b, (bx, by, bw, bh) in items[i + 1:]:
            overlap_x = min(ax + aw, bx + bw) - max(ax, bx)
            overlap_y = min(ay + ah, by + bh) - max(ay, by)
            if overlap_x > OVERLAP_TOLERANCE_MM and overlap_y > OVERLAP_TOLERANCE_MM:
                raise ValueError(
                    f"Les appareils '{id_a}' et '{id_b}' se superposent "
                    f"({overlap_x:.1f} × {overlap_y:.1f} mm) : ajuste leurs positions dans la scène"
                )


def compute_bounds(resolved_rects: Mapping[str, Rect], padding_mm: float, points: Iterable[Point] = ()) -> SceneBounds:
    """Taille du SVG englobant les appareils et les `points` (tracés des câbles) + marge,
    et décalage pour ramener le coin haut-gauche à la marge."""
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for x, y, w, h in resolved_rects.values():
        min_x = min(min_x, x)
        max_x = max(max_x, x + w)
        min_y = min(min_y, y)
        max_y = max(max_y, y + h)
    for x, y in points:
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)

    return SceneBounds(
        width_mm=(max_x - min_x) + (padding_mm * 2),
        height_mm=(max_y - min_y) + (padding_mm * 2),
        offset_x=padding_mm - min_x,
        offset_y=padding_mm - min_y,
    )
