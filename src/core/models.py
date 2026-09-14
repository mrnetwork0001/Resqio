"""Shared data models for Resqio.

Every agent, feed, and integration speaks these types. The structured-output
models at the bottom are what the Strands agents return via
``Agent.structured_output`` so LLM reasoning always lands in validated shapes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ────────────────────────────────────────────────────────────


class Severity(str, Enum):
    """NWS alert severity ladder (api.weather.gov vocabulary)."""

    EXTREME = "Extreme"
    SEVERE = "Severe"
    MODERATE = "Moderate"
    MINOR = "Minor"
    UNKNOWN = "Unknown"

    @property
    def rank(self) -> int:
        order = [Severity.UNKNOWN, Severity.MINOR, Severity.MODERATE, Severity.SEVERE, Severity.EXTREME]
        return order.index(self)


class CrisisSource(str, Enum):
    NOAA = "noaa"
    GRID = "grid"


class ResourceType(str, Enum):
    GENERATOR = "generator"
    ICE = "ice"
    FOOD = "food"
    WATER = "water"
    MEDICAL = "medical"
    SHELTER = "shelter"
    TRANSPORT = "transport"
    OTHER = "other"


class Vulnerability(str, Enum):
    ELDERLY = "elderly"
    INFANT = "infant"
    MEDICAL_REFRIGERATION = "medical_refrigeration"
    MOBILITY = "mobility"
    NONE = "none"


class EntryStatus(str, Enum):
    OPEN = "open"
    MATCHED = "matched"
    CLOSED = "closed"


class MatchStatus(str, Enum):
    PROPOSED = "proposed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DECLINED = "declined"
    DELIVERED = "delivered"
    EXPIRED = "expired"


# ── Geography ────────────────────────────────────────────────────────


class GeoPoint(BaseModel):
    lat: float
    lon: float


# ── Crisis events (from feeds) ───────────────────────────────────────


class CrisisEvent(BaseModel):
    id: str = Field(default_factory=lambda: _new_id("evt"))
    external_id: str = ""  # NWS alert id - dedupe key across polls
    source: CrisisSource
    event: str  # e.g. "Excessive Heat Warning", "Feeder outage"
    severity: Severity = Severity.UNKNOWN
    headline: str = ""
    description: str = ""
    area_desc: str = ""
    fips_codes: list[str] = Field(default_factory=list)  # SAME/FIPS county codes
    effective: datetime | None = None
    expires: datetime | None = None  # hazard end (NWS `ends`, falling back to `expires`)
    customers_affected: int | None = None  # grid outages only

    @property
    def is_active(self) -> bool:
        if self.expires is None:
            return True
        expires = self.expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires > utcnow()


# ── Community board (from inbound SMS) ───────────────────────────────


class ResourceOffer(BaseModel):
    """A neighbor's spare capacity: 'Generator available in Sector 4'."""

    id: str = Field(default_factory=lambda: _new_id("off"))
    contact_name: str = "neighbor"
    phone: str = ""
    resource_type: ResourceType = ResourceType.OTHER
    description: str = ""
    quantity: int = 1
    location: GeoPoint | None = None
    address: str = ""
    zone: str = "default"
    status: EntryStatus = EntryStatus.OPEN
    created_at: datetime = Field(default_factory=utcnow)


class ResourceRequest(BaseModel):
    """An urgent need: 'Insulin ice needed at 42 Maple St'."""

    id: str = Field(default_factory=lambda: _new_id("req"))
    contact_name: str = "resident"
    phone: str = ""
    resource_type: ResourceType = ResourceType.OTHER
    description: str = ""
    urgency: int = Field(default=3, ge=1, le=5)  # 5 = life-safety
    vulnerability: Vulnerability = Vulnerability.NONE
    location: GeoPoint | None = None
    address: str = ""
    zone: str = "default"
    status: EntryStatus = EntryStatus.OPEN
    created_at: datetime = Field(default_factory=utcnow)


