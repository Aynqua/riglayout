"""Câblage d'une scène : du port source au port cible sans traverser de machine ni se superposer.

Étapes : ancrage des ports (anchors) → grille autour des machines (grid) → plus court chemin par câble (router)
→ séparation des câbles qui partagent un couloir (nudging) → vérification → dessin (draw) → noms (labels).
"""
from typing import Dict, List, Mapping, NamedTuple

from renderer.models.device import DeviceLayout
from renderer.models.scene import Scene, SceneConnection
from renderer.models.theme import CableStyle, Theme
from renderer.scene.cabling.anchors import PortAnchor, port_anchor
from renderer.scene.cabling.draw import draw_cable
from renderer.scene.cabling.labels import draw_cable_label, place_label
from renderer.scene.cabling.geometry import Box, Point, segment_crosses_box, simplify
from renderer.scene.cabling.grid import RoutingGrid
from renderer.scene.cabling.nudging import nudge_routes
from renderer.scene.cabling.router import find_route
from renderer.scene.layout import Rect


class CableRoute(NamedTuple):
    connection: SceneConnection
    signal: str
    points: List[Point]   # polyligne orthogonale en coordonnées de scène, du port source au port cible


def route_cables(
    scene: Scene,
    layouts_by_instance: Mapping[str, DeviceLayout],
    rects: Mapping[str, Rect],
    style: CableStyle,
) -> List[CableRoute]:
    if not scene.connections:
        return []

    boxes: Dict[str, Box] = {device_id: Box.from_rect(rect) for device_id, rect in rects.items()}
    device_ids = list(boxes)
    obstacles = [boxes[device_id].inflate(style.clearance_mm) for device_id in device_ids]

    def anchor(device_id: str, port_id: str) -> PortAnchor:
        port = next(p for p in layouts_by_instance[device_id].ports if p.id == port_id)
        return port_anchor(port, boxes[device_id], style.clearance_mm)

    ends = [(anchor(c.source.device_id, c.source.port_id), anchor(c.target.device_id, c.target.port_id))
            for c in scene.connections]

    _check_distinct_plugs(scene.connections, ends)

    grid = RoutingGrid(obstacles, [a.exit for pair in ends for a in pair], frame_margin=style.clearance_mm * 2)
    for connection, pair in zip(scene.connections, ends):
        for endpoint, end in zip((connection.source, connection.target), pair):
            blocker = grid.blocking_obstacle(end.exit)
            if blocker is not None:
                raise ValueError(
                    f"Le port '{endpoint.port_id}' de '{endpoint.device_id}' est trop proche de "
                    f"'{device_ids[blocker]}' pour y brancher un câble (écart minimal : {style.clearance_mm} mm)"
                )

    paths: List[List[Point]] = []
    for connection, (source, target) in zip(scene.connections, ends):
        inward = (-target.direction[0], -target.direction[1])
        path = find_route(grid, source.exit, source.direction, target.exit, inward)
        if path is None:
            raise ValueError(
                f"Aucun chemin possible pour le câble {connection.source.device_id}:{connection.source.port_id}"
                f" → {connection.target.device_id}:{connection.target.port_id}"
            )
        paths.append(path)

    raw_routes = [simplify([source.point, *path, target.point]) for path, (source, target) in zip(paths, ends)]

    routes = nudge_routes(raw_routes, list(boxes.values()), style.spacing_mm, style.width_mm, style.clearance_mm)
    _check_no_device_crossing(scene.connections, routes, boxes)

    signals = [
        next(p for p in layouts_by_instance[c.source.device_id].ports if p.id == c.source.port_id).signal
        for c in scene.connections
    ]
    return [CableRoute(c, signal, points) for c, signal, points in zip(scene.connections, signals, routes)]


def _check_distinct_plugs(connections, ends):
    """Deux câbles ne peuvent pas se brancher au même endroit (ports déclarés à la même position)."""
    seen: Dict[Point, str] = {}
    for connection, pair in zip(connections, ends):
        for endpoint, end in zip((connection.source, connection.target), pair):
            key = (round(end.point[0], 3), round(end.point[1], 3))
            name = f"{endpoint.device_id}:{endpoint.port_id}"
            if key in seen:
                raise ValueError(
                    f"Les ports {seen[key]} et {name} sont à la même position : "
                    "deux câbles ne peuvent pas se brancher au même endroit (corrige x/y dans le layout)"
                )
            seen[key] = name


def _check_no_device_crossing(connections, routes, boxes: Mapping[str, Box]):
    for connection, points in zip(connections, routes):
        for a, b in zip(points, points[1:]):
            for device_id, box in boxes.items():
                if segment_crosses_box(a, b, box):
                    raise ValueError(
                        f"Le câble {connection.source.device_id}:{connection.source.port_id} → "
                        f"{connection.target.device_id}:{connection.target.port_id} traverserait '{device_id}'"
                    )


def draw_cables(container, routes: List[CableRoute], style: CableStyle):
    for route in routes:
        draw_cable(container, route.points, getattr(style.colors, route.signal), route.signal, style)


def draw_cable_labels(container, routes: List[CableRoute], theme: Theme, rects: Mapping[str, Rect]):
    """Mode détail : écrit le `label` de chaque connexion qui en a un, dans la couleur du câble,
    à un endroit libre (ni sur un autre câble, ni sur une machine)."""
    device_boxes = [Box.from_rect(rect) for rect in rects.values()]
    for route in routes:
        if not route.connection.label:
            continue
        others = [other.points for other in routes if other is not route]
        placement = place_label(route.points, route.connection.label, others, device_boxes, theme.cables)
        color = getattr(theme.cables.colors, route.signal)
        draw_cable_label(container, route.connection.label, placement, color, theme.labels.font_family, theme.cables)
