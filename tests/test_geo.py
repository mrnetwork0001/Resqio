import math

import pytest

from src.core.geo import estimate_transit_minutes, haversine_km
from src.core.models import GeoPoint


def test_haversine_zero_distance():
    p = GeoPoint(lat=30.2672, lon=-97.7431)
    assert haversine_km(p, p) == 0.0


def test_haversine_known_distance():
    # Austin Capitol → Dallas City Hall ≈ 293 km great-circle
    austin = GeoPoint(lat=30.2747, lon=-97.7404)
    dallas = GeoPoint(lat=32.7767, lon=-96.7970)
    assert math.isclose(haversine_km(austin, dallas), 293, rel_tol=0.03)


def test_haversine_neighborhood_scale():
    a = GeoPoint(lat=30.2795, lon=-97.6923)
    b = GeoPoint(lat=30.2764, lon=-97.7041)
    assert 0.5 < haversine_km(a, b) < 2.5


def test_transit_estimate_includes_loading_buffer():
    assert estimate_transit_minutes(0) == 5.0
    assert estimate_transit_minutes(30) == 65.0  # 30 km @ 30 km/h + 5 min


def test_transit_estimate_rejects_negative():
    with pytest.raises(ValueError):
        estimate_transit_minutes(-1)
