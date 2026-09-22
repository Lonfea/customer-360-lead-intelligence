from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log


@dataclass(frozen=True)
class CustomerEvent:
    event_id: str
    email: str
    phone: str | None
    company: str
    region: str
    event_type: str
    occurred_at: datetime
    analytics_consent: bool
    value: float = 0

    def identity_key(self) -> str:
        email = self.email.strip().lower()
        phone = "".join(ch for ch in (self.phone or "") if ch.isdigit())
        return f"{email}|{phone}" if phone else email


EVENT_WEIGHTS = {"page_view": 0.3, "content_download": 1.2, "webinar": 1.7, "demo_request": 3.0, "email_click": 0.8}
MODEL = {"bias": -2.1, "engagement": 0.65, "recency": 0.9, "intent": 1.15, "company_value": 0.45}


class LeadIntelligence:
    def __init__(self, events: Iterable[CustomerEvent], now: datetime | None = None):
        self.events = tuple(events)
        self.now = now or datetime.now(UTC)
        if not self.events:
            raise ValueError("at least one event is required")
        if len({event.event_id for event in self.events}) != len(self.events):
            raise ValueError("event_id must be unique")

    def profiles(self) -> dict[str, list[CustomerEvent]]:
        result: dict[str, list[CustomerEvent]] = {}
        for event in self.events:
            result.setdefault(event.identity_key(), []).append(event)
        return result

    def features(self, identity_key: str) -> dict[str, float]:
        events = [event for event in self.profiles().get(identity_key, []) if event.analytics_consent]
        if not events:
            return {"engagement": 0, "recency": 0, "intent": 0, "company_value": 0}
        decayed = []
        for event in events:
            age_days = max((self.now - event.occurred_at).total_seconds() / 86_400, 0)
            decayed.append(EVENT_WEIGHTS.get(event.event_type, 0) * exp(-age_days / 30))
        last_age = min(max((self.now - event.occurred_at).total_seconds() / 86_400, 0) for event in events)
        return {
            "engagement": min(sum(decayed) / 4, 1),
            "recency": exp(-last_age / 14),
            "intent": min(sum(event.event_type in {"demo_request", "webinar"} for event in events) / 2, 1),
            "company_value": min(max(event.value for event in events) / 100_000, 1),
        }

    def score(self, identity_key: str, threshold: float = 0.65) -> dict[str, object]:
        if identity_key not in self.profiles():
            raise KeyError(identity_key)
        features = self.features(identity_key)
        contributions = {name: round(features[name] * MODEL[name], 4) for name in features}
        logit = MODEL["bias"] + sum(contributions.values())
        probability = 1 / (1 + exp(-logit))
        event = self.profiles()[identity_key][0]
        qualified = probability >= threshold
        route = {"EMEA": "emea-enterprise", "AMER": "amer-enterprise", "APAC": "apac-enterprise"}.get(event.region, "global-queue")
        return {
            "identity_key": identity_key,
            "probability": round(probability, 4),
            "qualified": qualified,
            "threshold": threshold,
            "route": route if qualified else "nurture",
            "features": {key: round(value, 4) for key, value in features.items()},
            "contributions": contributions,
        }

    def funnel(self) -> dict[str, object]:
        profiles = self.profiles()
        stages = {"identified": len(profiles), "engaged": 0, "intent": 0, "qualified": 0}
        for key in profiles:
            features = self.features(key)
            stages["engaged"] += features["engagement"] > 0
            stages["intent"] += features["intent"] > 0
            stages["qualified"] += self.score(key)["qualified"]
        rates = {f"{left}_to_{right}": round(stages[right] / stages[left], 4) if stages[left] else 0 for left, right in (("identified", "engaged"), ("engaged", "intent"), ("intent", "qualified"))}
        return {"stages": stages, "conversion_rates": rates}

    @staticmethod
    def population_stability_index(expected: list[float], actual: list[float]) -> float:
        if len(expected) != len(actual) or not expected:
            raise ValueError("distributions must have equal, non-zero length")
        if any(value <= 0 for value in expected + actual):
            raise ValueError("all proportions must be positive")
        return round(sum((a - e) * log(a / e) for e, a in zip(expected, actual)), 6)


def demo_engine() -> LeadIntelligence:
    now = datetime(2026, 9, 22, tzinfo=UTC)
    events = [
        CustomerEvent("e1", "ada@example.com", "+49 111", "Auto AG", "EMEA", "page_view", datetime(2026, 9, 20, tzinfo=UTC), True, 90_000),
        CustomerEvent("e2", "ADA@example.com ", "+49-111", "Auto AG", "EMEA", "demo_request", datetime(2026, 9, 21, tzinfo=UTC), True, 90_000),
        CustomerEvent("e3", "lin@example.com", None, "Energy SE", "EMEA", "content_download", datetime(2026, 8, 15, tzinfo=UTC), True, 45_000),
        CustomerEvent("e4", "sam@example.com", None, "IoT Inc", "AMER", "webinar", datetime(2026, 9, 18, tzinfo=UTC), False, 60_000),
    ]
    return LeadIntelligence(events, now)

