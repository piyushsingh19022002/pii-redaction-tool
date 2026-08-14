import pytest
from src.detectors.ner import NERDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return NERDetector()

def test_person_detection(detector):
    """Verifies that a single PERSON entity is detected with correct metadata."""
    text = "John Doe joined the team."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == "John Doe"
    assert entity.entity_type == PIIType.PERSON
    assert entity.start == 0
    assert entity.end == 8
    assert entity.confidence == 0.85
    assert entity.source == "ner"

def test_multiple_person_entities(detector):
    """Verifies that multiple PERSON entities are detected in a single string."""
    text = "Rashi Patil and Rohan Dey are collaborating."
    results = detector.detect(text)
    
    # We check that the list contains both names
    person_texts = [r.text for r in results if r.entity_type == PIIType.PERSON]
    assert "Rashi Patil" in person_texts
    assert "Rohan Dey" in person_texts

def test_organization_detection(detector):
    """Verifies that a single ORG entity is mapped to PIIType.ORGANIZATION."""
    text = "We visited Acme Corporation today."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == "Acme Corporation"
    assert entity.entity_type == PIIType.ORGANIZATION
    assert entity.start == 11
    assert entity.end == 27

def test_multiple_organization_entities(detector):
    """Verifies that multiple ORG entities are detected in a single string."""
    text = "Scaler AI Labs acquired Example Technologies."
    results = detector.detect(text)
    
    org_texts = [r.text for r in results if r.entity_type == PIIType.ORGANIZATION]
    assert "Scaler AI Labs" in org_texts
    assert "Example Technologies" in org_texts

def test_mixed_person_and_org(detector):
    """Verifies that both PERSON and ORGANIZATION entities are detected in a mixed sentence."""
    text = "Rashi Patil works at Acme Corporation."
    results = detector.detect(text)
    
    assert len(results) == 2
    # Ensure they are sorted by start index
    results.sort(key=lambda x: x.start)
    
    assert results[0].text == "Rashi Patil"
    assert results[0].entity_type == PIIType.PERSON
    
    assert results[1].text == "Acme Corporation"
    assert results[1].entity_type == PIIType.ORGANIZATION

def test_exact_text_and_offsets(detector):
    """Verifies the text[start:end] == entity_text invariant on the original string."""
    text = "Yesterday, Rohan Dey visited Acme Corporation."
    results = detector.detect(text)
    
    for entity in results:
        assert text[entity.start : entity.end] == entity.text

def test_no_entities_found(detector):
    """Verifies empty list returned if no entities are present."""
    text = "This is standard text containing no names of people or companies."
    assert len(detector.detect(text)) == 0

def test_repeated_entity_occurrences(detector):
    """Verifies that duplicate mentions of the same name are returned individually."""
    text = "John Doe met another person who is not John Doe."
    results = detector.detect(text)
    
    person_results = [r for r in results if r.text == "John Doe"]
    assert len(person_results) == 2
    assert person_results[0].start != person_results[1].start

def test_ner_address_and_org_regression(detector):
    """Regression test for custom ORGANIZATION and ADDRESS extraction and filter rules."""
    # 1. Organization suffix match
    r_org = detector.detect("Google LLC is located here.")
    orgs = [ent for ent in r_org if ent.entity_type == PIIType.ORGANIZATION]
    assert any(o.text == "Google LLC" for o in orgs)

    # 2. Address pattern match
    r_addr = detector.detect("Address is 1600 Amphitheatre Parkway, Mountain View, CA.")
    addrs = [ent for ent in r_addr if ent.entity_type == PIIType.ADDRESS]
    assert len(addrs) == 1
    assert addrs[0].text == "1600 Amphitheatre Parkway, Mountain View, CA"

    # 3. False Positive Filtering
    r_fp = detector.detect("SSN, IP, LLC, Server IP, or 01/02/1995 are not organization names.")
    orgs_fp = [ent for ent in r_fp if ent.entity_type == PIIType.ORGANIZATION]
    assert len(orgs_fp) == 0
