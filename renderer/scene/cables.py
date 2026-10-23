"""Routage et style des câbles entre les ports d'une scène."""
from typing import Mapping, Sequence, Tuple

from svgwrite.path import Path

from renderer.models.scene import SceneConnection
from renderer.scene.layout import Rect

PortKey = Tuple[str, str]  # (id d'instance, id de port)
Point = Tuple[float, float]

STUB_LENGTH_MM = 8.0       # segment vertical à la sortie du port
TRAY_OFFSET_MM = 12.0      # hauteur de la première piste au-dessus de l'appareil source
TRAY_SPACING_MM = 3.5      # écart entre deux pistes
CABLE_WIDTH_MM = 2.5


def cable_color(connection: SceneConnection) -> str:
    return "#e67e22" if "midi" in connection.source.port_id else "#3498db"


def cable_path(start: Point, end: Point, tray_y: float) -> str:
    """Tracé orthogonal « en goulotte » : stub, montée jusqu'à la piste, horizontal, descente vers la cible."""
    x1, y1 = start
    x2, y2 = end
    return (
        f"M {x1} {y1} "
        f"L {x1} {y1 - STUB_LENGTH_MM} "
        f"L {x1} {tray_y} "
        f"L {x2} {tray_y} "
        f"L {x2} {y2 - STUB_LENGTH_MM} "
        f"L {x2} {y2}"
    )


def draw_cables(
    dwg,
    connections: Sequence[SceneConnection],
    port_coordinates: Mapping[PortKey, Point],
    resolved_rects: Mapping[str, Rect],
):
    # Chaque connexion a sa propre piste (index i) pour éviter les superpositions.
    for i, conn in enumerate(connections):
        source_key = (conn.source.device_id, conn.source.port_id)
        target_key = (conn.target.device_id, conn.target.port_id)
        if source_key not in port_coordinates or target_key not in port_coordinates:
            continue

        # Piste juste au-dessus du bord supérieur de la machine source (coordonnées de scène, non décalées).
        src_top_y = resolved_rects[conn.source.device_id][1]
        tray_y = src_top_y - TRAY_OFFSET_MM - (i * TRAY_SPACING_MM)

        dwg.add(Path(
            d=cable_path(port_coordinates[source_key], port_coordinates[target_key], tray_y),
            fill="none",
            stroke=cable_color(conn),
            stroke_width=CABLE_WIDTH_MM,
            stroke_linecap="round",
            stroke_linejoin="round",
            opacity=0.9
        ))
