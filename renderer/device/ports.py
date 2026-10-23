"""Ports d'un appareil : bord sur lequel ils se trouvent, et dessin (prise + nom) en mode détail."""
from typing import Tuple

from svgwrite.shapes import Circle
from svgwrite.text import Text

from renderer.models.device import DeviceLayout, DevicePort
from renderer.models.theme import Theme
from renderer.device.legends import label_color

Direction = Tuple[int, int]

# Directions en coordonnées SVG (y vers le bas).
UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)


def port_side(port: DevicePort) -> Direction:
    """Bord le plus proche de la position normalisée du port (ordre en cas d'égalité : haut, bas, gauche, droite)."""
    distances = ((port.y, UP), (1 - port.y, DOWN), (port.x, LEFT), (1 - port.x, RIGHT))
    return min(distances, key=lambda item: item[0])[1]


def port_edge_point(port: DevicePort, width: float, height: float) -> Tuple[float, float]:
    """Position du port projetée sur la tranche, en coordonnées locales à l'appareil (mm)."""
    side = port_side(port)
    if side == UP:
        return port.x * width, 0.0
    if side == DOWN:
        return port.x * width, height
    if side == LEFT:
        return 0.0, port.y * height
    return width, port.y * height


def draw_ports(container, layout: DeviceLayout, theme: Theme):
    """Dessine chaque port : un cercle sur la tranche et son nom, écrit vers l'intérieur de l'appareil."""
    style = theme.ports
    color = style.fill or label_color(theme)
    width, height = layout.physical.width_mm, layout.physical.height_mm

    for port in layout.ports:
        x, y = port_edge_point(port, width, height)
        side = port_side(port)
        container.add(Circle(
            center=(x, y), r=style.marker_radius_mm,
            fill="none", stroke=color, stroke_width=style.stroke_width_mm,
            class_="port",
        ))

        # Le texte part juste à l'intérieur de la prise et s'éloigne du bord.
        inset = style.marker_radius_mm + style.label_gap_mm
        text_x, text_y = x - side[0] * inset, y - side[1] * inset
        if side in (UP, DOWN):
            angle = 90 if side == UP else -90
            anchor, transform = "start", f"rotate({angle} {text_x} {text_y})"
        else:
            anchor, transform = ("start" if side == LEFT else "end"), None

        text = Text(
            port.label, insert=(text_x, text_y), text_anchor=anchor, dominant_baseline="central",
            fill=color, font_family=theme.labels.font_family, font_size=style.font_size_mm,
            class_="port-label",
        )
        if transform:
            text["transform"] = transform
        container.add(text)
