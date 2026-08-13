from abc import ABC, abstractmethod
from typing import List
from src.models import PIIEntity

class BaseDetector(ABC):
    """Abstract Base Class (ABC) defining the contract for all PII detectors.

    Every detector (e.g. email, phone, NER) must subclass this and implement
    the abstract `detect` method. This guarantees a common interface across
    the modular architecture.
    """

    @abstractmethod
    def detect(self, text: str) -> List[PIIEntity]:
        """Analyzes the input text and extracts any detected PIIEntity objects.

        Args:
            text: The normalized text string to analyze.

        Returns:
            A list of detected PIIEntity objects (which can be empty).
        """
        pass

    @property
    def name(self) -> str:
        """Returns the name of the detector class.

        Useful for tracking which engine detected which candidate entity.
        """
        return self.__class__.__name__
