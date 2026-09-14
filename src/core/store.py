"""CommunityStore - the shared board of offers, requests, and matches.

In-memory with JSON snapshot persistence so the daemon survives restarts and
the AgentCore runtime can rehydrate between invocations. Not a database on
purpose: a community deployment must run on a laptop in a shelter.

Single-writer by design: exactly ONE process may own a store file (the
AgentCore runtime, the webhook server with its embedded poll loop, or the
standalone daemon). The RLock covers threads within that process; it cannot
arbitrate between processes.

Match lifecycle is a guarded state machine - a captain's stale PASS must
never reopen a delivery someone already accepted:

    proposed → pending_approval → approved → delivered
                     ↘ declined / expired (reopens both sides)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path

from .models import (
    EntryStatus,
    Match,
    MatchStatus,
    ResourceOffer,
    ResourceRequest,
)

logger = logging.getLogger("resqio.store")


class InvalidTransition(ValueError):
    """Raised when a match status change is not a legal lifecycle step."""


_ALLOWED_TRANSITIONS: dict[MatchStatus, set[MatchStatus]] = {
    MatchStatus.PROPOSED: {MatchStatus.PENDING_APPROVAL, MatchStatus.DECLINED, MatchStatus.EXPIRED},
    MatchStatus.PENDING_APPROVAL: {MatchStatus.APPROVED, MatchStatus.DECLINED, MatchStatus.EXPIRED},
    MatchStatus.APPROVED: {MatchStatus.DELIVERED, MatchStatus.EXPIRED},
    MatchStatus.DECLINED: set(),
    MatchStatus.DELIVERED: set(),
    MatchStatus.EXPIRED: set(),
}


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
        """Persist a match and mark both sides as tentatively taken.

        The OPEN re-check happens *inside* the lock: two concurrent cycles
        that both saw the same open offer must not both book it.
        """
        with self._lock:
            offer = self.offers.get(match.offer_id)
            request = self.requests.get(match.request_id)
            if offer is None:
                raise KeyError(f"unknown offer id {match.offer_id!r}")
            if request is None:
                raise KeyError(f"unknown request id {match.request_id!r}")
            if offer.status != EntryStatus.OPEN:
                raise InvalidTransition(f"offer {offer.id} is no longer open ({offer.status.value})")
            if request.status != EntryStatus.OPEN:
                raise InvalidTransition(f"request {request.id} is no longer open ({request.status.value})")
            self.matches[match.id] = match
            offer.status = EntryStatus.MATCHED
            request.status = EntryStatus.MATCHED
            self._save()
        return match

    def get_match(self, match_id: str) -> Match | None:
        with self._lock:
            return self.matches.get(match_id)

    def pending_matches(self) -> list[Match]:
        with self._lock:
            return [m for m in self.matches.values() if m.status == MatchStatus.PENDING_APPROVAL]

    def awaiting_action_matches(self) -> list[Match]:
        """Matches still in a non-terminal, human-actionable state."""
        with self._lock:
            return [
                m for m in self.matches.values()
                if m.status in (MatchStatus.PROPOSED, MatchStatus.PENDING_APPROVAL)
            ]

    def set_match_status(self, match_id: str, status: MatchStatus) -> Match:
        with self._lock:
            match = self.matches.get(match_id)
            if match is None:
                raise KeyError(f"unknown match id {match_id!r}")
            if status not in _ALLOWED_TRANSITIONS[match.status]:
                raise InvalidTransition(
                    f"match {match_id} is {match.status.value}; cannot become {status.value}"
                )
            match.status = status
            # A declined/expired match frees both sides for re-matching; a
            # delivered one closes them. Only touch entries still MATCHED -
            # entries closed or re-booked by another match are not ours.
            if status in (MatchStatus.DECLINED, MatchStatus.EXPIRED):
                self._release_entries(match, EntryStatus.OPEN)
            elif status == MatchStatus.DELIVERED:
                self._release_entries(match, EntryStatus.CLOSED)
            self._save()
            return match

    def _release_entries(self, match: Match, new_status: EntryStatus) -> None:
        offer = self.offers.get(match.offer_id)
        if offer is not None and offer.status == EntryStatus.MATCHED:
            offer.status = new_status
        request = self.requests.get(match.request_id)
        if request is not None and request.status == EntryStatus.MATCHED:
            request.status = new_status

    def clear(self) -> None:
        """Wipe the board (demo resets only)."""
        with self._lock:
            self.offers.clear()
            self.requests.clear()
            self.matches.clear()
            self._save()

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
        with open(tmp, "w") as fh:
            fh.write(json.dumps(payload, indent=2))
            fh.flush()
            os.fsync(fh.fileno())  # a crash mid-crisis must not lose the board
        tmp.replace(self._path)

    def _load(self) -> None:
        try:
            raw = json.loads(self._path.read_text())
        except Exception as exc:  # noqa: BLE001 - a corrupt file must not brick startup
            quarantine = self._path.with_name(f"{self._path.name}.corrupt-{int(time.time())}")
            self._path.replace(quarantine)
            logger.error(
                "store file %s is corrupt (%s); quarantined to %s and starting empty",
                self._path, exc, quarantine,
            )
            return
        self.offers = self._validate_records(raw.get("offers", []), ResourceOffer)
        self.requests = self._validate_records(raw.get("requests", []), ResourceRequest)
        self.matches = self._validate_records(raw.get("matches", []), Match)

    @staticmethod
    def _validate_records(records: list[dict], model) -> dict:
        loaded = {}
        for record in records:
            try:
                item = model.model_validate(record)
                loaded[item.id] = item
            except Exception as exc:  # noqa: BLE001 - one bad record must not discard the rest
                logger.error("skipping invalid %s record %s (%s)", model.__name__, record.get("id"), exc)
        return loaded
