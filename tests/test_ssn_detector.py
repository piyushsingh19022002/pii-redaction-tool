import pytest
from src.detectors.ssn import SSNDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return SSNDetector()

def test_valid_formatted_ssn(detector):
    """Verifies that a valid formatted SSN is detected."""
    text = "The code is 123-45-6789."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == "123-45-6789"
    assert entity.entity_type == PIIType.SSN
    assert entity.start == 12
    assert entity.end == 23
    assert entity.confidence == 0.95
    assert entity.source == "SSNDetector"

def test_ssn_inside_normal_text(detector):
    """Verifies that an SSN embedded inside a text block is correctly detected."""
    text = "Please redact my SSN: 899-12-3456 right away."
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == "899-12-3456"
    assert text[results[0].start : results[0].end] == "899-12-3456"

def test_multiple_ssns(detector):
    """Verifies that multiple different SSNs are all detected with correct offsets."""
    text = "Check 123-45-6789 and 899-12-3456."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "123-45-6789"
    assert results[1].text == "899-12-3456"

def test_duplicate_ssn_occurrences(detector):
    """Verifies that duplicate occurrences of the same SSN are returned separately."""
    text = "SSN: 123-45-6789 and again 123-45-6789."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "123-45-6789"
    assert results[1].text == "123-45-6789"
    assert results[0].start != results[1].start

def test_ssn_followed_by_punctuation(detector):
    """Verifies that trailing punctuation is excluded from the match."""
    r1 = detector.detect("SSN: 123-45-6789.")
    assert len(r1) == 1
    assert r1[0].text == "123-45-6789"

    r2 = detector.detect("SSN: 123-45-6789, or 899-12-3456;")
    assert len(r2) == 2
    assert r2[0].text == "123-45-6789"
    assert r2[1].text == "899-12-3456"

def test_invalid_area_codes(detector):
    """Verifies structural rejection of invalid area codes: 000, 666, and 900-999."""
    assert len(detector.detect("000-12-3456")) == 0
    assert len(detector.detect("666-12-3456")) == 0
    assert len(detector.detect("900-12-3456")) == 0
    assert len(detector.detect("950-12-3456")) == 0
    assert len(detector.detect("999-12-3456")) == 0

def test_invalid_group_codes(detector):
    """Verifies structural rejection of group code '00'."""
    assert len(detector.detect("123-00-4567")) == 0

def test_invalid_serial_codes(detector):
    """Verifies structural rejection of serial code '0000'."""
    assert len(detector.detect("123-45-0000")) == 0

def test_digit_lengths(detector):
    """Verifies that numbers with too few or too many digits are rejected."""
    # Too few
    assert len(detector.detect("12-34-5678")) == 0
    assert len(detector.detect("123-4-5678")) == 0
    assert len(detector.detect("123-45-678")) == 0
    # Too many
    assert len(detector.detect("1234-56-7890")) == 0

def test_larger_identifier_containing_ssn_rejected(detector):
    """Verifies that an SSN-like pattern embedded within a larger number is rejected."""
    assert len(detector.detect("1123-45-67890")) == 0

def test_random_text_rejected(detector):
    """Verifies that normal text without SSNs produces no matches."""
    assert len(detector.detect("This is just standard text without any numbers.")) == 0

def test_ambiguous_unformatted_digits_rejected(detector):
    """Verifies that plain 9-digit numbers are ignored to avoid false positives."""
    assert len(detector.detect("123456789")) == 0
    assert len(detector.detect("202608130")) == 0
