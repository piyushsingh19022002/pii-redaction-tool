import re
from typing import List
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class SSNDetector(BaseDetector):
    """PII Detector for U.S. Social Security Numbers (SSN).

    Inherits from BaseDetector and scans for formatted SSNs (XXX-XX-XXXX),
    verifying structural constraints for area, group, and serial numbers.
    """

    def __init__(self) -> None:
        # Regex matches formatted SSN candidates. Capturing groups extract AAA, GG, and SSSS.
        # Alphanumeric lookahead/lookbehind boundaries prevent matching substrings of longer tokens.
        self.ssn_regex = re.compile(
            r"(?<![a-zA-Z0-9])(\d{3})-(\d{2})-(\d{4})(?![a-zA-Z0-9])"
        )
        # Standard detector confidence for a structurally verified formatted SSN match
        self.confidence_level = 0.95

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text for formatted SSN candidates, validates them, and returns PIIEntity objects.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of validated PIIEntity objects of type SSN.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # 1. Candidate Generation
        for match in self.ssn_regex.finditer(text):
            raw_match = match.group(0)
            start, end = match.start(), match.end()
            
            aaa = match.group(1)
            gg = match.group(2)
            ssss = match.group(3)

            # 2. Structural Validation
            # - AAA (Area number) cannot be "000", "666", or in range 900-999.
            # - GG (Group number) cannot be "00".
            # - SSSS (Serial number) cannot be "0000".
            if aaa == "000" or aaa == "666" or (900 <= int(aaa) <= 999):
                continue
            if gg == "00":
                continue
            if ssss == "0000":
                continue

            # 3. PIIEntity Creation
            entities.append(PIIEntity(
                text=raw_match,  # Original unmodified string
                entity_type=PIIType.SSN,
                start=start,
                end=end,
                confidence=self.confidence_level,
                source=self.name
            ))

        return entities
