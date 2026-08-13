import pytest
from src.normalizer import normalize_text

def test_normalize_normal_text():
    """Verifies that clean, normal text is unchanged."""
    assert normalize_text("Hello World") == "Hello World"
    assert normalize_text("This is a simple sentence.") == "This is a simple sentence."

def test_normalize_empty_and_whitespace():
    """Verifies that empty strings or whitespace-only inputs result in empty outputs."""
    assert normalize_text("") == ""
    assert normalize_text("   ") == ""
    assert normalize_text("\n\n") == ""

def test_normalize_multiple_spaces():
    """Verifies that consecutive spaces are collapsed to a single space."""
    assert normalize_text("John    Smith") == "John Smith"
    assert normalize_text("  Alice   Bob  ") == "Alice Bob"

def test_normalize_leading_trailing_whitespace():
    """Verifies that leading and trailing whitespace are trimmed from each line."""
    assert normalize_text("   Trim Me   ") == "Trim Me"
    assert normalize_text("\tTrim Me\t") == "Trim Me"

def test_normalize_tabs():
    """Verifies that tab characters are correctly collapsed into spaces."""
    assert normalize_text("Name\tAge\tSalary") == "Name Age Salary"
    assert normalize_text("Data  \t  More Data") == "Data More Data"

def test_normalize_repeated_whitespace_mixed():
    """Verifies that mixtures of multiple spaces and tabs are cleanly collapsed."""
    assert normalize_text("Some\t \t  Text") == "Some Text"

def test_normalize_control_characters():
    """Verifies that non-spacing control/format characters are stripped safely."""
    # \x00 is null byte (Cc), \u200b is zero-width space (Cf)
    assert normalize_text("System\x00Failure") == "SystemFailure"
    assert normalize_text("Word\u200bSeparated") == "WordSeparated"

def test_normalize_unicode_compatibility():
    """Verifies that Unicode compatibility forms are normalized (NFKC)."""
    # \xa0 is a non-breaking space, which NFKC maps to standard space (\x20)
    assert normalize_text("First\xa0Second") == "First Second"
    # Full-width characters are normalized to half-width equivalents
    assert normalize_text("Ｈｅｌｌｏ") == "Hello"

def test_normalize_extraction_artifacts():
    """Verifies that soft hyphens (\xad) are safely removed (a common DOCX wrap artifact)."""
    # \xad is a soft hyphen (Cf)
    assert normalize_text("Maha\xadrashtra") == "Maharashtra"
    assert normalize_text("read\xadability") == "readability"

def test_normalize_multi_line_address():
    """Verifies that line breaks are preserved for addresses, but each line is normalized."""
    raw_address = """
        123 Main St.  
        Suite 100 \t 
        
        New York,   NY 10001
    """
    expected = (
        "123 Main St.\n"
        "Suite 100\n"
        "New York, NY 10001"
    )
    assert normalize_text(raw_address) == expected
