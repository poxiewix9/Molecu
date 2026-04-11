"""Tests for the deterministic evidence scoring system.

These tests require zero external API calls — they validate the core
scoring formula: Target(0-30) + Trial(0-25) + Literature(0-25) + Safety(0-20).
"""

import pytest
from backend.agents.drug_hunter import compute_evidence_score


class TestTargetAssociation:
    """Target association score: 0-30 points based on Open Targets association score."""

    def test_perfect_target_score(self):
        score = compute_evidence_score(target_score=1.0, phase="Phase 2")
        assert score.target_association == 30

    def test_zero_target_score(self):
        score = compute_evidence_score(target_score=0.0, phase="Phase 2")
        assert score.target_association == 0

    def test_mid_range_target(self):
        score = compute_evidence_score(target_score=0.5, phase="Phase 2")
        assert score.target_association == 15

    def test_target_capped_at_30(self):
        score = compute_evidence_score(target_score=1.5, phase="Phase 2")
        assert score.target_association == 30


class TestTrialEvidence:
    """Trial evidence score: 0-25 points based on clinical trial phase."""

    def test_phase3_gets_25(self):
        score = compute_evidence_score(target_score=0.5, phase="Phase 3")
        assert score.trial_evidence == 25

    def test_phase3_alternate_format(self):
        score = compute_evidence_score(target_score=0.5, phase="PHASE3")
        assert score.trial_evidence == 25

    def test_phase2_gets_15(self):
        score = compute_evidence_score(target_score=0.5, phase="Phase 2")
        assert score.trial_evidence == 15

    def test_phase1_gets_5(self):
        score = compute_evidence_score(target_score=0.5, phase="Phase 1")
        assert score.trial_evidence == 5

    def test_unknown_phase_gets_0(self):
        score = compute_evidence_score(target_score=0.5, phase="Pre-clinical")
        assert score.trial_evidence == 0

    def test_empty_phase_gets_0(self):
        score = compute_evidence_score(target_score=0.5, phase="")
        assert score.trial_evidence == 0


class TestLiteratureSupport:
    """Literature support score: 0-25 points based on PubMed paper count."""

    def test_five_plus_papers_gets_25(self):
        score = compute_evidence_score(0.5, "Phase 2", paper_count=5)
        assert score.literature_support == 25

    def test_many_papers_gets_25(self):
        score = compute_evidence_score(0.5, "Phase 2", paper_count=50)
        assert score.literature_support == 25

    def test_three_papers_gets_15(self):
        score = compute_evidence_score(0.5, "Phase 2", paper_count=3)
        assert score.literature_support == 15

    def test_one_paper_gets_8(self):
        score = compute_evidence_score(0.5, "Phase 2", paper_count=1)
        assert score.literature_support == 8

    def test_no_papers_gets_0(self):
        score = compute_evidence_score(0.5, "Phase 2", paper_count=0)
        assert score.literature_support == 0


class TestSafetyProfile:
    """Safety profile score: 0-20 points based on FDA FAERS verdict."""

    def test_pass_gets_20(self):
        score = compute_evidence_score(0.5, "Phase 2", safety_verdict="PASS")
        assert score.safety_profile == 20

    def test_warning_gets_10(self):
        score = compute_evidence_score(0.5, "Phase 2", safety_verdict="WARNING")
        assert score.safety_profile == 10

    def test_hard_fail_gets_0(self):
        score = compute_evidence_score(0.5, "Phase 2", safety_verdict="HARD_FAIL")
        assert score.safety_profile == 0

    def test_unknown_safety_gets_10(self):
        score = compute_evidence_score(0.5, "Phase 2", safety_verdict="")
        assert score.safety_profile == 10


class TestTotalScore:
    """Total score is the sum of all four components, capped at 100."""

    def test_perfect_score(self):
        score = compute_evidence_score(
            target_score=1.0, phase="Phase 3", paper_count=10, safety_verdict="PASS"
        )
        assert score.total == 100

    def test_worst_score(self):
        score = compute_evidence_score(
            target_score=0.0, phase="", paper_count=0, safety_verdict="HARD_FAIL"
        )
        assert score.total == 0

    def test_moderate_score(self):
        score = compute_evidence_score(
            target_score=0.5, phase="Phase 2", paper_count=3, safety_verdict="WARNING"
        )
        assert score.total == 15 + 15 + 15 + 10  # 55

    def test_breakdown_string_contains_components(self):
        score = compute_evidence_score(0.5, "Phase 2", paper_count=3, safety_verdict="PASS")
        assert "Target:" in score.breakdown
        assert "Trial:" in score.breakdown
        assert "Literature:" in score.breakdown
        assert "Safety:" in score.breakdown


class TestScoreModel:
    """Verify the EvidenceScore Pydantic model fields."""

    def test_all_fields_present(self):
        score = compute_evidence_score(0.5, "Phase 2")
        assert hasattr(score, "target_association")
        assert hasattr(score, "trial_evidence")
        assert hasattr(score, "literature_support")
        assert hasattr(score, "safety_profile")
        assert hasattr(score, "total")
        assert hasattr(score, "breakdown")

    def test_serialization(self):
        score = compute_evidence_score(0.7, "Phase 3", paper_count=5, safety_verdict="PASS")
        d = score.model_dump()
        assert isinstance(d, dict)
        assert d["total"] == d["target_association"] + d["trial_evidence"] + d["literature_support"] + d["safety_profile"]