# ── Matching & routing ───────────────────────────────────────────────


class RouteInfo(BaseModel):
    distance_km: float = 0.0
    est_minutes: float = 0.0
    hazards: list[str] = Field(default_factory=list)
    instructions: str = ""


class Match(BaseModel):
    id: str = Field(default_factory=lambda: _new_id("mat"))
    offer_id: str
    request_id: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = ""
    distance_km: float | None = None
    status: MatchStatus = MatchStatus.PROPOSED
    route: RouteInfo | None = None
    created_at: datetime = Field(default_factory=utcnow)


class ApprovalPing(BaseModel):
    match_id: str
    captain_phone: str
    message_body: str
    channel: str = "whatsapp"  # "whatsapp" | "sms" | "console"
    sent_at: datetime = Field(default_factory=utcnow)


# ── Structured-output models (returned by Strands agents) ────────────


class CrisisAssessment(BaseModel):
    """StrandsGridMonitor verdict on the current feed snapshot."""

    is_crisis: bool = Field(description="True if any event warrants activating community logistics")
    crisis_level: int = Field(ge=0, le=5, description="0 = calm, 5 = extreme life-safety emergency")
    active_hazards: list[str] = Field(default_factory=list, description="Short hazard labels, e.g. 'Excessive Heat Warning'")
    affected_areas: list[str] = Field(default_factory=list, description="Human-readable affected areas")
    summary: str = Field(description="Two-sentence situation report for volunteer captains")


class MatchCandidate(BaseModel):
    """One offer→request pairing proposed by StrandsResourceMatcher."""

    offer_id: str = Field(description="id of the ResourceOffer to dispatch")
    request_id: str = Field(description="id of the ResourceRequest it serves")
    score: float = Field(ge=0.0, le=1.0, description="Confidence that this pairing is the best use of the offer")
    rationale: str = Field(description="One sentence: why this pairing, citing urgency/vulnerability/distance")


class MatchProposal(BaseModel):
    matches: list[MatchCandidate] = Field(default_factory=list)
    unmet_request_ids: list[str] = Field(default_factory=list, description="Open requests no offer could serve")


MessageKind = Literal["offer", "request", "accept", "pass", "delivered", "unknown"]
_MESSAGE_KINDS = {"offer", "request", "accept", "pass", "delivered", "unknown"}


class ParsedInboundMessage(BaseModel):
    """StrandsResourceMatcher's reading of a raw community SMS."""

    kind: MessageKind = Field(description="'offer' | 'request' | 'accept' | 'pass' | 'delivered' | 'unknown'")
    resource_type: ResourceType = ResourceType.OTHER
    description: str = ""
    urgency: int = Field(default=3, ge=1, le=5)
    vulnerability: Vulnerability = Vulnerability.NONE
    address: str = ""
    match_id: str = Field(default="", description="For accept/pass/delivered replies: the match id referenced")

    @field_validator("kind", mode="before")
    @classmethod
    def _normalize_kind(cls, value: object) -> str:
        # LLM output like "Offer" or "REPLY" must fail into the safe branch,
        # never drop a community message on a capitalization mismatch.
        if isinstance(value, str) and value.strip().lower() in _MESSAGE_KINDS:
            return value.strip().lower()
        return "unknown"

    @field_validator("match_id", mode="before")
    @classmethod
    def _normalize_match_id(cls, value: object) -> str:
        return value.strip().lower() if isinstance(value, str) else ""


class RoutePlan(BaseModel):
    """StrandsVolunteerRouter output for an approved candidate match."""

    distance_km: float = Field(ge=0.0)
    est_minutes: float = Field(ge=0.0)
    hazards: list[str] = Field(default_factory=list, description="Active hazards along the way the volunteer must know")
    instructions: str = Field(description="Short safe-transit guidance for the volunteer")
    ping_message: str = Field(description="The exact WhatsApp/SMS text to send the captain, ending with reply options ACCEPT <id> / PASS <id>")
