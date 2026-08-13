import pytest
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

def test_base_detector_cannot_be_instantiated():
    """Verifies that BaseDetector is abstract and cannot be directly instantiated."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class BaseDetector"):
        BaseDetector()

def test_concrete_detector_implementation():
    """Verifies that a subclass implementing detect can be successfully run."""
    class MockPhoneDetector(BaseDetector):
        """Mock detector that looks for a simple phone-number pattern matching '555-0199'."""
        def detect(self, text: str) -> list[PIIEntity]:
            entities = []
            target = "555-0199"
            start_idx = text.find(target)
            while start_idx != -1:
                entities.append(PIIEntity(
                    text=target,
                    entity_type=PIIType.PHONE,
                    start=start_idx,
                    end=start_idx + len(target),
                    confidence=0.99,
                    source=self.name
                ))
                start_idx = text.find(target, start_idx + len(target))
            return entities

    detector = MockPhoneDetector()
    
    # Assert properties
    assert detector.name == "MockPhoneDetector"

    # Match in string
    results = detector.detect("Call me at 555-0199 today.")
    assert len(results) == 1
    assert results[0].text == "555-0199"
    assert results[0].entity_type == PIIType.PHONE
    assert results[0].start == 11
    assert results[0].end == 19
    assert results[0].confidence == 0.99
    assert results[0].source == "MockPhoneDetector"

    # Match empty return on no results
    no_results = detector.detect("Hello World")
    assert isinstance(no_results, list)
    assert len(no_results) == 0
