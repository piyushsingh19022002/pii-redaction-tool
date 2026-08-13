import pytest
from src.models import PIIEntity, PIIType
from src.pseudonymizer import Pseudonymizer

@pytest.fixture
def pseudonymizer():
    return Pseudonymizer()

def test_person_replacement(pseudonymizer):
    entity = PIIEntity("Rashi Patil", PIIType.PERSON, 0, 11, 0.90, "ner")
    replacement = pseudonymizer.pseudonymize(entity)
    assert replacement != "Rashi Patil"
    assert len(replacement) > 0

def test_email_replacement(pseudonymizer):
    entity = PIIEntity("john@example.com", PIIType.EMAIL, 0, 16, 0.95, "regex")
    replacement = pseudonymizer.pseudonymize(entity)
    assert "@example.com" in replacement
    assert replacement != "john@example.com"

def test_phone_replacement(pseudonymizer):
    entity = PIIEntity("+91 9876543210", PIIType.PHONE, 0, 14, 0.90, "regex")
    replacement = pseudonymizer.pseudonymize(entity)
    assert replacement.startswith("+91")
    assert replacement != "+91 9876543210"

def test_organization_replacement(pseudonymizer):
    entity = PIIEntity("Scaler AI Labs", PIIType.ORGANIZATION, 0, 14, 0.90, "ner")
    replacement = pseudonymizer.pseudonymize(entity)
    assert replacement != "Scaler AI Labs"
    assert len(replacement) > 0

def test_address_replacement(pseudonymizer):
    entity = PIIEntity("123 Main St", PIIType.ADDRESS, 0, 11, 0.85, "regex")
    replacement = pseudonymizer.pseudonymize(entity)
    assert replacement != "123 Main St"
    assert len(replacement) > 0

def test_ssn_replacement(pseudonymizer):
    entity = PIIEntity("123-45-6789", PIIType.SSN, 0, 11, 0.99, "regex")
    replacement = pseudonymizer.pseudonymize(entity)
    assert replacement.startswith("999-")
    assert replacement != "123-45-6789"

def test_credit_card_replacement(pseudonymizer):
    entity = PIIEntity("4111-1111-1111-1111", PIIType.CREDIT_CARD, 0, 19, 0.99, "regex")
    replacement = pseudonymizer.pseudonymize(entity)
    assert "-" in replacement
    assert replacement != "4111-1111-1111-1111"
    
    # Verify it passes Luhn check dynamically
    digits = replacement.replace("-", "")
    total = 0
    for idx, char in enumerate(reversed(digits)):
        num = int(char)
        if idx % 2 == 1:
            num *= 2
            if num > 9:
                num -= 9
        total += num
    assert total % 10 == 0

def test_dob_replacement(pseudonymizer):
    entity = PIIEntity("01/02/1995", PIIType.DOB, 0, 10, 0.90, "regex")
    replacement = pseudonymizer.pseudonymize(entity)
    assert "/" in replacement
    assert replacement != "01/02/1995"

def test_ip_address_replacement(pseudonymizer):
    entity = PIIEntity("192.168.1.1", PIIType.IP_ADDRESS, 0, 11, 0.95, "regex")
    replacement = pseudonymizer.pseudonymize(entity)
    assert replacement.startswith("192.0.2.")
    assert replacement != "192.168.1.1"

def test_consistency_repeated_person(pseudonymizer):
    entity1 = PIIEntity("Rashi Patil", PIIType.PERSON, 0, 11, 0.90, "ner")
    entity2 = PIIEntity("Rashi Patil", PIIType.PERSON, 20, 31, 0.90, "ner")
    
    replacement1 = pseudonymizer.pseudonymize(entity1)
    replacement2 = pseudonymizer.pseudonymize(entity2)
    assert replacement1 == replacement2

def test_consistency_repeated_email(pseudonymizer):
    entity1 = PIIEntity("john@example.com", PIIType.EMAIL, 10, 26, 0.95, "regex")
    entity2 = PIIEntity("john@example.com", PIIType.EMAIL, 50, 66, 0.95, "regex")
    
    replacement1 = pseudonymizer.pseudonymize(entity1)
    replacement2 = pseudonymizer.pseudonymize(entity2)
    assert replacement1 == replacement2

def test_independent_mapping_different_type(pseudonymizer):
    # Same string but different type maps independently
    entity1 = PIIEntity("Example", PIIType.PERSON, 0, 7, 0.80, "ner")
    entity2 = PIIEntity("Example", PIIType.ORGANIZATION, 10, 17, 0.80, "ner")
    
    rep1 = pseudonymizer.pseudonymize(entity1)
    rep2 = pseudonymizer.pseudonymize(entity2)
    assert rep1 != rep2

def test_different_pii_values_get_different_mappings(pseudonymizer):
    entity1 = PIIEntity("John Doe", PIIType.PERSON, 0, 8, 0.90, "ner")
    entity2 = PIIEntity("Jane Smith", PIIType.PERSON, 10, 20, 0.90, "ner")
    
    rep1 = pseudonymizer.pseudonymize(entity1)
    rep2 = pseudonymizer.pseudonymize(entity2)
    assert rep1 != rep2

def test_original_entity_is_not_modified(pseudonymizer):
    entity = PIIEntity("Rashi Patil", PIIType.PERSON, 0, 11, 0.90, "ner")
    pseudonymizer.pseudonymize(entity)
    assert entity.text == "Rashi Patil"
    assert entity.start == 0
    assert entity.end == 11
    assert entity.entity_type == PIIType.PERSON
