import pytest
from src.detectors.dob import DOBDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return DOBDetector()

def test_dob_with_different_context_keywords(detector):
    """Verifies that dates prefixed with valid DOB keywords are detected."""
    # Date of Birth
    r1 = detector.detect("Date of Birth: 01/02/1995")
    assert len(r1) == 1
    assert r1[0].text == "01/02/1995"
    assert r1[0].entity_type == PIIType.DOB
    assert r1[0].confidence == 0.80
    assert r1[0].source == "context"
    assert r1[0].start == 15
    assert r1[0].end == 25

    # DOB
    r2 = detector.detect("DOB: 01-02-1995")
    assert len(r2) == 1
    assert r2[0].text == "01-02-1995"

    # Birth Date
    r3 = detector.detect("Birth Date: February 1, 1995")
    assert len(r3) == 1
    assert r3[0].text == "February 1, 1995"

    # Born on
    r4 = detector.detect("Born on 1 February 1995")
    assert len(r4) == 1
    assert r4[0].text == "1 February 1995"

    # Birthdate
    r5 = detector.detect("My birthdate is 01.02.1995.")
    assert len(r5) == 1
    assert r5[0].text == "01.02.1995"

def test_case_insensitive_keywords(detector):
    """Verifies that context keywords are checked case-insensitively."""
    r1 = detector.detect("dob: 01/02/1995")
    assert len(r1) == 1
    assert r1[0].text == "01/02/1995"

    r2 = detector.detect("BORN ON 01/02/1995")
    assert len(r2) == 1
    assert r2[0].text == "01/02/1995"

def test_multiple_dobs(detector):
    """Verifies detection of multiple distinct DOB occurrences in the same string."""
    text = "DOB: 01/02/1995 and birth date: 02/03/1996."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "01/02/1995"
    assert results[1].text == "02/03/1996"
    assert results[0].start == 5
    assert results[0].end == 15
    assert results[1].start == 32
    assert results[1].end == 42

def test_duplicate_dob_occurrences(detector):
    """Verifies that duplicate DOB occurrences are returned individually with unique offsets."""
    text = "DOB is 01/02/1995, repeat DOB is 01/02/1995."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "01/02/1995"
    assert results[1].text == "01/02/1995"
    assert results[0].start != results[1].start

def test_supported_date_formats(detector):
    """Verifies that all required date layouts (numeric and textual) are parsed."""
    formats = [
        ("DOB: 01/02/1995", "01/02/1995"),
        ("DOB: 01-02-1995", "01-02-1995"),
        ("DOB: 01.02.1995", "01.02.1995"),
        ("DOB: 1995-02-01", "1995-02-01"),
        ("DOB: February 1, 1995", "February 1, 1995"),
        ("DOB: Feb 1, 1995", "Feb 1, 1995"),
        ("DOB: 1 February 1995", "1 February 1995"),
        ("DOB: 1 Feb 1995", "1 Feb 1995"),
    ]
    for text, expected in formats:
        res = detector.detect(text)
        assert len(res) == 1, f"Failed for format: {text}"
        assert res[0].text == expected

def test_invalid_calendar_dates_rejected(detector):
    """Verifies that syntactically correct dates representing invalid calendar dates are rejected."""
    # February 31st
    assert len(detector.detect("DOB: 31/02/1995")) == 0
    # 99/99/9999 dummy date
    assert len(detector.detect("DOB: 99/99/9999")) == 0
    # Month 99
    assert len(detector.detect("DOB: 2025-99-99")) == 0

def test_non_dob_dates_rejected(detector):
    """Verifies that calendar dates with non-DOB context are ignored."""
    assert len(detector.detect("Date of Issue: 01/02/1995")) == 0
    assert len(detector.detect("Date of Incorporation: 01/02/1995")) == 0
    assert len(detector.detect("Agreement Date: 01/02/1995")) == 0
    assert len(detector.detect("The document was signed on 01/02/1995.")) == 0

def test_punctuation_around_dob(detector):
    """Verifies that punctuation directly adjacent to the date is excluded."""
    # Trailing period
    r1 = detector.detect("DOB: 01/02/1995.")
    assert len(r1) == 1
    assert r1[0].text == "01/02/1995"
    
    # Parentheses
    r2 = detector.detect("DOB: (01/02/1995)")
    assert len(r2) == 1
    assert r2[0].text == "01/02/1995"

def test_offset_invariance(detector):
    """Verifies the text[start:end] == matched_text invariant."""
    text = "He was born on 1 February 1995 today."
    results = detector.detect(text)
    assert len(results) == 1
    assert text[results[0].start : results[0].end] == "1 February 1995"
