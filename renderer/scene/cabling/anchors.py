"""Points de branchement : où un câble touche la machine et dans quelle direction il en sort."""
from typing import NamedTuple

from renderer.device.ports import port_edge_point, port_side
from renderer.models.device import DevicePort
from renderer.scene.cabling.geometry import Box, Direction, Point

__all__ = ["PortAnchor", "port_anchor", "port_side"]


class PortAnchor(NamedTuple):
    point: Point          # sur le bord de la machine
    direction: Direction  # sortie, perpendiculaire au bord
    exit: Point           # point à `clearance` du bord, où commence le routage


def port_anchor(port: DevicePort, box: Box, clearance: float) -> PortAnchor:
    """Projette le port sur son bord : un câble se branche toujours sur la tranche de la machine."""
    local_x, local_y = port_edge_point(port, box.x2 - box.x1, box.y2 - box.y1)
    point = (box.x1 + local_x, box.y1 + local_y)
    direction = port_side(port)
    exit_point = (point[0] + direction[0] * clearance, point[1] + direction[1] * clearance)
    return PortAnchor(point, direction, exit_point)
