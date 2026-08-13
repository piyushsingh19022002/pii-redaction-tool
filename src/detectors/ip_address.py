import re
import ipaddress
from typing import List
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class IPDetector(BaseDetector):
    """PII Detector for extracting IPv4 and IPv6 addresses from text.

    Inherits from BaseDetector and uses regex-based candidate generation
    followed by validation using the standard 'ipaddress' library module.
    """

    def __init__(self) -> None:
        # IPv4 pattern: 4 groups of 1-3 digits separated by dots.
        # Boundary constraints prevent matching subparts of version numbers (like v1.2.3.4) or dates.
        self.ipv4_regex = re.compile(
            r"(?<![a-zA-Z0-9])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![a-zA-Z0-9])"
        )

        # IPv6 pattern: Matches blocks of 1-4 hex digits separated by colons, including compressed forms (::).
        # Boundary constraints prevent matching substrings of invalid hex strings (like 2001:db8::g1).
        self.ipv6_regex = re.compile(
            r"(?<![a-zA-Z0-9:])(?:[0-9a-fA-F]{1,4}:|:){1,7}(?:[0-9a-fA-F]{1,4}|:)(?![a-zA-Z0-9:])"
        )

        # High confidence score because candidate matches are validated using Python's standard library ipaddress module.
        self.confidence_level = 0.98

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text for IPv4 and IPv6 address candidates, validates them, and returns PIIEntity objects.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of validated PIIEntity objects of type IP_ADDRESS.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # 1. Candidate Generation
        candidates = []
        
        # Search for IPv4 candidates
        for match in self.ipv4_regex.finditer(text):
            candidates.append((match.group(0), match.start(), match.end()))

        # Search for IPv6 candidates
        for match in self.ipv6_regex.finditer(text):
            candidates.append((match.group(0), match.start(), match.end()))

        # 2. Overlap Resolution
        # Sort candidates by match length descending, then by start index ascending
        candidates.sort(key=lambda x: (x[2] - x[1]), reverse=True)
        accepted_ranges = []

        for raw_match, start, end in candidates:
            # Check for overlap with already accepted spans
            overlap = False
            for a_start, a_end in accepted_ranges:
                if not (end <= a_start or start >= a_end):
                    overlap = True
                    break
            if overlap:
                continue

            # 3. IP Validation using standard library ipaddress module
            try:
                # ipaddress.ip_address parses both IPv4 and IPv6 strings
                ipaddress.ip_address(raw_match)
                
                # If valid, accept the range and create the entity
                accepted_ranges.append((start, end))
                entities.append(PIIEntity(
                    text=raw_match,  # Original unmodified string
                    entity_type=PIIType.IP_ADDRESS,
                    start=start,
                    end=end,
                    confidence=self.confidence_level,
                    source=self.name
                ))
            except ValueError:
                # Discard candidates that fail standard IP validation (e.g. out of range)
                continue

        # Sort final list of entities by start index
        entities.sort(key=lambda x: x.start)
        return entities
