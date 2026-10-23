"""Séparation des câbles qui empruntent le même couloir.

Après le routage, plusieurs câbles peuvent partager la même ligne de grille. Chaque groupe de segments
colinéaires qui se recouvrent est réparti en voies parallèles espacées de `spacing`. L'ordre des voies
est choisi selon l'endroit où chaque câble quitte le couloir, pour éviter qu'ils se croisent.

Le premier et le dernier segment d'un câble (ceux qui sortent du port) restent fixes.
"""
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Dict, List, Optional, Sequence, Tuple

from renderer.scene.cabling.geometry import EPS, Box, Point, is_horizontal

LANE_SAFETY_MM = 0.5   # marge supplémentaire entre le bord d'un câble et une machine
MAX_LOOKAHEAD = 8


@dataclass
class _Segment:
    route: int
    index: int
    horizontal: bool
    track: float              # y d'un segment horizontal, x d'un segment vertical
    lo: float                 # bornes le long du segment
    hi: float
    anchored: bool
    lo_turn: int = 0          # -1 / +1 : côté vers lequel part le segment voisin à l'extrémité lo (0 = aucun)
    hi_turn: int = 0
    lo_neighbor: Optional[int] = None
    hi_neighbor: Optional[int] = None
    offset: float = 0.0


def _sign(value: float) -> int:
    return 0 if abs(value) < EPS else (1 if value > 0 else -1)


def _build_segments(route_index: int, points: Sequence[Point]) -> List[_Segment]:
    segments = []
    last = len(points) - 2
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        horizontal = is_horizontal(a, b)
        along = (lambda p: p[0]) if horizontal else (lambda p: p[1])
        across = (lambda p: p[1]) if horizontal else (lambda p: p[0])
        track = across(a)

        # Voisins attachés en a (segment i-1) et en b (segment i+1), et côté vers lequel ils partent.
        a_neighbor = i - 1 if i > 0 else None
        b_neighbor = i + 1 if i < last else None
        a_turn = _sign(across(points[i - 1]) - track) if a_neighbor is not None else 0
        b_turn = _sign(across(points[i + 2]) - track) if b_neighbor is not None else 0

        segment = _Segment(route_index, i, horizontal, track, min(along(a), along(b)), max(along(a), along(b)),
                           anchored=(i == 0 or i == last))
        if along(a) <= along(b):
            segment.lo_turn, segment.lo_neighbor, segment.hi_turn, segment.hi_neighbor = a_turn, a_neighbor, b_turn, b_neighbor
        else:
            segment.lo_turn, segment.lo_neighbor, segment.hi_turn, segment.hi_neighbor = b_turn, b_neighbor, a_turn, a_neighbor
        segments.append(segment)
    return segments


class _Ordering:
    """Compare deux segments d'un même couloir : négatif si `a` doit être du côté -1 (haut / gauche)."""

    def __init__(self, segments: List[List[_Segment]]):
        self.segments = segments

    def compare(self, a: _Segment, b: _Segment, skip_side: Optional[str] = None, depth: int = 0) -> int:
        for side in ("lo", "hi"):
            if side == skip_side:
                continue
            decision = self._decide_side(a, b, side, depth)
            if decision:
                return decision
        return 0

    def _decide_side(self, a: _Segment, b: _Segment, side: str, depth: int) -> int:
        a_end, b_end = getattr(a, side), getattr(b, side)
        a_turn, b_turn = getattr(a, f"{side}_turn"), getattr(b, f"{side}_turn")
        # Du côté lo, celui qui s'arrête le plus tôt est celui dont la borne est la plus grande (et inversement).
        a_leaves_first = a_end > b_end + EPS if side == "lo" else a_end < b_end - EPS
        b_leaves_first = b_end > a_end + EPS if side == "lo" else b_end < a_end - EPS

        if a_leaves_first:
            return a_turn     # a quitte le couloir vers son côté : il doit y être placé
        if b_leaves_first:
            return -b_turn
        if a_turn != b_turn:
            return _sign(a_turn - b_turn)
        if a_turn == 0 or depth >= MAX_LOOKAHEAD:
            return 0

        # Même coude au même endroit : l'ordre se décide plus loin, sur le couloir perpendiculaire.
        a_next = self.segments[a.route][getattr(a, f"{side}_neighbor")]
        b_next = self.segments[b.route][getattr(b, f"{side}_neighbor")]
        back_side = "hi" if a_turn == -1 else "lo"   # extrémité du voisin qui revient vers ce couloir
        sub = self.compare(a_next, b_next, skip_side=back_side, depth=depth + 1)
        # Au passage d'un coude, l'ordre s'inverse pour (lo, -1) et (hi, +1).
        inverted = (side == "lo" and a_turn == -1) or (side == "hi" and a_turn == 1)
        return -sub if inverted else sub


