from datetime import UTC, datetime

import pytest

from lead_intel.engine import CustomerEvent, LeadIntelligence, demo_engine


def test_identity_resolution_normalizes_email_and_phone():
    engine = demo_engine()
    assert len(engine.profiles()) == 3
    assert len(engine.profiles()["ada@example.com|49111"]) == 2


def test_consent_exclusion_and_explanations():
    engine = demo_engine()
    sam = engine.score("sam@example.com")
    assert sam["features"] == {"engagement": 0, "recency": 0, "intent": 0, "company_value": 0}
    assert set(sam["contributions"]) == set(sam["features"])


def test_funnel_and_drift_monitor():
    engine = demo_engine()
    assert engine.funnel()["stages"]["identified"] == 3
    assert engine.population_stability_index([0.5, 0.5], [0.4, 0.6]) > 0
    with pytest.raises(ValueError):
        engine.population_stability_index([1], [0.5, 0.5])


def test_duplicate_event_rejected():
    event = CustomerEvent("e", "a@b.com", None, "A", "EMEA", "page_view", datetime.now(UTC), True)
    with pytest.raises(ValueError, match="unique"):
        LeadIntelligence([event, event])

