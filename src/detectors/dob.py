import re
import datetime
from typing import List, Optional
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class DOBDetector(BaseDetector):
    """PII Detector for Date of Birth (DOB).

    Inherits from BaseDetector, parses common date formats, validates they represent
    real calendar dates, and verifies the presence of local contextual keywords.
    """

    def __init__(self) -> None:
        # DD-MM-YYYY or MM-DD-YYYY or DD.MM.YYYY etc.
        self.date_pattern_1 = re.compile(
            r"(?<![a-zA-Z0-9])\d{1,2}[/\.-]\d{1,2}[/\.-]\d{4}(?![a-zA-Z0-9])"
        )
        # YYYY-MM-DD or YYYY.MM.DD etc.
        self.date_pattern_2 = re.compile(
            r"(?<![a-zA-Z0-9])\d{4}[/\.-]\d{1,2}[/\.-]\d{1,2}(?![a-zA-Z0-9])"
        )
        # Month DD, YYYY (case-insensitive)
        self.date_pattern_3 = re.compile(
            r"(?<![a-zA-Z0-9])(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-zA-Z]*\s+\d{1,2},\s+\d{4}(?![a-zA-Z0-9])",
            re.IGNORECASE
        )
        # DD Month YYYY (case-insensitive)
        self.date_pattern_4 = re.compile(
            r"(?<![a-zA-Z0-9])\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-zA-Z]*\s+\d{4}(?![a-zA-Z0-9])",
            re.IGNORECASE
        )

        # Context boundary check regex.
        # Checks for keywords as complete words inside the local context windows.
        self.context_regex = re.compile(
            r"\b(date of birth|dob|birth date|birthdate|born on|born)\b",
            re.IGNORECASE
        )

        # Standard detector confidence for a structurally and contextually verified DOB match
        self.confidence_level = 0.90

    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Determines if a candidate string represents a valid calendar date and birth year."""
        cleaned = re.sub(r"\s+", " ", date_str.strip())
        current_year = datetime.datetime.now().year

        # 1. Try parsing textual month formats (case-insensitive conversion)
        text_formats = [
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y"
        ]
        for fmt in text_formats:
            try:
                dt = datetime.datetime.strptime(cleaned, fmt)
                if 1900 <= dt.year <= current_year:
                    return True
            except ValueError:
                continue

        # 2. Try parsing numeric formats (normalize separators first)
        normalized_numeric = re.sub(r"[/\.]", "-", cleaned)
        numeric_formats = [
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%Y-%d-%m"
        ]
        for fmt in numeric_formats:
            try:
                dt = datetime.datetime.strptime(normalized_numeric, fmt)
                if 1900 <= dt.year <= current_year:
                    return True
            except ValueError:
                continue

        return False

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text for date candidates, validates them, checks local context, and returns PIIEntity objects.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of validated PIIEntity objects of type DOB.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # 1. Candidate Generation
        candidates = []
        for match in self.date_pattern_1.finditer(text):
            candidates.append((match.group(0), match.start(), match.end()))
        for match in self.date_pattern_2.finditer(text):
            candidates.append((match.group(0), match.start(), match.end()))
        for match in self.date_pattern_3.finditer(text):
            candidates.append((match.group(0), match.start(), match.end()))
        for match in self.date_pattern_4.finditer(text):
            candidates.append((match.group(0), match.start(), match.end()))

        # 2. Overlap Resolution (sort descending by length, then ascending by start index)
        candidates.sort(key=lambda x: (x[2] - x[1]), reverse=True)
        accepted_ranges = []

        for raw_match, start, end in candidates:
            # Check for overlaps with already accepted matches
            overlap = False
            for a_start, a_end in accepted_ranges:
                if not (end <= a_start or start >= a_end):
                    overlap = True
                    break
            if overlap:
                continue

            # 3. Calendar-Date Validation
            if not self.validate_date(raw_match):
                continue

            # 4. Local Context Inspection
            # Check 30 characters before and after the matched candidate string
            context_before = text[max(0, start - 30):start]
            context_after = text[end:min(len(text), end + 30)]

            has_context = bool(
                self.context_regex.search(context_before) or
                self.context_regex.search(context_after)
            )

            # 5. PIIEntity Creation
            if has_context:
                accepted_ranges.append((start, end))
                entities.append(PIIEntity(
                    text=raw_match,  # Original unmodified string
                    entity_type=PIIType.DOB,
                    start=start,
                    end=end,
                    confidence=self.confidence_level,
                    source="context"
                ))

        # Re-sort final entities by start offset
        entities.sort(key=lambda x: x.start)
        return entities
