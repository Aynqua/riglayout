"""Recherche du chemin d'un câble sur la grille : A* qui minimise longueur + pénalité par coude."""
import heapq
import itertools
from typing import Dict, List, Optional, Tuple

from renderer.scene.cabling.geometry import DIRECTIONS, Direction, Point
from renderer.scene.cabling.grid import Node, RoutingGrid

BEND_PENALTY_MM = 12.0

State = Tuple[Node, Direction]
_GOAL = "goal"


def find_route(
    grid: RoutingGrid,
    start: Point,
    start_direction: Direction,
    goal: Point,
    goal_direction: Direction,
    bend_penalty: float = BEND_PENALTY_MM,
) -> Optional[List[Point]]:
    """Chemin de `start` à `goal` (points de la grille, coudes inclus).

    `start_direction` : direction de sortie du port de départ (continuer tout droit ne coûte pas de coude).
    `goal_direction` : direction dans laquelle le câble doit arriver pour entrer dans le port cible.
    """
    start_node, goal_node = grid.node_at(start), grid.node_at(goal)
    goal_x, goal_y = grid.point(goal_node)

    def heuristic(node: Node) -> float:
        x, y = grid.point(node)
        return abs(x - goal_x) + abs(y - goal_y)

    counter = itertools.count()
    start_state: State = (start_node, start_direction)
    queue = [(heuristic(start_node), next(counter), 0.0, start_state)]
    best: Dict[object, float] = {start_state: 0.0}
    parent: Dict[object, object] = {}

    while queue:
        _, _, cost, state = heapq.heappop(queue)
        if cost > best.get(state, float("inf")):
            continue
        if state[0] == _GOAL:
            return _reconstruct(grid, parent, state)

        node, direction = state
        if node == goal_node:
            final_cost = cost + (0.0 if direction == goal_direction else bend_penalty)
            final_state = (_GOAL, direction)
            if final_cost < best.get(final_state, float("inf")):
                best[final_state] = final_cost
                parent[final_state] = state
                heapq.heappush(queue, (final_cost, next(counter), final_cost, final_state))
            continue

        x, y = grid.point(node)
        for new_direction in DIRECTIONS:
            if new_direction == (-direction[0], -direction[1]):
                continue  # pas de demi-tour
            neighbor = grid.step(node, new_direction)
            if neighbor is None:
                continue
            nx, ny = grid.point(neighbor)
            new_cost = cost + abs(nx - x) + abs(ny - y) + (0.0 if new_direction == direction else bend_penalty)
            new_state = (neighbor, new_direction)
            if new_cost < best.get(new_state, float("inf")):
                best[new_state] = new_cost
                parent[new_state] = state
                heapq.heappush(queue, (new_cost + heuristic(neighbor), next(counter), new_cost, new_state))
    return None


def _reconstruct(grid: RoutingGrid, parent: Dict[object, object], goal_state) -> List[Point]:
    points: List[Point] = []
    state = parent[goal_state]
    while True:
        points.append(grid.point(state[0]))
        if state not in parent:
            break
        state = parent[state]
    points.reverse()
    return points
