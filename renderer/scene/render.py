"""Rendu d'une scène : chargement, validation, placement, câblage, puis dessin des appareils et des câbles."""
import json
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

import svgwrite
from svgwrite.shapes import Rect

from renderer.models.device import DeviceLayout
from renderer.models.scene import Scene
from renderer.models.theme import Theme
from renderer.device.draw import draw_device_to_group
from renderer.scene.cabling import draw_cable_labels, draw_cables, route_cables
from renderer.scene.layout import check_no_overlap, compute_bounds, resolve_positions
from renderer.scene.validation import validate_scene_connections
from renderer.text import BlockLayout, draw_text_block, layout_text_block

SCENE_PADDING_MM = 20.0


def load_scene(scene_path: Union[str, Path]) -> Scene:
    with open(scene_path, 'r', encoding='utf-8') as f:
        return Scene(**json.load(f))


def load_scene_layouts(scene: Scene, base_dir: Union[str, Path]) -> Dict[str, DeviceLayout]:
    """Charge le layout de chaque instance. Les chemins `device` relatifs le sont au dossier du fichier de scène."""
    layouts_by_instance = {}
    for dev_ref in scene.devices:
        device_path = Path(base_dir) / dev_ref.device
        if not device_path.is_file():
            raise ValueError(
                f"Layout introuvable pour '{dev_ref.id}' : {device_path} "
                "(les chemins sont relatifs au dossier du fichier de scène)"
            )
        with open(device_path, 'r', encoding='utf-8') as f:
            layouts_by_instance[dev_ref.id] = DeviceLayout(**json.load(f))
    return layouts_by_instance


class PlacedTitle(NamedTuple):
    layout: BlockLayout
    origin: Tuple[float, float]
    corners: List[Tuple[float, float]]


def _place_title(scene: Scene, rects, cable_points) -> Optional[PlacedTitle]:
    """Titre centré horizontalement sur les machines, au-dessus de tout (machines et câbles), à `title_gap_mm`."""
    if not scene.title:
        return None
    layout = layout_text_block(scene.title)
    left = min(x for x, _, _, _ in rects.values())
    right = max(x + w for x, _, w, _ in rects.values())
    top = min([y for _, y, _, _ in rects.values()] + [y for _, y in cable_points])
    x0, y0, x1, y1 = layout.bbox
    anchor_x = {"left": left, "center": (left + right) / 2, "right": right}[scene.title.align]
    origin = (anchor_x, top - scene.title_gap_mm - y1)
    corners = [(origin[0] + x0, origin[1] + y0), (origin[0] + x1, origin[1] + y1)]
    return PlacedTitle(layout, origin, corners)


def render_scene_svg(
    scene_path: str,
    output_path: str,
    theme: Theme,
    padding_mm: float = SCENE_PADDING_MM,
    show_labels: bool = False
):
    scene = load_scene(scene_path)
    if not scene.devices:
        raise ValueError("La scène ne contient aucun appareil à rendre.")

    layouts_by_instance = load_scene_layouts(scene, Path(scene_path).parent)
    validate_scene_connections(scene, layouts_by_instance)

    resolved_rects = resolve_positions(scene, layouts_by_instance)
    check_no_overlap(resolved_rects)
    routes = route_cables(scene, layouts_by_instance, resolved_rects, theme.cables)
    points = [point for route in routes for point in route.points]
    title = _place_title(scene, resolved_rects, points)
    if title:
        points += title.corners
    bounds = compute_bounds(resolved_rects, padding_mm, points)

    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{bounds.width_mm}mm", f"{bounds.height_mm}mm"),
        viewBox=f"0 0 {bounds.width_mm} {bounds.height_mm}"
    )
    # Pas de fond de scène : le SVG reste transparent (impression sur textile).

    # Tout le contenu est dessiné en coordonnées de scène dans un groupe décalé.
    content = dwg.g(transform=f"translate({bounds.offset_x} {bounds.offset_y})")
    for dev_ref in scene.devices:
        layout = layouts_by_instance[dev_ref.id]
        x, y, dev_w, dev_h = resolved_rects[dev_ref.id]

        device_group = dwg.g(transform=f"translate({x} {y})", class_="device", id=f"device-{dev_ref.id}")
        bg_style = theme.background
        device_group.add(Rect(
            insert=(0, 0),
            size=(dev_w, dev_h),
            rx=bg_style.get("rx", 6),
            fill=bg_style.get("fill", "#222222"),
            stroke=bg_style.get("stroke", "#444444"),
            stroke_width=bg_style.get("stroke_width", 1.5)
        ))
        draw_device_to_group(device_group, layout, theme, show_labels=show_labels)
        content.add(device_group)

    draw_cables(content, routes, theme.cables)
    if show_labels:
        draw_cable_labels(content, routes, theme, resolved_rects)
    if title:
        draw_text_block(content, scene.title, title.origin, theme, title.layout)
    dwg.add(content)

    dwg.save()
