"""Tests for the rule-based safety classification system.

Validates the FDA FAERS adverse event classification logic without
requiring any external API calls.
"""

import pytest
from backend.agents.safety_checker import _classify_event, HIGH_RISK_TERMS


class TestEventClassification:
    """Unit tests for _classify_event — the core safety classification function."""

    def test_death_is_high_risk(self):
        is_risky, organs = _classify_event("death")
        assert is_risky is True

    def test_cardiac_failure_detected(self):
        is_risky, organs = _classify_event("cardiac failure")
        assert is_risky is True
        assert "heart" in organs

    def test_hepatic_failure_detected(self):
        is_risky, organs = _classify_event("hepatic failure")
        assert is_risky is True
        assert "liver" in organs

    def test_renal_failure_detected(self):
        is_risky, organs = _classify_event("renal failure")
        assert is_risky is True
        assert "kidney" in organs

    def test_benign_event_is_not_high_risk(self):
        is_risky, organs = _classify_event("headache")
        assert is_risky is False

    def test_nausea_is_not_high_risk(self):
        is_risky, organs = _classify_event("nausea")
        assert is_risky is False
        assert organs == []

    def test_case_insensitive(self):
        is_risky, _ = _classify_event("CARDIAC ARREST")
        assert is_risky is True

    def test_stevens_johnson(self):
        is_risky, _ = _classify_event("Stevens-Johnson syndrome")
        assert is_risky is True

    def test_pulmonary_event_organ(self):
        _, organs = _classify_event("pulmonary embolism")
        assert "lungs" in organs

    def test_cerebrovascular_event_organ(self):
        _, organs = _classify_event("cerebrovascular accident")
        assert "brain" in organs

    def test_gastrointestinal_organ(self):
        _, organs = _classify_event("gastrointestinal hemorrhage")
        assert "GI tract" in organs

    def test_neurological_organ(self):
        _, organs = _classify_event("neurotoxicity")
        assert "nervous system" in organs


class TestHighRiskTermsCompleteness:
    """Verify the HIGH_RISK_TERMS set contains expected critical events."""

    def test_contains_death(self):
        assert "death" in HIGH_RISK_TERMS

    def test_contains_cardiac_arrest(self):
        assert "cardiac arrest" in HIGH_RISK_TERMS

    def test_contains_anaphylactic_shock(self):
        assert "anaphylactic shock" in HIGH_RISK_TERMS

    def test_contains_toxic_epidermal_necrolysis(self):
        assert "toxic epidermal necrolysis" in HIGH_RISK_TERMS

    def test_minimum_high_risk_terms(self):
        assert len(HIGH_RISK_TERMS) >= 10


class TestSafetyVerdictLogic:
    """Test the verdict determination rules (PASS/WARNING/HARD_FAIL)."""

    def test_no_events_means_pass(self):
        from backend.models import SafetyVerdict
        assert SafetyVerdict.PASS.value == "PASS"

    def test_verdict_enum_values(self):
        from backend.models import SafetyVerdict
        assert set(v.value for v in SafetyVerdict) == {"PASS", "WARNING", "HARD_FAIL"}
