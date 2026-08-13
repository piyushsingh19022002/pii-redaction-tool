import pytest
from dataclasses import FrozenInstanceError
from src.models import PIIEntity, PIIType

def test_valid_person_entity():
    """Verifies that a valid PERSON entity is initialized successfully."""
    entity = PIIEntity(
        text="Sarthak Malvadkar",
        entity_type=PIIType.PERSON,
        start=15,
        end=33,
        confidence=0.94,
        source="ner"
    )
    assert entity.text == "Sarthak Malvadkar"
    assert entity.entity_type == PIIType.PERSON
    assert entity.start == 15
    assert entity.end == 33
    assert entity.confidence == 0.94
    assert entity.source == "ner"

def test_valid_email_entity():
    """Verifies that a valid EMAIL entity is initialized successfully."""
    entity = PIIEntity(
        text="sarthak@example.com",
        entity_type=PIIType.EMAIL,
        start=50,
        end=69,
        confidence=0.99,
        source="regex"
    )
    assert entity.text == "sarthak@example.com"
    assert entity.entity_type == PIIType.EMAIL
    assert entity.start == 50
    assert entity.end == 69
    assert entity.confidence == 0.99
    assert entity.source == "regex"

def test_valid_sources():
    """Verifies that various valid sources ('ner', 'regex', 'context') can be used."""
    e1 = PIIEntity("Mumbai", PIIType.ADDRESS, 0, 6, 1.0, "ner")
    e2 = PIIEntity("Mumbai", PIIType.ADDRESS, 0, 6, 1.0, "regex")
    e3 = PIIEntity("Mumbai", PIIType.ADDRESS, 0, 6, 1.0, "context")
    assert e1.source == "ner"
    assert e2.source == "regex"
    assert e3.source == "context"

def test_offsets_meaning():
    """Verifies that start and end offsets follow the standard [start, end) exclusive convention."""
    text = "Hello John"
    # "John" starts at index 6 and ends at index 10
    start = 6
    end = 10
    assert text[start:end] == "John"
    
    entity = PIIEntity(
        text="John",
        entity_type=PIIType.PERSON,
        start=start,
        end=end,
        confidence=0.9,
        source="regex"
    )
    assert entity.start == 6
    assert entity.end == 10

def test_confidence_boundaries():
    """Verifies confidence boundary checks (0.0, 0.5, 1.0 are valid)."""
    e1 = PIIEntity("test", PIIType.IP_ADDRESS, 0, 4, 0.0, "regex")
    e2 = PIIEntity("test", PIIType.IP_ADDRESS, 0, 4, 0.5, "regex")
    e3 = PIIEntity("test", PIIType.IP_ADDRESS, 0, 4, 1.0, "regex")
    
    assert e1.confidence == 0.0
    assert e2.confidence == 0.5
    assert e3.confidence == 1.0

def test_invalid_negative_start():
    """Verifies that an error is raised when the start index is negative."""
    with pytest.raises(ValueError, match="start index must be a non-negative integer"):
        PIIEntity("John", PIIType.PERSON, -1, 4, 0.9, "ner")

def test_invalid_end_before_start():
    """Verifies that an error is raised if end index is strictly less than start index."""
    with pytest.raises(ValueError, match="end index must be an integer greater than or equal to the start index"):
        PIIEntity("John", PIIType.PERSON, 5, 4, 0.9, "ner")

def test_invalid_confidence_range():
    """Verifies that an error is raised if confidence is outside the [0.0, 1.0] range."""
    with pytest.raises(ValueError, match="confidence must be a number between 0.0 and 1.0 inclusive"):
        PIIEntity("John", PIIType.PERSON, 0, 4, -0.1, "ner")
        
    with pytest.raises(ValueError, match="confidence must be a number between 0.0 and 1.0 inclusive"):
        PIIEntity("John", PIIType.PERSON, 0, 4, 1.01, "ner")

def test_invalid_entity_type():
    """Verifies that an error is raised if entity_type is not a PIIType enum member."""
    with pytest.raises(TypeError, match="entity_type must be a member of the PIIType enum"):
        PIIEntity("John", "PERSON", 0, 4, 0.9, "ner")

def test_invalid_empty_source():
    """Verifies that an error is raised if source is empty or whitespace-only."""
    with pytest.raises(ValueError, match="source must be a non-empty string"):
        PIIEntity("John", PIIType.PERSON, 0, 4, 0.9, "")
        
    with pytest.raises(ValueError, match="source must be a non-empty string"):
        PIIEntity("John", PIIType.PERSON, 0, 4, 0.9, "   ")

def test_equality_behavior():
    """Verifies that two entities with identical parameters are equal."""
    e1 = PIIEntity("John", PIIType.PERSON, 0, 4, 0.9, "ner")
    e2 = PIIEntity("John", PIIType.PERSON, 0, 4, 0.9, "ner")
    e3 = PIIEntity("Doe", PIIType.PERSON, 0, 3, 0.9, "ner")
    
    assert e1 == e2
    assert e1 != e3

def test_immutability():
    """Verifies that PIIEntity is frozen and raises FrozenInstanceError upon modification attempt."""
    entity = PIIEntity("John", PIIType.PERSON, 0, 4, 0.9, "ner")
    with pytest.raises(FrozenInstanceError):
        entity.text = "Jack"
    with pytest.raises(FrozenInstanceError):
        entity.confidence = 0.95
