"""Multi-county zones: loading, assignment, rosters, and zone-scoped matching."""

import json

import pytest

from src.core.config import Settings
from src.core.models import GeoPoint, ResourceOffer, ResourceRequest, ResourceType
from src.core.store import CommunityStore
from src.core.zones import ZoneRegistry
from src.agents.strands_resource_matcher import heuristic_matches


AUSTIN = GeoPoint(lat=30.2764, lon=-97.7041)      # inside austin-east radius
ROUND_ROCK = GeoPoint(lat=30.51, lon=-97.68)      # inside round-rock radius
EL_PASO = GeoPoint(lat=31.76, lon=-106.49)        # inside neither


def _registry(tmp_path, zones: list[dict], captains=()) -> ZoneRegistry:
    path = tmp_path / "zones.json"
    path.write_text(json.dumps({"zones": zones}))
    settings = Settings(zones_file=path, captain_numbers=tuple(captains))
    return ZoneRegistry.load(settings)


TWO_ZONES = [
    {"key": "austin-east", "noaa_area": "TX", "center": {"lat": 30.272, "lon": -97.7}, "radius_km": 8,
     "captain_numbers": ["whatsapp:+15550000001"]},
    {"key": "round-rock", "noaa_area": "TX", "center": {"lat": 30.508, "lon": -97.679}, "radius_km": 10},
]


def test_missing_zones_file_gives_single_implicit_zone(tmp_path):
    settings = Settings(zones_file=tmp_path / "nope.json", noaa_area="OK", demo_mode=False,
                        captain_numbers=("whatsapp:+15559999999",))
    registry = ZoneRegistry.load(settings)
    assert list(registry.zones) == ["default"]
    assert registry.assign(AUSTIN) == "default"
    assert registry.captains_for("default") == ("whatsapp:+15559999999",)
    assert registry.noaa_areas() == ["OK"]


def test_demo_mode_falls_back_to_bundled_demo_zones(tmp_path):
    settings = Settings(zones_file=tmp_path / "nope.json", demo_mode=True)
    registry = ZoneRegistry.load(settings)
    assert set(registry.zones) == {"austin-east", "round-rock"}


def test_corrupt_zones_file_falls_back_to_single_zone(tmp_path):
    path = tmp_path / "zones.json"
    path.write_text("{broken")
    registry = ZoneRegistry.load(Settings(zones_file=path))
    assert list(registry.zones) == ["default"]


def test_duplicate_zone_keys_fall_back_to_single_zone(tmp_path):
    path = tmp_path / "zones.json"
    path.write_text(json.dumps({"zones": [
        {"key": "z1", "noaa_area": "TX"}, {"key": "z1", "noaa_area": "LA"},
    ]}))
    registry = ZoneRegistry.load(Settings(zones_file=path, demo_mode=False))
    assert list(registry.zones) == ["default"]


def test_noaa_areas_always_includes_configured_area(tmp_path):
    # A zones file must never stop the deployment from watching its own state.
    path = tmp_path / "zones.json"
    path.write_text(json.dumps({"zones": [
        {"key": "shreveport", "noaa_area": "LA", "center": {"lat": 32.5, "lon": -93.7}}]}))
    registry = ZoneRegistry.load(Settings(zones_file=path, noaa_area="OK"))
    assert registry.noaa_areas() == ["OK", "LA"]


def test_assignment_by_centroid_radius(tmp_path):
    registry = _registry(tmp_path, TWO_ZONES)
    assert registry.assign(AUSTIN) == "austin-east"
    assert registry.assign(ROUND_ROCK) == "round-rock"
    # outside every radius → default (first) zone
    assert registry.assign(EL_PASO) == "austin-east"
    assert registry.assign(None) == "austin-east"


def test_zone_roster_with_global_fallback(tmp_path):
    registry = _registry(tmp_path, TWO_ZONES, captains=["whatsapp:+15558888888"])
    assert registry.captains_for("austin-east") == ("whatsapp:+15550000001",)
    # zone without its own roster falls back to the global list
    assert registry.captains_for("round-rock") == ("whatsapp:+15558888888",)


def test_noaa_areas_deduped(tmp_path):
    registry = _registry(tmp_path, TWO_ZONES + [
        {"key": "shreveport", "noaa_area": "LA", "center": {"lat": 32.5, "lon": -93.7}, "radius_km": 10}])
    assert registry.noaa_areas() == ["TX", "LA"]


def test_matching_stays_within_zone(tmp_path):
    store = CommunityStore(tmp_path / "s.json")
    store.add_offer(ResourceOffer(id="off_rr", resource_type=ResourceType.GENERATOR,
                                  description="generator", zone="round-rock",
                                  location=ROUND_ROCK))
    store.add_request(ResourceRequest(id="req_atx", resource_type=ResourceType.MEDICAL,
                                      description="insulin refrigeration", urgency=5,
                                      zone="austin-east", location=AUSTIN))
    proposal = heuristic_matches(store)
    # compatible types, but different zones → no match, request escalated
    assert proposal.matches == []
    assert proposal.unmet_request_ids == ["req_atx"]


def test_pre_zones_default_entries_match_any_zone(tmp_path):
    # Entries stored before zones were enabled (zone='default') must not be
    # stranded when a zones file activates.
    store = CommunityStore(tmp_path / "s.json")
    store.add_offer(ResourceOffer(id="off_new", resource_type=ResourceType.GENERATOR,
                                  description="generator", zone="austin-east", location=AUSTIN))
    store.add_request(ResourceRequest(id="req_old", resource_type=ResourceType.MEDICAL,
                                      description="insulin refrigeration", urgency=5,
                                      zone="default", location=AUSTIN))
    proposal = heuristic_matches(store)
    assert len(proposal.matches) == 1
    assert proposal.matches[0].request_id == "req_old"


def test_pipeline_pings_zone_roster(tmp_path, monkeypatch):
    from src.orchestrator import ResqioPipeline

    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")

    zones_path = tmp_path / "zones.json"
    zones_path.write_text(json.dumps({"zones": [
        {"key": "austin-east", "noaa_area": "TX",
         "center": {"lat": 30.272, "lon": -97.7}, "radius_km": 8,
         "captain_numbers": ["whatsapp:+15550000001", "whatsapp:+15550000002"]},
    ]}))
    settings = Settings(store_path=tmp_path / "s.json", demo_mode=True, zones_file=zones_path)
    pipeline = ResqioPipeline(settings=settings, store=CommunityStore(tmp_path / "s.json"))

    pipeline.handle_inbound("OFFER: generator available", phone="+1", name="M", location=AUSTIN)
    pipeline.handle_inbound("HELP: insulin needs refrigeration urgent", phone="+2", name="A", location=AUSTIN)
    report = pipeline.run_cycle()

    assert len(report.new_matches) == 1
    # both zone captains pinged (console channel in demo mode, but addressed to the roster)
    assert [p.captain_phone for p in report.pings] == ["whatsapp:+15550000001", "whatsapp:+15550000002"]
    offer = pipeline.store.offers[report.new_matches[0].offer_id]
    assert offer.zone == "austin-east"
    # rosters are private: the unauthenticated dashboard payload has no numbers
    for zone in pipeline.status()["zones"]:
        assert "captain_numbers" not in zone