def _groups(segments: List[List[_Segment]]) -> List[List[_Segment]]:
    """Segments mobiles colinéaires dont les intervalles se recouvrent."""
    by_track: Dict[Tuple[bool, float], List[_Segment]] = {}
    for route_segments in segments:
        for segment in route_segments:
            if not segment.anchored:
                by_track.setdefault((segment.horizontal, round(segment.track, 6)), []).append(segment)

    groups = []
    for track_segments in by_track.values():
        track_segments.sort(key=lambda s: s.lo)
        current: List[_Segment] = []
        current_hi = float("-inf")
        for segment in track_segments:
            if current and segment.lo < current_hi - EPS:
                current.append(segment)
                current_hi = max(current_hi, segment.hi)
            else:
                if len(current) > 1:
                    groups.append(current)
                current, current_hi = [segment], segment.hi
        if len(current) > 1:
            groups.append(current)
    return groups


def _free_space(group: List[_Segment], boxes: Sequence[Box]) -> Tuple[float, float]:
    """Distance libre de part et d'autre du couloir jusqu'à la machine la plus proche."""
    horizontal = group[0].horizontal
    track = group[0].track
    lo, hi = min(s.lo for s in group), max(s.hi for s in group)
    negative = positive = float("inf")
    for box in boxes:
        along_lo, along_hi = (box.x1, box.x2) if horizontal else (box.y1, box.y2)
        across_lo, across_hi = (box.y1, box.y2) if horizontal else (box.x1, box.x2)
        if along_lo >= hi - EPS or along_hi <= lo + EPS:
            continue
        if across_hi <= track + EPS:
            negative = min(negative, track - across_hi)
        elif across_lo >= track - EPS:
            positive = min(positive, across_lo - track)
    return negative, positive


def _lane_offsets(
    count: int, spacing: float, negative_free: float, positive_free: float, half_width: float, clearance: float
) -> List[float]:
    """Décalages des voies, centrés sur le couloir puis repoussés pour rester à `clearance` des machines.
    Si le couloir est trop étroit pour ça, on se contente de ne pas toucher les machines (marge `half_width`)
    et, en dernier recours, on resserre l'espacement."""
    span = (count - 1) * spacing
    lower, upper = -(negative_free - clearance), positive_free - clearance
    if span > upper - lower:
        lower, upper = -negative_free + half_width, positive_free - half_width
        room = upper - lower
        if span > room:
            spacing = max(room, 0.0) / (count - 1)
            span = (count - 1) * spacing
    start = -span / 2
    if start < lower:
        start = lower
    if start + span > upper:
        start = upper - span
    return [start + k * spacing for k in range(count)]


def _rebuild(points: Sequence[Point], segments: List[_Segment]) -> List[Point]:
    """Recalcule les coudes : intersection des segments voisins une fois décalés."""
    rebuilt = [points[0]]
    for previous, following in zip(segments, segments[1:]):
        if previous.horizontal:
            rebuilt.append((following.track + following.offset, previous.track + previous.offset))
        else:
            rebuilt.append((previous.track + previous.offset, following.track + following.offset))
    rebuilt.append(points[-1])
    return rebuilt


def nudge_routes(
    routes: Sequence[Sequence[Point]], boxes: Sequence[Box], spacing: float, width: float, clearance: float = 0.0
) -> List[List[Point]]:
    segments = [_build_segments(i, points) for i, points in enumerate(routes)]
    ordering = _Ordering(segments)

    def compare(a: _Segment, b: _Segment) -> int:
        return ordering.compare(a, b) or (a.route - b.route)

    for group in _groups(segments):
        ordered = sorted(group, key=cmp_to_key(compare))
        negative_free, positive_free = _free_space(group, boxes)
        offsets = _lane_offsets(len(ordered), spacing, negative_free, positive_free, width / 2 + LANE_SAFETY_MM, clearance)
        for segment, offset in zip(ordered, offsets):
            segment.offset = offset

    return [_rebuild(points, route_segments) for points, route_segments in zip(routes, segments)]
