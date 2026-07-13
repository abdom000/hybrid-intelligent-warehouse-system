import pytest

from hybrid_warehouse.routing import RoutePlanner, RoutePlanningError
from hybrid_warehouse.schemas import WarehousePath, WarehouseZone


def zone(zone_id: str, *, active: bool = True) -> WarehouseZone:
    return WarehouseZone(zone_id=zone_id, name=f"Zone {zone_id}", active=active)


def path(
    path_id: str,
    start: str,
    end: str,
    distance: float,
    *,
    active: bool = True,
) -> WarehousePath:
    return WarehousePath(
        path_id=path_id,
        start_zone_id=start,
        end_zone_id=end,
        distance_meters=distance,
        estimated_travel_seconds=distance * 0.85,
        active=active,
    )


@pytest.fixture()
def planner() -> RoutePlanner:
    zones = [zone("A"), zone("B"), zone("C"), zone("D"), zone("F", active=False)]
    paths = [
        path("P1", "A", "C", 20.0),
        path("P2", "C", "A", 20.0),
        path("P3", "C", "B", 25.0),
        path("P4", "B", "C", 25.0),
        path("P5", "A", "B", 60.0),
        path("P6", "C", "D", 30.0),
        path("P7", "D", "F", 12.0),
    ]
    return RoutePlanner(zones=zones, paths=paths)


def test_multi_hop_route_is_shorter_than_direct_edge(planner):
    result = planner.plan_route(robot_id="R1", start_zone_id="A", destination_zone_id="B")
    assert result.route_available
    assert result.route == ["A", "C", "B"]
    assert result.distance_meters == 45.0


def test_same_zone_route_has_zero_distance(planner):
    result = planner.plan_route(robot_id="R1", start_zone_id="A", destination_zone_id="A")
    assert result.route_available
    assert result.route == ["A"]
    assert result.distance_meters == 0.0


def test_route_to_inactive_zone_is_unavailable(planner):
    result = planner.plan_route(robot_id="R1", start_zone_id="A", destination_zone_id="F")
    assert not result.route_available
    assert result.route == []


def test_route_without_connecting_paths_is_unavailable(planner):
    # D has an outgoing edge only towards inactive F, and no edge back to C.
    result = planner.plan_route(robot_id="R1", start_zone_id="D", destination_zone_id="A")
    assert not result.route_available


def test_inactive_path_is_excluded():
    zones = [zone("A"), zone("B")]
    paths = [path("P1", "A", "B", 10.0, active=False)]
    planner = RoutePlanner(zones=zones, paths=paths)
    result = planner.plan_route(robot_id="R1", start_zone_id="A", destination_zone_id="B")
    assert not result.route_available


def test_unknown_zone_raises(planner):
    with pytest.raises(RoutePlanningError):
        planner.plan_route(robot_id="R1", start_zone_id="A", destination_zone_id="X")


def test_travel_seconds_accumulate_along_route(planner):
    result = planner.plan_route(robot_id="R1", start_zone_id="A", destination_zone_id="B")
    assert result.estimated_travel_seconds == pytest.approx(45.0 * 0.85)
