from dataclasses import dataclass
from typing import Optional

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
