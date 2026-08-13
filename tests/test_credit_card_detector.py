import pytest
from src.detectors.credit_card import CreditCardDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return CreditCardDetector()

# Synthetic test fixtures for Luhn check:
# 4111111111111111 is a standard Visa test card number (Luhn valid)
# 4111111111111112 is Luhn invalid (ends with 2 instead of 1)
VALID_CARD_UNFORMATTED = "4111111111111111"
VALID_CARD_SPACES = "4111 1111 1111 1111"
VALID_CARD_HYPHENS = "4111-1111-1111-1111"
INVALID_LUHN_CARD = "4111111111111112"

def test_valid_luhn_card_number(detector):
    """Verifies that a valid unformatted synthetic card number is detected."""
    text = f"My card is {VALID_CARD_UNFORMATTED}."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == VALID_CARD_UNFORMATTED
    assert entity.entity_type == PIIType.CREDIT_CARD
    assert entity.start == 11
    assert entity.end == 27
    assert entity.confidence == 0.99
    assert entity.source == "CreditCardDetector"

def test_valid_card_with_spaces(detector):
    """Verifies that a valid card number formatted with spaces is detected."""
    text = f"My card is {VALID_CARD_SPACES}."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == VALID_CARD_SPACES
    assert text[entity.start : entity.end] == VALID_CARD_SPACES

def test_valid_card_with_hyphens(detector):
    """Verifies that a valid card number formatted with hyphens is detected."""
    text = f"My card is {VALID_CARD_HYPHENS}."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == VALID_CARD_HYPHENS
    assert text[entity.start : entity.end] == VALID_CARD_HYPHENS

def test_multiple_cards(detector):
    """Verifies that multiple different credit card numbers are detected."""
    text = f"Cards: {VALID_CARD_UNFORMATTED} and {VALID_CARD_HYPHENS}."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == VALID_CARD_UNFORMATTED
    assert results[1].text == VALID_CARD_HYPHENS

def test_duplicate_card_occurrences(detector):
    """Verifies that duplicate card numbers in the same text block are returned individually."""
    text = f"Primary: {VALID_CARD_HYPHENS}, backup: {VALID_CARD_HYPHENS}."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == VALID_CARD_HYPHENS
    assert results[1].text == VALID_CARD_HYPHENS
    assert results[0].start != results[1].start

def test_card_followed_by_punctuation(detector):
    """Verifies that trailing punctuation is excluded from the match."""
    text = f"Please charge {VALID_CARD_HYPHENS}."
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == VALID_CARD_HYPHENS

def test_card_surrounded_by_text(detector):
    """Verifies card detection when embedded inside query strings."""
    text = f"card_number={VALID_CARD_UNFORMATTED}&expiry=1227"
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == VALID_CARD_UNFORMATTED

def test_invalid_luhn_number_rejected(detector):
    """Verifies that a card-like number with an invalid checksum is rejected."""
    text = f"Invalid card: {INVALID_LUHN_CARD}."
    results = detector.detect(text)
    assert len(results) == 0

def test_length_validations_rejected(detector):
    """Verifies that numbers outside the 13-19 digit range are rejected."""
    # Too short: 12 digits (Luhn valid for 123456789012? No, but length check handles it)
    assert len(detector.detect("123456789012")) == 0
    # Too long: 20 digits
    assert len(detector.detect("12345678901234567890")) == 0

def test_numeric_non_card_rejection(detector):
    """Verifies that non-card numeric strings are rejected."""
    # A standard 13-digit sequence that fails Luhn check
    assert len(detector.detect("1234567890123")) == 0
    # Version numbers
    assert len(detector.detect("Version 1.2.3.4")) == 0
