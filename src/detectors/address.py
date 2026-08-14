import re
from typing import List
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class AddressDetector(BaseDetector):
    """PII Detector for physical addresses.

    Inherits from BaseDetector and scans for standard street addresses
    with numbers, street names, unit numbers, cities, states, and zip codes.
    """

    def __init__(self) -> None:
        # Standard suffix-based address: [number] [street name] [suffix] [optional unit] [optional city/state/zip]
        # Placing unit pattern before optional city/state/zip captures it correctly and avoids truncation.
        self.suffix_regex = re.compile(
            r"\b\d+\s+[A-Z][a-zA-Z0-9\s\.\,\-\']+(?:Street|St\.|St|Avenue|Ave\.|Ave|Road|Rd\.|Rd|Boulevard|Blvd\.|Blvd|Parkway|Pkwy|Way|Drive|Dr\.|Dr)(?:,\s+(?:Apt|Suite|Unit|Apt\.|Suite\.|Unit\.)\s+[a-zA-Z0-9]+|\s+(?:Apt|Suite|Unit|Apt\.|Suite\.|Unit\.)\s+[a-zA-Z0-9]+)?(?:,\s+[A-Z][a-zA-Z\s]+)?(?:,\s+[A-Z]{2})?(?:\s+\d{5})?\b"
        )
        
        # Prefix-based address (e.g. French style): [number] [prefix word] [street name] [optional city...]
        self.prefix_regex = re.compile(
            r"\b\d+\s+(?:Boulevard|Boulevard\.|Blvd|Blvd\.|Avenue|Ave|Ave\.|Street|St|St\.|Road|Rd|Rd\.)\s+[A-Z][a-zA-Z0-9\s\.\,\-\']+(?:,\s+[A-Z][a-zA-Z\s]+)?\b"
        )
        
        # Address confidence level
        self.confidence_level = 0.85

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text for address candidates and returns PIIEntity objects.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of PIIEntity objects of type ADDRESS.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # Track matched spans to avoid duplicates
        matched_spans = set()

        # 1. Scan suffix-based addresses
        for match in self.suffix_regex.finditer(text):
            span = match.span()
            matched_spans.add(span)
            entities.append(PIIEntity(
                text=match.group(0),
                entity_type=PIIType.ADDRESS,
                start=match.start(),
                end=match.end(),
                confidence=self.confidence_level,
                source=self.name
            ))

        # 2. Scan prefix-based addresses
        for match in self.prefix_regex.finditer(text):
            span = match.span()
            # Avoid duplicating or overlapping with suffix matches
            overlap = False
            for s_start, s_end in matched_spans:
                if not (span[1] <= s_start or span[0] >= s_end):
                    overlap = True
                    break
            if not overlap:
                entities.append(PIIEntity(
                    text=match.group(0),
                    entity_type=PIIType.ADDRESS,
                    start=match.start(),
                    end=match.end(),
                    confidence=self.confidence_level,
                    source=self.name
                ))

        return entities
