import re
import unicodedata

def normalize_text(text: str) -> str:
    """Normalizes document text conservatively for better PII detection.

    Applies Unicode NFKC normalization, removes non-spacing control/format
    characters (like soft hyphens or zero-width spaces), collapses multiple
    spaces and tabs into a single space, and preserves meaningful line breaks
    (useful for multi-line physical addresses).

    Args:
        text: The raw input string.

    Returns:
        The normalized string.
    """
    if not text:
        return ""

    # Apply standard Unicode NFKC normalization
    # This maps full-width characters to half-width, normalizes compatibility
    # characters, and converts non-breaking spaces (\xa0) to standard spaces (\x20).
    normalized = unicodedata.normalize("NFKC", text)

    # Split the text by line boundaries to preserve line structure (e.g. for addresses)
    lines = normalized.splitlines()
    normalized_lines = []

    for line in lines:
        # Remove control/format characters (Category starting with 'C' in Unicode)
        # We explicitly preserve tabs (\t) here, as they are collapsed to spaces next.
        cleaned_chars = []
        for char in line:
            category = unicodedata.category(char)
            if category.startswith("C") and char != "\t":
                continue
            cleaned_chars.append(char)
        line_str = "".join(cleaned_chars)

        # Collapse consecutive spaces and tabs into a single space, and strip outer margins
        line_str = re.sub(r"[ \t]+", " ", line_str).strip()

        # Keep only non-empty lines to clean up redundant spacing
        if line_str:
            normalized_lines.append(line_str)

    # Rejoin lines with a clean single newline character
    return "\n".join(normalized_lines)
