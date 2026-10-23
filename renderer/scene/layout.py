"""Placement des appareils d'une scène : positions absolues/relatives et encombrement total."""
from typing import Dict, Mapping, NamedTuple, Tuple

from renderer.models.device import DeviceLayout
from renderer.models.scene import Scene

# id d'instance -> (x haut-gauche, y haut-gauche, largeur, hauteur), en mm
Rect = Tuple[float, float, float, float]

MAX_RESOLUTION_PASSES = 10


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


def compute_bounds(resolved_rects: Mapping[str, Rect], padding_mm: float) -> SceneBounds:
    """Taille du SVG englobant tous les appareils + marge, et décalage pour ramener le coin haut-gauche à la marge."""
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for x, y, w, h in resolved_rects.values():
        min_x = min(min_x, x)
        max_x = max(max_x, x + w)
        min_y = min(min_y, y)
        max_y = max(max_y, y + h)

    return SceneBounds(
        width_mm=(max_x - min_x) + (padding_mm * 2),
        height_mm=(max_y - min_y) + (padding_mm * 2),
        offset_x=padding_mm - min_x,
        offset_y=padding_mm - min_y,
    )
