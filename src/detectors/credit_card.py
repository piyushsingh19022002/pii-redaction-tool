import re
from typing import List
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class CreditCardDetector(BaseDetector):
    """PII Detector for credit card numbers.

    Inherits from BaseDetector and detects common card formats (13 to 19 digits)
    with spaces or hyphens, validating them using the Luhn algorithm.
    """

    def __init__(self) -> None:
        # Regex matches sequences of 13 to 19 digits separated by optional single space/hyphen.
        # Boundary constraints prevent matching subparts of longer numeric strings.
        self.card_regex = re.compile(
            r"(?<![a-zA-Z0-9])(?:[0-9][\s-]?){12,18}[0-9](?![a-zA-Z0-9])"
        )
        # High confidence since candidates must pass the mathematical Luhn checksum
        self.confidence_level = 0.99

    @staticmethod
    def luhn_checksum(digits: str) -> bool:
        """Applies the Luhn algorithm (mod 10) to verify a digit string."""
        if not digits.isdigit():
            return False

        total = 0
        reverse_digits = digits[::-1]
        for idx, char in enumerate(reverse_digits):
            num = int(char)
            if idx % 2 == 1:
                num *= 2
                if num > 9:
                    num -= 9
            total += num

        return total % 10 == 0

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text for potential credit card numbers, validates them, and returns PIIEntity objects.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of validated PIIEntity objects of type CREDIT_CARD.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # 1. Candidate Generation
        for match in self.card_regex.finditer(text):
            raw_match = match.group(0)
            start, end = match.start(), match.end()

            # 2. Candidate Normalization (remove separators for validation only)
            normalized_digits = re.sub(r"[\s-]", "", raw_match)

            # 3. Length Validation
            if not (13 <= len(normalized_digits) <= 19):
                continue

            # 4. Luhn Validation
            if self.luhn_checksum(normalized_digits):
                # 5. PIIEntity Creation
                entities.append(PIIEntity(
                    text=raw_match,  # Preserve the exact original matched text
                    entity_type=PIIType.CREDIT_CARD,
                    start=start,
                    end=end,
                    confidence=self.confidence_level,
                    source=self.name
                ))

        return entities
