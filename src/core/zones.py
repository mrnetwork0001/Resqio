"""Zones - multi-county deployments with per-zone captain rosters.

A zone is a service area: a name, the NOAA area to watch, its associated
county FIPS codes (reserved for outage-to-zone attribution), a centroid +
radius for assigning inbound offers/requests, and its own volunteer
captain roster.

Zones load from a JSON file (``RESQIO_ZONES_FILE``, default
``data/zones.json``); demo mode falls back to the bundled demo zones.
With no file present, Resqio runs exactly as before: one implicit zone
built from the flat settings - fully backwards compatible. Entries with
zone ``"default"`` (including anything stored before zones were enabled)
match against any zone.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from .config import Settings
from .geo import haversine_km
from .models import GeoPoint

logger = logging.getLogger("resqio.zones")

DEFAULT_ZONE_KEY = "default"


class Zone(BaseModel):
    key: str
    name: str = ""
    noaa_area: str = "TX"
    fips_codes: list[str] = Field(default_factory=list)
    captain_numbers: list[str] = Field(default_factory=list)
    center: GeoPoint | None = None
    radius_km: float = Field(default=15.0, gt=0)


class ZoneRegistry:
    def __init__(
        self,
        zones: list[Zone],
        fallback_captains: tuple[str, ...] = (),
        fallback_noaa_area: str = "",
    ) -> None:
        if not zones:
            raise ValueError("ZoneRegistry needs at least one zone")
        self.zones: dict[str, Zone] = {z.key: z for z in zones}
        self.default_key = zones[0].key
        self._fallback_captains = fallback_captains
        self._fallback_noaa_area = fallback_noaa_area

    @classmethod
    def load(cls, settings: Settings) -> "ZoneRegistry":
        """Load zones from the configured file, or build the single implicit zone.

        Lookup order: the configured ``zones_file``; in demo mode, the bundled
        demo zones; otherwise one implicit zone from the flat settings.
        """
        candidates = [settings.zones_file]
        if settings.demo_mode:
            candidates.append(settings.demo_dir / "zones.json")
        for path in candidates:
            if path is None or not path.exists():
                continue
            try:
                raw = json.loads(path.read_text())
                zones = [Zone.model_validate(z) for z in raw.get("zones", [])]
                keys = [z.key for z in zones]
                if len(keys) != len(set(keys)):
                    raise ValueError(f"duplicate zone key(s): {sorted({k for k in keys if keys.count(k) > 1})}")
                if not zones:
                    logger.warning("zones file %s has no zones; trying next source", path)
                    continue
                # A non-first zone without a centroid can never be assigned an
                # entry - its roster would silently never be pinged.
                for zone in zones[1:]:
                    if zone.center is None:
                        logger.warning(
                            "zone %r has no center: entries can never be assigned to it "
                            "and its captains will not be pinged", zone.key,
                        )
                logger.info("loaded %d zone(s) from %s", len(zones), path)
                return cls(
                    zones,
                    fallback_captains=settings.captain_numbers,
                    fallback_noaa_area=settings.noaa_area,
                )
            except Exception as exc:  # noqa: BLE001 - a bad zones file must not stop monitoring
                logger.error("failed to load zones file %s (%s); using single-zone mode", path, exc)
                break
        implicit = Zone(
            key=DEFAULT_ZONE_KEY,
            name="Service area",
            noaa_area=settings.noaa_area,
            captain_numbers=list(settings.captain_numbers),
        )
        return cls(
            [implicit],
            fallback_captains=settings.captain_numbers,
            fallback_noaa_area=settings.noaa_area,
        )

    # ── Assignment & lookup ──────────────────────────────────────────

    def assign(self, location: GeoPoint | None) -> str:
        """Zone for an inbound offer/request: nearest centroid within radius."""
        if location is None:
            return self.default_key
        best: tuple[float, str] | None = None
        for zone in self.zones.values():
            if zone.center is None:
                continue
            distance = haversine_km(location, zone.center)
            if distance <= zone.radius_km and (best is None or distance < best[0]):
                best = (distance, zone.key)
        return best[1] if best else self.default_key

    def captains_for(self, zone_key: str) -> tuple[str, ...]:
        """The zone's roster, falling back to the global captain list."""
        zone = self.zones.get(zone_key)
        if zone is not None and zone.captain_numbers:
            return tuple(zone.captain_numbers)
        return self._fallback_captains

    def noaa_areas(self) -> list[str]:
        """Unique NOAA areas across zones, always including the configured
        fallback area - a zones file must never silently stop the deployment
        from watching its own state (one comma-joined API query)."""
        seen: list[str] = []
        if self._fallback_noaa_area:
            seen.append(self._fallback_noaa_area)
        for zone in self.zones.values():
            if zone.noaa_area and zone.noaa_area not in seen:
                seen.append(zone.noaa_area)
        return seen

    def name_for(self, zone_key: str) -> str:
        zone = self.zones.get(zone_key)
        return zone.name or zone.key if zone else zone_key
