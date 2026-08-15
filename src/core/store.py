"""CommunityStore — the shared board of offers, requests, and matches.

In-memory with JSON snapshot persistence so the daemon survives restarts and
the AgentCore runtime can rehydrate between invocations. Not a database on
purpose: a community deployment must run on a laptop in a shelter.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from .models import (
    EntryStatus,
    Match,
    MatchStatus,
    ResourceOffer,
    ResourceRequest,
)


class CommunityStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._lock = threading.RLock()
        self.offers: dict[str, ResourceOffer] = {}
        self.requests: dict[str, ResourceRequest] = {}
        self.matches: dict[str, Match] = {}
        if path is not None and path.exists():
            self._load()

    # ── Offers / requests ────────────────────────────────────────────

    def add_offer(self, offer: ResourceOffer) -> ResourceOffer:
        with self._lock:
            self.offers[offer.id] = offer
            self._save()
        return offer

    def add_request(self, request: ResourceRequest) -> ResourceRequest:
        with self._lock:
            self.requests[request.id] = request
            self._save()
        return request

    def open_offers(self) -> list[ResourceOffer]:
        with self._lock:
            return [o for o in self.offers.values() if o.status == EntryStatus.OPEN]

    def open_requests(self) -> list[ResourceRequest]:
        with self._lock:
            reqs = [r for r in self.requests.values() if r.status == EntryStatus.OPEN]
            return sorted(reqs, key=lambda r: r.urgency, reverse=True)

    # ── Matches ──────────────────────────────────────────────────────

    def record_match(self, match: Match) -> Match:
        """Persist a match and mark both sides as tentatively taken."""
        with self._lock:
            if match.offer_id not in self.offers:
                raise KeyError(f"unknown offer id {match.offer_id!r}")
            if match.request_id not in self.requests:
                raise KeyError(f"unknown request id {match.request_id!r}")
            self.matches[match.id] = match
            self.offers[match.offer_id].status = EntryStatus.MATCHED
            self.requests[match.request_id].status = EntryStatus.MATCHED
            self._save()
        return match

    def get_match(self, match_id: str) -> Match | None:
        with self._lock:
            return self.matches.get(match_id)

    def pending_matches(self) -> list[Match]:
        with self._lock:
            return [m for m in self.matches.values() if m.status == MatchStatus.PENDING_APPROVAL]

    def set_match_status(self, match_id: str, status: MatchStatus) -> Match:
        with self._lock:
            match = self.matches.get(match_id)
            if match is None:
                raise KeyError(f"unknown match id {match_id!r}")
            match.status = status
            # A declined/expired match frees both sides for re-matching.
            if status in (MatchStatus.DECLINED, MatchStatus.EXPIRED):
                if match.offer_id in self.offers:
                    self.offers[match.offer_id].status = EntryStatus.OPEN
                if match.request_id in self.requests:
                    self.requests[match.request_id].status = EntryStatus.OPEN
            elif status == MatchStatus.DELIVERED:
                if match.offer_id in self.offers:
                    self.offers[match.offer_id].status = EntryStatus.CLOSED
                if match.request_id in self.requests:
                    self.requests[match.request_id].status = EntryStatus.CLOSED
            self._save()
            return match

    # ── Persistence ──────────────────────────────────────────────────

    def _save(self) -> None:
        if self._path is None:
            return
        payload = {
            "offers": [o.model_dump(mode="json") for o in self.offers.values()],
            "requests": [r.model_dump(mode="json") for r in self.requests.values()],
            "matches": [m.model_dump(mode="json") for m in self.matches.values()],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(self._path)

    def _load(self) -> None:
        raw = json.loads(self._path.read_text())
        self.offers = {d["id"]: ResourceOffer.model_validate(d) for d in raw.get("offers", [])}
        self.requests = {d["id"]: ResourceRequest.model_validate(d) for d in raw.get("requests", [])}
        self.matches = {d["id"]: Match.model_validate(d) for d in raw.get("matches", [])}
