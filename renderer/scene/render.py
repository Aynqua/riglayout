"""Rendu d'une scène : chargement, validation, placement, dessin des appareils puis des câbles."""
import json
from typing import Dict

import svgwrite
from svgwrite.shapes import Rect

from renderer.models.device import DeviceLayout
from renderer.models.scene import Scene
from renderer.models.theme import Theme
from renderer.device.draw import draw_device_to_group
from renderer.scene.cables import PortKey, Point, draw_cables
from renderer.scene.layout import compute_bounds, resolve_positions
from renderer.scene.validation import validate_scene_connections

SCENE_BACKGROUND = "#111111"


def load_scene(scene_path: str) -> Scene:
    with open(scene_path, 'r', encoding='utf-8') as f:
        return Scene(**json.load(f))


def load_scene_layouts(scene: Scene) -> Dict[str, DeviceLayout]:
    """Charge le layout de chaque instance. Les chemins `device` sont relatifs au dossier courant."""
    layouts_by_instance = {}
    for dev_ref in scene.devices:
        with open(dev_ref.device, 'r', encoding='utf-8') as f:
            layouts_by_instance[dev_ref.id] = DeviceLayout(**json.load(f))
    return layouts_by_instance


def render_scene_svg(
    scene_path: str,
    output_path: str,
    theme: Theme,
    padding_mm: float = 80.0,
    show_labels: bool = False
):
    scene = load_scene(scene_path)
    if not scene.devices:
        raise ValueError("La scène ne contient aucun appareil à rendre.")

    layouts_by_instance = load_scene_layouts(scene)
    validate_scene_connections(scene, layouts_by_instance)

    resolved_rects = resolve_positions(scene, layouts_by_instance)
    bounds = compute_bounds(resolved_rects, padding_mm)

    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{bounds.width_mm}mm", f"{bounds.height_mm}mm"),
        viewBox=f"0 0 {bounds.width_mm} {bounds.height_mm}"
    )
    dwg.add(Rect(insert=(0, 0), size=(bounds.width_mm, bounds.height_mm), fill=SCENE_BACKGROUND))

    port_coordinates: Dict[PortKey, Point] = {}
    for dev_ref in scene.devices:
        layout = layouts_by_instance[dev_ref.id]
        rx, ry, dev_w, dev_h = resolved_rects[dev_ref.id]
        final_x = rx + bounds.offset_x
        final_y = ry + bounds.offset_y

        device_group = dwg.g(transform=f"translate({final_x} {final_y})")

        # Fond de l'appareil (basé sur le thème)
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
        dwg.add(device_group)

        # Coordonnées absolues (SVG) des ports, points d'ancrage des câbles
        for port in layout.ports:
            port_coordinates[(dev_ref.id, port.id)] = (final_x + (port.x * dev_w), final_y + (port.y * dev_h))

    draw_cables(dwg, scene.connections, port_coordinates, resolved_rects)

    dwg.save()
    print(f"Scène rendue avec succès dans : {output_path} (Taille auto : {bounds.width_mm:.1f}x{bounds.height_mm:.1f} mm)")
