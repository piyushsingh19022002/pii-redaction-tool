import pytest
from src.detectors.email import EmailDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return EmailDetector()

def test_detect_one_valid_email(detector):
    """Verifies detection of a single basic email address."""
    text = "Please reach out to john@example.com for details."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == "john@example.com"
    assert entity.entity_type == PIIType.EMAIL
    assert entity.start == 20
    assert entity.end == 36
    assert entity.source == "EmailDetector"
    assert entity.confidence == 0.95

def test_detect_multiple_valid_emails(detector):
    """Verifies that multiple different emails in the same text are all detected."""
    text = "Send copy to alice@example.com and cc bob@company.org."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "alice@example.com"
    assert results[1].text == "bob@company.org"
    
    # Verify offsets
    assert text[results[0].start : results[0].end] == "alice@example.com"
    assert text[results[1].start : results[1].end] == "bob@company.org"

def test_detect_gmail_style_email(detector):
    """Verifies detection of gmail-style dot formatting in username."""
    text = "Contact me at rashi.patil@gmail.com"
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "rashi.patil@gmail.com"

def test_detect_company_email(detector):
    """Verifies detection of typical corporate email structures."""
    text = "Email john.doe@example.com"
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "john.doe@example.com"

def test_detect_multi_level_domain(detector):
    """Verifies detection of emails with multi-level domains (e.g. .co.in)."""
    text = "Support: user123@company.co.in"
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "user123@company.co.in"

def test_detect_plus_tag_email(detector):
    """Verifies detection of emails containing a plus-tag modifier in the local part."""
    text = "Register with name+tag@example.com"
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "name+tag@example.com"

def test_detect_hyphen_and_underscore_local_part(detector):
    """Verifies detection of hyphens and underscores in the username."""
    text = "Emails: test-user@example.com and dev_admin@company.com"
    results = detector.detect(text)
    assert len(results) == 2
    assert results[0].text == "test-user@example.com"
    assert results[1].text == "dev_admin@company.com"

def test_detect_no_email(detector):
    """Verifies that an empty list is returned if no email exists in the text."""
    text = "This is a normal paragraph with no electronic mail addresses."
    results = detector.detect(text)
    assert len(results) == 0

def test_detect_invalid_emails(detector):
    """Verifies that invalid email formats are ignored by the regex parser."""
    invalid_cases = [
        "hello@",
        "@example.com",
        "john",
        "john@@example.com",
        "john@ ",
        "john@example",
        "john@.com"
    ]
    for case in invalid_cases:
        results = detector.detect(case)
        assert len(results) == 0, f"Expected no match for invalid email case: '{case}'"

def test_detect_multiple_occurrences_of_same_email(detector):
    """Verifies that duplicate occurrences are not deduplicated and are returned separately."""
    text = "Email a@x.com and again a@x.com"
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "a@x.com"
    assert results[1].text == "a@x.com"
    
    # Assert coordinates represent both instances separately
    assert results[0].start != results[1].start

def test_detect_email_followed_by_punctuation(detector):
    """Verifies that trailing punctuation like dots or commas is omitted from the match."""
    # Trail dot
    r1 = detector.detect("Write to john@example.com.")
    assert len(r1) == 1
    assert r1[0].text == "john@example.com"
    
    # Trail comma
    r2 = detector.detect("Contact john@example.com, or check website.")
    assert len(r2) == 1
    assert r2[0].text == "john@example.com"

def test_detect_email_surrounded_by_text(detector):
    """Verifies that email can be detected when embedded closely in other characters."""
    text = "send_to:john@example.com;type=regular"
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "john@example.com"
