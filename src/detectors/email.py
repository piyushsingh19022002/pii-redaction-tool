import re
from typing import List
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class EmailDetector(BaseDetector):
    """PII Detector for extracting email addresses from text.

    Inherits from BaseDetector and implements regex-based matching for
    common and practical email patterns.
    """

    def __init__(self) -> None:
        # Regular expression breakdown:
        # - Local part: [a-zA-Z0-9._%+-]+ (letters, digits, dots, underscores, percents, plus, hyphens)
        # - Separator: @
        # - Domain start: [a-zA-Z0-9] (must start with alphanumeric character)
        # - Domain body: [a-zA-Z0-9.-]* (alphanumeric, dots, hyphens)
        # - TLD: \.[a-zA-Z]{2,} (dot followed by at least two letters, e.g. .com, .edu, .co, .in)
        self.email_regex = re.compile(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}"
        )
        # Standard confidence score for a structurally valid email matched by regex.
        # Set to 0.95 because email regex matches are highly reliable.
        self.confidence_level = 0.95

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text for email address candidates.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of detected PIIEntity objects of type EMAIL.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # Search for all matches using finditer to capture offsets
        for match in self.email_regex.finditer(text):
            email_text = match.group(0)
            start_offset = match.start()
            end_offset = match.end()

            entities.append(PIIEntity(
                text=email_text,
                entity_type=PIIType.EMAIL,
                start=start_offset,
                end=end_offset,
                confidence=self.confidence_level,
                source=self.name
            ))

        return entities
