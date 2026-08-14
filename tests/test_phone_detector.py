import pytest
from src.detectors.phone import PhoneDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return PhoneDetector()

def test_indian_10_digit_mobile(detector):
    """Verifies detection of a plain 10-digit Indian mobile number."""
    text = "Call me at 9876543210."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == "9876543210"
    assert entity.entity_type == PIIType.PHONE
    assert entity.start == 11
    assert entity.end == 21
    assert entity.confidence == 0.80
    assert entity.source == "PhoneDetector"

def test_plus_91_mobile(detector):
    """Verifies mobile numbers with a +91 prefix and space separator."""
    text = "Contact: +91 9876543210"
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == "+91 9876543210"
    assert text[results[0].start : results[0].end] == "+91 9876543210"

def test_plus_91_mobile_with_hyphen(detector):
    """Verifies mobile numbers with a +91 prefix and hyphen separator."""
    text = "My number is +91-9876543210."
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == "+91-9876543210"

def test_indian_landline_std_code(detector):
    """Verifies local landlines with a leading 0 STD code and hyphen separator."""
    text = "Tel: 020-45053237"
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == "020-45053237"

def test_plus_91_landline(detector):
    """Verifies landlines with +91 country prefix and standard spaces."""
    text = "Landline: +91 20 4505 3237"
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == "+91 20 4505 3237"

def test_landline_with_separators_and_parentheses(detector):
    """Verifies landline formats containing parenthesized area codes or hyphens."""
    r1 = detector.detect("Office: +91 (20) 4505 3237")
    assert len(r1) == 1
    assert r1[0].text == "+91 (20) 4505 3237"
    
    r2 = detector.detect("Office: +91-20-4505-3237")
    assert len(r2) == 1
    assert r2[0].text == "+91-20-4505-3237"

def test_multiple_phone_numbers(detector):
    """Verifies detection of multiple distinct phone numbers in a single text block."""
    text = "Reach us at 9876543210 or landline 020-45053237."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "9876543210"
    assert results[1].text == "020-45053237"

def test_duplicate_phone_number(detector):
    """Verifies that duplicate numbers are returned separately and not pruned."""
    text = "Dial 9876543210 or 9876543210."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "9876543210"
    assert results[1].text == "9876543210"
    assert results[0].start != results[1].start

def test_phone_followed_by_punctuation(detector):
    """Verifies that trailing punctuation is excluded from the match bounds."""
    text = "Call +91-9876543210, now."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "+91-9876543210"

def test_phone_surrounded_by_text(detector):
    """Verifies phone detection when embedded closely in other formatting tags."""
    text = "tel:+91-20-4505-3237;ext=1"
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "+91-20-4505-3237"

def test_no_phone_number(detector):
    """Verifies empty list returned if no phone number exists."""
    text = "The page index is 2026."
    results = detector.detect(text)
    assert len(results) == 0

def test_short_numeric_strings(detector):
    """Verifies that short codes or numbers are ignored (preventing high false positives)."""
    assert len(detector.detect("2025")) == 0
    assert len(detector.detect("12345")) == 0
    assert len(detector.detect("141032")) == 0

def test_dates_rejected(detector):
    """Verifies that calendar dates are structurally rejected."""
    text = "The prospectus date is 2026-08-13."
    results = detector.detect(text)
    assert len(results) == 0

def test_registration_identifiers_rejected(detector):
    """Verifies that corporate identifiers containing digits (like CINs) are ignored."""
    text = "Company CIN is U74999MH2018PTC307777."
    results = detector.detect(text)
    assert len(results) == 0

def test_incorrectly_structured_numbers_rejected(detector):
    """Verifies that numbers starting with invalid digits (non-6-9) are structurally rejected."""
    # Start with '1'
    assert len(detector.detect("1234567890")) == 0
    # Prefixed starts with '1'
    assert len(detector.detect("+91 1234567890")) == 0

def test_phone_with_hyphen_regression(detector):
    """Regression test for phone number formatted with hyphens/spaces: 98765-43210."""
    # Positive case
    r_pos = detector.detect("Call +91 98765-43210 for details.")
    assert len(r_pos) == 1
    assert r_pos[0].text == "+91 98765-43210"

    # Negative case (nearby negative example)
    # Starts with 5 (invalid starting digit for Indian mobile)
    assert len(detector.detect("Order number 58765-43210")) == 0
    # Invalid length (too short)
    assert len(detector.detect("Call 98765-4321")) == 0

def test_6_true_positives_detection(detector):
    """Verifies that the PhoneDetector detects all 6 true positive PHONE formats from the evaluation set."""
    # 1. ex2
    r2 = detector.detect("My contact number is +91 98765-43210.")
    assert len(r2) == 1 and r2[0].text == "+91 98765-43210"

    # 2. ex22
    r22 = detector.detect("You can reach the help desk at 9876543210.")
    assert len(r22) == 1 and r22[0].text == "9876543210"

    # 3. ex23
    r23 = detector.detect("For support, dial the local landline: 022-2653-3333.")
    assert len(r23) == 1 and r23[0].text == "022-2653-3333"

    # 4. ex24
    r24 = detector.detect("Call our helpline at +91-9123456789.")
    assert len(r24) == 1 and r24[0].text == "+91-9123456789"

    # 5. ex25
    r25 = detector.detect("Reach our Mumbai office at +91-22-4505-3237.")
    assert len(r25) == 1 and r25[0].text == "+91-22-4505-3237"

    # 6. ex26
    r26 = detector.detect("Please contact us via mobile at 9999999999.")
    assert len(r26) == 1 and r26[0].text == "9999999999"

def test_phone_pipeline_regression_ex58():
    """Regression test for ex58: Verifies that Ticket ID is rejected as PHONE due to negative context penalty."""
    from src.pipeline import PIIRedactionPipeline
    from src.resolver import resolve_candidates
    
    pipeline = PIIRedactionPipeline()
    text = "Ticket ID 98765-43210 is not a valid mobile phone number."
    
    # Retrieve PhoneDetector
    phone_detector = next(d for d in pipeline.detectors if d.name == "PhoneDetector")
    candidates = phone_detector.detect(text)
    
    assert len(candidates) == 1
    assert candidates[0].text == "98765-43210"
    
    resolved = resolve_candidates(candidates, text)
    assert len(resolved) == 1
    assert not resolved[0].is_accepted
