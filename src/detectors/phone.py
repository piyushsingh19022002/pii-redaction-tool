import re
from typing import List
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class PhoneDetector(BaseDetector):
    """PII Detector for extracting phone numbers from text.

    Inherits from BaseDetector and implements regex-based extraction and
    structural validation rules, with particular focus on Indian formats
    (mobile and landline).
    """

    def __init__(self) -> None:
        # Regex patterns targeting boundaries:
        # 1. Indian Mobile numbers (10 digits starting with 6, 7, 8, or 9), with optional +91 or 91 country codes
        #    (?<!\d) ensures we do not match suffixes of larger numeric values.
        #    (?!\d) ensures we do not match prefixes of larger numeric values.
        self.mobile_regex = re.compile(
            r"(?<!\d)(?:(?:\+91|91)[\s-]?)?[6-9](?:\d{9}|\d{4}[\s-]\d{5}|\d{2}[\s-]\d{3}[\s-]\d{4})(?!\d)"
        )

        # 2. Indian Landline numbers (STD codes prefixed with country codes +91/91, or starting with 0 locally)
        #    Supports parentheses around area code, spaces/hyphens as separators.
        #    Total digit length typically ranges between 10 and 13.
        self.landline_regex = re.compile(
            r"(?<!\d)(?:(?:\+91|91)[\s-]?\(?\d{2,4}\)?|0\d{1,3})[\s-]?\d{3,4}[\s-]?\d{3,4}(?!\d)"
        )

        # Standard detector confidence for matched phone candidates
        self.confidence_level = 0.80

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text for phone number candidates, validates them structurally, and returns entities.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of validated PIIEntity objects of type PHONE.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # 1. Candidate Extraction
        candidates = []
        for match in self.mobile_regex.finditer(text):
            candidates.append((match.group(0), match.start(), match.end(), "mobile"))

        for match in self.landline_regex.finditer(text):
            candidates.append((match.group(0), match.start(), match.end(), "landline"))

        # 2. Overlap Resolution (sort descending by length, then ascending by start index)
        candidates.sort(key=lambda x: (x[2] - x[1]), reverse=True)
        accepted_ranges = []

        for raw_match, start, end, phone_type in candidates:
            # Check for overlaps with already accepted matches
            overlap = False
            for a_start, a_end in accepted_ranges:
                if not (end <= a_start or start >= a_end):
                    overlap = True
                    break
            if overlap:
                continue

            # 3. Candidate Normalization
            # Strip non-digits for validation checks
            digits_only = re.sub(r"\D", "", raw_match)

            # 4. Structural Validation
            is_valid = False
            if phone_type == "mobile":
                # With country code prefix (e.g. 919876543210): total 12 digits, local starts with 6-9
                if len(digits_only) == 12 and digits_only.startswith("91") and digits_only[2] in "6789":
                    is_valid = True
                # Without country code prefix (e.g. 9876543210): total 10 digits, starts with 6-9
                elif len(digits_only) == 10 and digits_only[0] in "6789":
                    is_valid = True
            elif phone_type == "landline":
                # Landline total digit count is typically 10 to 13 digits (with STD code)
                if 10 <= len(digits_only) <= 13:
                    if digits_only.startswith("91") or digits_only.startswith("0"):
                        # Extract the number after prefix 91 or 0
                        rem = digits_only[2:] if digits_only.startswith("91") else digits_only[1:]
                        # Must not start with '1' unless it's '11' (Delhi STD code)
                        if not rem.startswith("1") or rem.startswith("11"):
                            is_valid = True

            # 5. PIIEntity Creation
            if is_valid:
                accepted_ranges.append((start, end))
                entities.append(PIIEntity(
                    text=raw_match,  # Maintain original spacing/separators
                    entity_type=PIIType.PHONE,
                    start=start,
                    end=end,
                    confidence=self.confidence_level,
                    source=self.name
                ))

        # Re-sort final entities by start offset
        entities.sort(key=lambda x: x.start)
        return entities
