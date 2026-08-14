import pytest
from src.detectors.address import AddressDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return AddressDetector()

def test_regression_ex33_unit_truncation(detector):
    """Regression test for ex33: preserves unit number and avoids truncation."""
    text = "Send the physical documents to 456 Oak Avenue, Apt 2B, Chicago, IL."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "456 Oak Avenue, Apt 2B, Chicago, IL"
    assert results[0].entity_type == PIIType.ADDRESS
    assert results[0].start == 31
    assert results[0].end == 66

def test_regression_ex35_french_prefix(detector):
    """Regression test for ex35: supports leading road prefixes (French style)."""
    text = "The company's registered address is 101 Boulevard Saint-Germain, Paris."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "101 Boulevard Saint-Germain, Paris"
    assert results[0].entity_type == PIIType.ADDRESS

def test_regression_ex36_abbreviation_zip(detector):
    """Regression test for ex36: supports suffix abbreviation without dot and trailing ZIP code."""
    text = "Visit our flagship store at 505 Broadway Ave, Seattle, WA 98101."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "505 Broadway Ave, Seattle, WA 98101"
    assert results[0].entity_type == PIIType.ADDRESS

def test_general_negative_cases(detector):
    """Verifies that ordinary prose containing keywords is rejected."""
    # Ordinary context words
    assert len(detector.detect("The office is located at the street corner.")) == 0
    assert len(detector.detect("Please drive down the road.")) == 0
    assert len(detector.detect("I live in the city of Paris.")) == 0
    assert len(detector.detect("Enter your email address.")) == 0

    # Lowercase prefix/suffix words
    assert len(detector.detect("We went to 123 main street.")) == 0
    assert len(detector.detect("Meet at 101 boulevard Saint-Germain.")) == 0

    # Lowercase name after prefix
    assert len(detector.detect("I bought 2 Boulevard books.")) == 0
