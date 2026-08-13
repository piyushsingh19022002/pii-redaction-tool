from dataclasses import dataclass
from enum import Enum
from typing import Optional

class PIIType(Enum):
    """Supported categories of Personally Identifiable Information (PII)."""
    PERSON = "PERSON"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ORGANIZATION = "ORGANIZATION"
    ADDRESS = "ADDRESS"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    DOB = "DOB"
    IP_ADDRESS = "IP_ADDRESS"

@dataclass(frozen=True)
class PIIEntity:
    """Represents a single detected instance of Personally Identifiable Information (PII).

    This model is immutable (frozen) to ensure that detection events are not
    accidentally mutated as they pass through the resolution, validation,
    and pseudonymization pipeline.

    Attributes:
        text: The exact original text detected (un-normalized).
        entity_type: The classified PII category (PIIType enum).
        start: Start character offset (inclusive) within the analyzed text segment.
        end: End character offset (exclusive) within the analyzed text segment.
        confidence: Floating-point value representing detection confidence (range: 0.0 to 1.0).
        source: The mechanism that produced the entity (e.g. 'regex', 'ner', 'context').
    """
    text: str
    entity_type: PIIType
    start: int
    end: int
    confidence: float
    source: str

    def __post_init__(self):
        # 1. Type and value validations
        if self.text is None:
            raise ValueError("text cannot be None")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")

        if not isinstance(self.entity_type, PIIType):
            raise TypeError("entity_type must be a member of the PIIType enum")

        if not isinstance(self.start, int) or self.start < 0:
            raise ValueError("start index must be a non-negative integer")

        if not isinstance(self.end, int) or self.end < self.start:
            raise ValueError("end index must be an integer greater than or equal to the start index")

        # Support both float and int types for confidence representation (e.g. 1 or 1.0)
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be a number between 0.0 and 1.0 inclusive")

        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")

@dataclass
class TextSegment:
    """Represents an extracted unit of text from a DOCX document.

    Preserves structural metadata to locate exactly where the text
    came from, facilitating future document reconstruction.
    """
    text: str
    segment_type: str  # "paragraph" or "table-cell"

    # Metadata for paragraph segments
    paragraph_index: Optional[int] = None

    # Metadata for table-cell segments
    table_index: Optional[int] = None
    row_index: Optional[int] = None
    cell_index: Optional[int] = None

    # Normalized text for PII detection
    normalized_text: Optional[str] = None

@dataclass(frozen=True)
class ContextEvidence:
    """Represents contextual evidence gathered around a candidate PIIEntity.

    Attributes:
        has_positive: Boolean indicating if supporting context was found.
        has_negative: Boolean indicating if contradicting/negative context was found.
        matched_keyword: The actual keyword string that matched, or None.
        matched_rule: Name/ID of the rule that matched, or None.
        distance: Optional character distance of the match from candidate boundaries, or None.
    """
    has_positive: bool
    has_negative: bool
    matched_keyword: Optional[str] = None
    matched_rule: Optional[str] = None
    distance: Optional[int] = None
