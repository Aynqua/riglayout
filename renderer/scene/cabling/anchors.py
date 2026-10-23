"""Points de branchement : où un câble touche la machine et dans quelle direction il en sort."""
from typing import NamedTuple

from renderer.models.device import DevicePort
from renderer.scene.cabling.geometry import DOWN, LEFT, RIGHT, UP, Box, Direction, Point


class PortAnchor(NamedTuple):
    point: Point          # sur le bord de la machine
    direction: Direction  # sortie, perpendiculaire au bord
    exit: Point           # point à `clearance` du bord, où commence le routage


def port_side(port: DevicePort) -> Direction:
    """Bord le plus proche de la position normalisée du port (ordre en cas d'égalité : haut, bas, gauche, droite)."""
    distances = ((port.y, UP), (1 - port.y, DOWN), (port.x, LEFT), (1 - port.x, RIGHT))
    return min(distances, key=lambda item: item[0])[1]


def port_anchor(port: DevicePort, box: Box, clearance: float) -> PortAnchor:
    """Projette le port sur son bord : un câble se branche toujours sur la tranche de la machine."""
    width, height = box.x2 - box.x1, box.y2 - box.y1
    direction = port_side(port)
    if direction == UP:
        point = (box.x1 + port.x * width, box.y1)
    elif direction == DOWN:
        point = (box.x1 + port.x * width, box.y2)
    elif direction == LEFT:
        point = (box.x1, box.y1 + port.y * height)
    else:
        point = (box.x2, box.y1 + port.y * height)
    exit_point = (point[0] + direction[0] * clearance, point[1] + direction[1] * clearance)
    return PortAnchor(point, direction, exit_point)
