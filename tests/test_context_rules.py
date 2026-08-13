import pytest
from src.context.rules import evaluate_context
from src.models import PIIType

def test_positive_dob_context():
    """Verifies that positive DOB keywords are matched in the context window."""
    text = "Date of Birth: 01/02/1995"
    # Candidate starts at 15 ("01/02/1995")
    evidence = evaluate_context(text, 15, 25, PIIType.DOB)
    
    assert evidence.has_positive is True
    assert evidence.has_negative is False
    assert evidence.matched_keyword == "Date of Birth"
    assert evidence.matched_rule == "DOB_positive"
    assert evidence.distance is not None

def test_negative_dob_context():
    """Verifies that negative DOB keywords (like incorporation date) are matched."""
    text = "Date of Incorporation: 01/02/1995"
    evidence = evaluate_context(text, 23, 33, PIIType.DOB)
    
    assert evidence.has_positive is False
    assert evidence.has_negative is True
    assert evidence.matched_keyword.lower() == "date of incorporation"
    assert evidence.matched_rule == "DOB_negative"

def test_positive_email_context():
    """Verifies positive email keyword matching."""
    text = "Please write to my email: john@example.com"
    evidence = evaluate_context(text, 26, 42, PIIType.EMAIL)
    
    assert evidence.has_positive is True
    assert evidence.matched_keyword == "email"

def test_positive_phone_context():
    """Verifies positive phone keyword matching."""
    text = "Contact number is +91 9876543210"
    evidence = evaluate_context(text, 18, 32, PIIType.PHONE)
    
    assert evidence.has_positive is True
    assert evidence.matched_keyword.lower() == "contact number"

def test_positive_address_context():
    """Verifies positive address keyword matching."""
    text = "Our registered office is at Pune, India."
    evidence = evaluate_context(text, 28, 39, PIIType.ADDRESS)
    
    assert evidence.has_positive is True
    assert evidence.matched_keyword.lower() == "registered office"

def test_positive_organization_context():
    """Verifies positive organization/company keyword matching."""
    text = "This company is based in India."
    evidence = evaluate_context(text, 5, 12, PIIType.ORGANIZATION)
    
    assert evidence.has_positive is True
    assert evidence.matched_keyword.lower() == "company"

def test_negative_order_number_context():
    """Verifies negative context matching for order numbers on phone/SSN types."""
    text = "Order Number: 123456789"
    # Test on phone type
    ev_phone = evaluate_context(text, 14, 23, PIIType.PHONE)
    assert ev_phone.has_negative is True
    assert ev_phone.matched_keyword.lower() == "order number"
    
    # Test on SSN type
    ev_ssn = evaluate_context(text, 14, 23, PIIType.SSN)
    assert ev_ssn.has_negative is True
    assert ev_ssn.matched_keyword.lower() == "order number"

def test_negative_ticket_number_context():
    """Verifies negative context matching for ticket numbers on phone/SSN types."""
    text = "Refer to ticket number: 123456789"
    evidence = evaluate_context(text, 24, 33, PIIType.SSN)
    
    assert evidence.has_negative is True
    assert evidence.matched_keyword.lower() == "ticket number"

def test_case_insensitive_matching():
    """Verifies that keywords match case-insensitively."""
    text = "DATE OF BIRTH is 01/02/1995"
    evidence = evaluate_context(text, 17, 27, PIIType.DOB)
    
    assert evidence.has_positive is True
    assert evidence.matched_keyword == "DATE OF BIRTH"

def test_word_boundary_behavior():
    """Verifies that keywords are not matched as substrings of unrelated words."""
    # 'mobile' is a keyword, 'automobile' should not match
    text = "Near the automobile is 9876543210"
    evidence = evaluate_context(text, 23, 33, PIIType.PHONE)
    assert evidence.has_positive is False

def test_candidate_near_context():
    """Verifies matching when context is within the window size."""
    text = "dob: 01/02/1995"
    # Distance is small
    evidence = evaluate_context(text, 5, 15, PIIType.DOB, window_size=10)
    assert evidence.has_positive is True

def test_candidate_far_from_context():
    """Verifies that context outside the window is ignored."""
    text = "dob ... very far ... 01/02/1995"
    # Using window size of 5 characters, 'dob' is outside it
    evidence = evaluate_context(text, 21, 31, PIIType.DOB, window_size=5)
    assert evidence.has_positive is False

def test_no_context():
    """Verifies returned results when no context matches."""
    text = "The value was 01/02/1995."
    evidence = evaluate_context(text, 14, 24, PIIType.DOB)
    
    assert evidence.has_positive is False
    assert evidence.has_negative is False
    assert evidence.matched_keyword is None

def test_multiple_context_signals():
    """Verifies that both positive and negative signals are evaluated if present."""
    # Text contains both positive (born) and negative (issue date) near candidate
    text = "born on issue date 01/02/1995"
    evidence = evaluate_context(text, 19, 29, PIIType.DOB, window_size=30)
    
    assert evidence.has_positive is True
    assert evidence.has_negative is True
    # The evaluation prioritizes what is closer or checked. Let's verify both are true
    assert evidence.matched_keyword is not None
