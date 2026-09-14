from __future__ import annotations

import pytest

from src.core.config import Settings
from src.core.models import GeoPoint, ResourceOffer, ResourceRequest, ResourceType, Vulnerability
from src.core.store import CommunityStore


@pytest.fixture(autouse=True)
def _no_real_side_effects(monkeypatch):
    """.env may hold real Twilio and AWS credentials. Tests must never send a
    WhatsApp message or call Bedrock, so strip them for every test."""
    for var in (
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "RESQIO_CAPTAIN_NUMBERS", "RESQIO_REAL_PINGS",
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


@pytest.fixture()
def settings(tmp_path):
    return Settings(store_path=tmp_path / "store.json", demo_mode=True)


@pytest.fixture()
def store(tmp_path) -> CommunityStore:
    return CommunityStore(tmp_path / "store.json")


@pytest.fixture()
def seeded_store(store: CommunityStore) -> CommunityStore:
    store.add_offer(
        ResourceOffer(
            id="off_generator1", contact_name="Marcus", phone="+15125550101",
            resource_type=ResourceType.GENERATOR, description="7500W dual fuel generator",
            location=GeoPoint(lat=30.2795, lon=-97.6923), address="Springdale Rd",
        )
    )
    store.add_offer(
        ResourceOffer(
            id="off_ice1", contact_name="Rosa", phone="+15125550102",
            resource_type=ResourceType.ICE, description="6 bags of ice and cooler space",
            location=GeoPoint(lat=30.2801, lon=-97.7137), address="MLK & Chestnut",
        )
    )
    store.add_request(
        ResourceRequest(
            id="req_insulin1", contact_name="Amara", phone="+15125550103",
            resource_type=ResourceType.MEDICAL, description="insulin needs refrigeration, power out",
            urgency=5, vulnerability=Vulnerability.MEDICAL_REFRIGERATION,
            location=GeoPoint(lat=30.2764, lon=-97.7041), address="42 Maple St",
        )
    )
    store.add_request(
        ResourceRequest(
            id="req_infant1", contact_name="Dan", phone="+15125550104",
            resource_type=ResourceType.SHELTER, description="family with 3-month-old, no power, need cooling",
            urgency=4, vulnerability=Vulnerability.INFANT,
            location=GeoPoint(lat=30.2618, lon=-97.6889), address="Govalle",
        )
    )
    return store
