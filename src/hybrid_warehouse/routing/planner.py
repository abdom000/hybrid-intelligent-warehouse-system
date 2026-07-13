from __future__ import annotations

import heapq
from collections import defaultdict

from hybrid_warehouse.schemas import RouteResult, WarehousePath, WarehouseZone


class RoutePlanningError(ValueError):
    """Raised when route planning receives inconsistent inputs."""


class RoutePlanner:
    """Shortest-path planner over the warehouse zone graph.

    Only active zones and active paths participate in planning, so a
    disabled path (for example one blocked by an obstacle) automatically
    makes dependent routes unavailable. Distances are minimized with
    Dijkstra's algorithm; travel time is accumulated along the same route.
    """

    def __init__(
        self,
        *,
        zones: list[WarehouseZone],
        paths: list[WarehousePath],
    ) -> None:
        if not zones:
            raise RoutePlanningError("At least one zone is required.")

        self._zone_ids = {zone.zone_id for zone in zones}
        self._active_zone_ids = {zone.zone_id for zone in zones if zone.active}

        self._graph: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
        for path in paths:
            if not path.active:
                continue
            if (
                path.start_zone_id not in self._active_zone_ids
                or path.end_zone_id not in self._active_zone_ids
            ):
                continue
            self._graph[path.start_zone_id].append(
                (
                    path.end_zone_id,
                    path.distance_meters,
                    path.estimated_travel_seconds,
                )
            )

    def plan_route(
        self,
        *,
        robot_id: str,
        start_zone_id: str,
        destination_zone_id: str,
    ) -> RouteResult:
        for zone_id in (start_zone_id, destination_zone_id):
            if zone_id not in self._zone_ids:
                raise RoutePlanningError(f"Unknown zone: {zone_id}")

        def unavailable() -> RouteResult:
            return RouteResult(
                robot_id=robot_id,
                start_zone_id=start_zone_id,
                destination_zone_id=destination_zone_id,
                route=[],
                distance_meters=0.0,
                estimated_travel_seconds=0.0,
                route_available=False,
            )

        if (
            start_zone_id not in self._active_zone_ids
            or destination_zone_id not in self._active_zone_ids
        ):
            return unavailable()

        if start_zone_id == destination_zone_id:
            return RouteResult(
                robot_id=robot_id,
                start_zone_id=start_zone_id,
                destination_zone_id=destination_zone_id,
                route=[start_zone_id],
                distance_meters=0.0,
                estimated_travel_seconds=0.0,
                route_available=True,
            )

        # Dijkstra over (distance, travel_seconds); distance is the cost.
        best: dict[str, float] = {start_zone_id: 0.0}
        previous: dict[str, str] = {}
        travel_seconds: dict[str, float] = {start_zone_id: 0.0}
        queue: list[tuple[float, str]] = [(0.0, start_zone_id)]
        visited: set[str] = set()

        while queue:
            distance, zone_id = heapq.heappop(queue)
            if zone_id in visited:
                continue
            visited.add(zone_id)
            if zone_id == destination_zone_id:
                break
            for neighbor, edge_distance, edge_seconds in self._graph[zone_id]:
                candidate = distance + edge_distance
                if candidate < best.get(neighbor, float("inf")):
                    best[neighbor] = candidate
                    previous[neighbor] = zone_id
                    travel_seconds[neighbor] = travel_seconds[zone_id] + edge_seconds
                    heapq.heappush(queue, (candidate, neighbor))

        if destination_zone_id not in best:
            return unavailable()

        route = [destination_zone_id]
        while route[-1] != start_zone_id:
            route.append(previous[route[-1]])
        route.reverse()

        return RouteResult(
            robot_id=robot_id,
            start_zone_id=start_zone_id,
            destination_zone_id=destination_zone_id,
            route=route,
            distance_meters=round(best[destination_zone_id], 3),
            estimated_travel_seconds=round(travel_seconds[destination_zone_id], 3),
            route_available=True,
        )
