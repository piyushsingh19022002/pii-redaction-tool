import pytest
from src.models import PIIEntity, PIIType, ContextEvidence, ResolutionResult
from src.resolver import resolve_candidate, resolve_candidates, resolve_overlaps

def test_high_confidence_accepted():
    """Verifies that high-confidence candidates without context are accepted."""
    cand = PIIEntity(
        text="john@example.com",
        entity_type=PIIType.EMAIL,
        start=0,
        end=16,
        confidence=0.95,
        source="regex"
    )
    result = resolve_candidate(cand, None, acceptance_threshold=0.70)
    assert result.is_accepted is True
    assert result.score == 0.95
    assert "Accepted" in result.reason

def test_low_confidence_rejected():
    """Verifies that low-confidence candidates without context are rejected."""
    cand = PIIEntity(
        text="12345",
        entity_type=PIIType.PHONE,
        start=0,
        end=5,
        confidence=0.40,
        source="regex"
    )
    result = resolve_candidate(cand, None, acceptance_threshold=0.70)
    assert result.is_accepted is False
    assert result.score == 0.40
    assert "Rejected" in result.reason

def test_positive_context_increases_score():
    """Verifies that positive context evidence adds context bonus and clamps at 1.0."""
    cand = PIIEntity(
        text="01/02/1995",
        entity_type=PIIType.DOB,
        start=15,
        end=25,
        confidence=0.90,
        source="regex"
    )
    evidence = ContextEvidence(has_positive=True, has_negative=False, matched_keyword="dob")
    result = resolve_candidate(cand, evidence, acceptance_threshold=0.70, context_bonus=0.15)
    
    # 0.90 + 0.15 = 1.05 -> clamped to 1.0
    assert result.score == 1.0
    assert result.is_accepted is True
    assert "positive context bonus" in result.reason

def test_negative_context_decreases_score():
    """Verifies that negative context evidence subtracts penalty."""
    cand = PIIEntity(
        text="01/02/1995",
        entity_type=PIIType.DOB,
        start=23,
        end=33,
        confidence=0.85,
        source="regex"
    )
    evidence = ContextEvidence(has_positive=False, has_negative=True, matched_keyword="issue date")
    result = resolve_candidate(cand, evidence, acceptance_threshold=0.70, context_penalty=0.30)
    
    # 0.85 - 0.30 = 0.55 -> below threshold 0.70
    assert result.score == 0.55
    assert result.is_accepted is False
    assert "negative context" in result.reason

def test_positive_and_negative_conflict_handled():
    """Verifies score logic and reason description when both positive and negative context exist."""
    cand = PIIEntity(
        text="01/02/1995",
        entity_type=PIIType.DOB,
        start=10,
        end=20,
        confidence=0.80,
        source="regex"
    )
    evidence = ContextEvidence(has_positive=True, has_negative=True, matched_keyword="dob")
    result = resolve_candidate(cand, evidence, context_bonus=0.15, context_penalty=0.30)
    
    # 0.80 + 0.15 - 0.30 = 0.65 (clamped)
    assert result.score == 0.65
    assert "Conflicting context" in result.reason

def test_no_context_uses_detector_confidence():
    """Verifies baseline confidence is used as final score when ContextEvidence exists but is empty."""
    cand = PIIEntity(
        text="01/02/1995",
        entity_type=PIIType.DOB,
        start=10,
        end=20,
        confidence=0.75,
        source="regex"
    )
    evidence = ContextEvidence(has_positive=False, has_negative=False)
    result = resolve_candidate(cand, evidence)
    
    assert result.score == 0.75
    assert "No context matches" in result.reason

def test_non_overlapping_candidates_retained():
    """Verifies that non-overlapping accepted candidates are all kept."""
    results = [
        ResolutionResult(
            entity=PIIEntity("john@example.com", PIIType.EMAIL, 10, 26, 0.95, "regex"),
            is_accepted=True, score=0.95, reason=""
        ),
        ResolutionResult(
            entity=PIIEntity("9876543210", PIIType.PHONE, 50, 60, 0.90, "regex"),
            is_accepted=True, score=0.90, reason=""
        )
    ]
    resolved = resolve_overlaps(results)
    assert len(resolved) == 2
    assert resolved[0].entity.text == "john@example.com"
    assert resolved[1].entity.text == "9876543210"

def test_overlapping_candidates_scores():
    """Verifies that the candidate with the higher score is kept when spans overlap."""
    results = [
        # Candidate A: start=10, end=25, score=0.95
        ResolutionResult(
            entity=PIIEntity("john doe", PIIType.PERSON, 10, 18, 0.95, "ner"),
            is_accepted=True, score=0.95, reason=""
        ),
        # Candidate B: start=15, end=20, score=0.80 (overlaps A)
        ResolutionResult(
            entity=PIIEntity("doe", PIIType.ORGANIZATION, 15, 18, 0.80, "ner"),
            is_accepted=True, score=0.80, reason=""
        )
    ]
    resolved = resolve_overlaps(results)
    assert len(resolved) == 1
    assert resolved[0].entity.text == "john doe"

def test_overlapping_equal_score_longer_span():
    """Verifies that the candidate with the longer span wins when scores are equal."""
    results = [
        # Short span: start=10, end=15 (len=5)
        ResolutionResult(
            entity=PIIEntity("short", PIIType.ORGANIZATION, 10, 15, 0.85, "ner"),
            is_accepted=True, score=0.85, reason=""
        ),
        # Long span: start=8, end=18 (len=10) (overlaps short)
        ResolutionResult(
            entity=PIIEntity("longer span", PIIType.PERSON, 8, 19, 0.85, "ner"),
            is_accepted=True, score=0.85, reason=""
        )
    ]
    resolved = resolve_overlaps(results)
    assert len(resolved) == 1
    assert resolved[0].entity.text == "longer span"

def test_exact_duplicates_deduplicated():
    """Verifies that exact duplicate candidates are resolved to a single accepted item."""
    results = [
        ResolutionResult(
            entity=PIIEntity("john doe", PIIType.PERSON, 10, 18, 0.90, "ner"),
            is_accepted=True, score=0.90, reason=""
        ),
        ResolutionResult(
            entity=PIIEntity("john doe", PIIType.PERSON, 10, 18, 0.90, "ner"),
            is_accepted=True, score=0.90, reason=""
        )
    ]
    resolved = resolve_overlaps(results)
    assert len(resolved) == 1
    assert resolved[0].entity.text == "john doe"

def test_preservation_invariants():
    """Verifies that original properties (text, start, end, type) are preserved in resolved results."""
    cand = PIIEntity("john doe", PIIType.PERSON, 10, 18, 0.90, "ner")
    result = resolve_candidate(cand, None)
    
    assert result.entity.text == "john doe"
    assert result.entity.start == 10
    assert result.entity.end == 18
    assert result.entity.entity_type == PIIType.PERSON
    assert result.entity.source == "ner"
