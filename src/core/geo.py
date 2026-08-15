"""Lightweight geospatial helpers (no external GIS dependency)."""

from __future__ import annotations

import math

from .models import GeoPoint

EARTH_RADIUS_KM = 6371.0088

# Conservative average speed for a volunteer driving through a disaster zone.
CRISIS_DRIVING_KMH = 30.0


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """Great-circle distance between two points in kilometres."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def estimate_transit_minutes(distance_km: float, speed_kmh: float = CRISIS_DRIVING_KMH) -> float:
    """Door-to-door estimate at crisis-condition speeds, incl. 5 min load/unload."""
    if distance_km < 0:
        raise ValueError("distance_km must be non-negative")
    return round(distance_km / speed_kmh * 60 + 5, 1)
