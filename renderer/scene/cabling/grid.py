"""Grille de routage orthogonale autour des machines.

Les lignes de la grille passent par les bords des machines gonflés de `clearance`, par les points de sortie
des ports, par les milieux entre machines (couloirs centrés) et par un cadre extérieur pour pouvoir tout contourner.
Un nœud ou une arête à l'intérieur strict d'une zone gonflée est interdit : un câble ne peut donc pas passer sur une machine.
"""
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from renderer.scene.cabling.geometry import Box, Direction, Point

Node = Tuple[int, int]  # (indice dans xs, indice dans ys)

PRECISION = 6


def _key(value: float) -> float:
    return round(value, PRECISION)


def _with_midpoints(values: Iterable[float]) -> List[float]:
    ordered = sorted({_key(v) for v in values})
    return ordered + [_key((a + b) / 2) for a, b in zip(ordered, ordered[1:])]


class RoutingGrid:
    def __init__(self, obstacles: Sequence[Box], waypoints: Iterable[Point], frame_margin: float):
        self.obstacles = list(obstacles)
        waypoints = list(waypoints)

        frame = Box(
            min([b.x1 for b in self.obstacles] + [p[0] for p in waypoints]) - frame_margin,
            min([b.y1 for b in self.obstacles] + [p[1] for p in waypoints]) - frame_margin,
            max([b.x2 for b in self.obstacles] + [p[0] for p in waypoints]) + frame_margin,
            max([b.y2 for b in self.obstacles] + [p[1] for p in waypoints]) + frame_margin,
        )
        obstacle_xs = [frame.x1, frame.x2] + [v for b in self.obstacles for v in (b.x1, b.x2)]
        obstacle_ys = [frame.y1, frame.y2] + [v for b in self.obstacles for v in (b.y1, b.y2)]

        self.xs: List[float] = sorted(set(_with_midpoints(obstacle_xs)) | {_key(p[0]) for p in waypoints})
        self.ys: List[float] = sorted(set(_with_midpoints(obstacle_ys)) | {_key(p[1]) for p in waypoints})
        self._x_index: Dict[float, int] = {x: i for i, x in enumerate(self.xs)}
        self._y_index: Dict[float, int] = {y: i for i, y in enumerate(self.ys)}
        self._free_cache: Dict[Node, bool] = {}
        self._step_cache: Dict[Tuple[Node, Direction], Optional[Node]] = {}

    def point(self, node: Node) -> Point:
        return self.xs[node[0]], self.ys[node[1]]

    def node_at(self, point: Point) -> Node:
        return self._x_index[_key(point[0])], self._y_index[_key(point[1])]

    def is_free(self, node: Node) -> bool:
        if node not in self._free_cache:
            point = self.point(node)
            self._free_cache[node] = not any(box.contains_strict(point) for box in self.obstacles)
        return self._free_cache[node]

    def blocking_obstacle(self, point: Point) -> Optional[int]:
        for index, box in enumerate(self.obstacles):
            if box.contains_strict(point):
                return index
        return None

    def step(self, node: Node, direction: Direction) -> Optional[Node]:
        """Nœud voisin dans `direction`, ou None si hors grille ou si l'arête traverse une machine."""
        key = (node, direction)
        if key not in self._step_cache:
            self._step_cache[key] = self._compute_step(node, direction)
        return self._step_cache[key]

    def _compute_step(self, node: Node, direction: Direction) -> Optional[Node]:
        ix, iy = node[0] + direction[0], node[1] + direction[1]
        if not (0 <= ix < len(self.xs) and 0 <= iy < len(self.ys)):
            return None
        neighbor = (ix, iy)
        if not self.is_free(neighbor):
            return None
        (x1, y1), (x2, y2) = self.point(node), self.point(neighbor)
        middle = ((x1 + x2) / 2, (y1 + y2) / 2)
        if any(box.contains_strict(middle) for box in self.obstacles):
            return None
        return neighbor
