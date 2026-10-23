"""Primitives géométriques du câblage (coordonnées de scène, en mm, y vers le bas)."""
from typing import Iterable, List, NamedTuple, Tuple

from renderer.device.ports import DOWN, LEFT, RIGHT, UP, Direction

Point = Tuple[float, float]
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

EPS = 1e-6


class Box(NamedTuple):
    """Rectangle aligné sur les axes : coin haut-gauche (x1, y1), coin bas-droit (x2, y2)."""
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_rect(cls, rect: Tuple[float, float, float, float]) -> "Box":
        x, y, w, h = rect
        return cls(x, y, x + w, y + h)

    def inflate(self, margin: float) -> "Box":
        return Box(self.x1 - margin, self.y1 - margin, self.x2 + margin, self.y2 + margin)

    def contains_strict(self, point: Point) -> bool:
        x, y = point
        return self.x1 + EPS < x < self.x2 - EPS and self.y1 + EPS < y < self.y2 - EPS

    def overlaps(self, other: "Box") -> bool:
        """Intersection d'aire non nulle (deux boîtes qui se touchent ne se chevauchent pas)."""
        return (
            min(self.x2, other.x2) - max(self.x1, other.x1) > EPS
            and min(self.y2, other.y2) - max(self.y1, other.y1) > EPS
        )


def is_horizontal(a: Point, b: Point) -> bool:
    return abs(a[1] - b[1]) < EPS


def segment_crosses_box(a: Point, b: Point, box: Box) -> bool:
    """Vrai si le segment orthogonal [a, b] passe par l'intérieur strict de la boîte."""
    if is_horizontal(a, b):
        y = a[1]
        return box.y1 + EPS < y < box.y2 - EPS and max(a[0], b[0]) > box.x1 + EPS and min(a[0], b[0]) < box.x2 - EPS
    x = a[0]
    return box.x1 + EPS < x < box.x2 - EPS and max(a[1], b[1]) > box.y1 + EPS and min(a[1], b[1]) < box.y2 - EPS


def simplify(points: Iterable[Point]) -> List[Point]:
    """Supprime les points en double et les points intermédiaires alignés."""
    result: List[Point] = []
    for point in points:
        if result and abs(result[-1][0] - point[0]) < EPS and abs(result[-1][1] - point[1]) < EPS:
            continue
        if len(result) >= 2:
            a, b = result[-2], result[-1]
            if (is_horizontal(a, b) and is_horizontal(b, point)) or (
                abs(a[0] - b[0]) < EPS and abs(b[0] - point[0]) < EPS
            ):
                result[-1] = point
                continue
        result.append(point)
    return result
