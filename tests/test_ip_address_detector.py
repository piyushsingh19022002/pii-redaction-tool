import pytest
from src.detectors.ip_address import IPDetector
from src.models import PIIType

@pytest.fixture
def detector():
    return IPDetector()

def test_valid_ipv4(detector):
    """Verifies that standard valid IPv4 addresses are detected."""
    text = "The server is hosted at 192.168.1.1."
    results = detector.detect(text)
    
    assert len(results) == 1
    entity = results[0]
    assert entity.text == "192.168.1.1"
    assert entity.entity_type == PIIType.IP_ADDRESS
    assert entity.start == 24
    assert entity.end == 35
    assert entity.confidence == 0.98
    assert entity.source == "IPDetector"

def test_multiple_ipv4(detector):
    """Verifies that multiple IPv4 addresses are all detected with correct offsets."""
    text = "Routing from 10.0.0.1 to 10.0.0.254."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "10.0.0.1"
    assert results[1].text == "10.0.0.254"
    assert text[results[0].start : results[0].end] == "10.0.0.1"
    assert text[results[1].start : results[1].end] == "10.0.0.254"

def test_valid_ipv6(detector):
    """Verifies that full-form valid IPv6 addresses are detected."""
    text = "Connecting to 2001:0db8:85a3:0000:0000:8a2e:0370:7334."
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].text == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"

def test_compressed_ipv6(detector):
    """Verifies compressed IPv6 representations (using double colons)."""
    text = "Server Fe80::1 and database 2001:db8::1 are active."
    results = detector.detect(text)
    
    assert len(results) == 2
    # re.findall/finditer is case-insensitive for hex due to regex classes
    assert results[0].text.lower() == "fe80::1"
    assert results[1].text == "2001:db8::1"

def test_loopback_ips(detector):
    """Verifies detection of loopback addresses for both IPv4 and IPv6."""
    text = "Local hosts: 127.0.0.1 and ::1."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "127.0.0.1"
    assert results[1].text == "::1"

def test_invalid_ipv4_discarded(detector):
    """Verifies that syntactically matching but logically invalid IPv4 addresses are discarded."""
    assert len(detector.detect("999.999.999.999")) == 0  # Octets out of range
    assert len(detector.detect("256.1.1.1")) == 0
    assert len(detector.detect("1.2.3.999")) == 0

def test_invalid_ipv6_discarded(detector):
    """Verifies that malformed IPv6 strings are ignored."""
    assert len(detector.detect("2001:db8::g1")) == 0  # Invalid hex letter 'g'
    assert len(detector.detect("abcd:efgh::1")) == 0  # Invalid hex letter 'g', 'h'

def test_ip_followed_by_punctuation(detector):
    """Verifies that trailing punctuation is excluded from the match."""
    r1 = detector.detect("Server IP: 192.168.1.1.")
    assert len(r1) == 1
    assert r1[0].text == "192.168.1.1"

    r2 = detector.detect("IP: 192.168.1.1, or ::1.")
    assert len(r2) == 2
    assert r2[0].text == "192.168.1.1"
    assert r2[1].text == "::1"

def test_ip_surrounded_by_text(detector):
    """Verifies IP detection when embedded in surrounding strings."""
    text = "host=192.168.1.1;port=80"
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "192.168.1.1"

def test_no_ip_address(detector):
    """Verifies empty list returned if no IP exists."""
    assert len(detector.detect("No IP address in this sentence.")) == 0

def test_duplicate_ips(detector):
    """Verifies that multiple occurrences of the same IP are returned individually."""
    text = "Ping 8.8.8.8 then ping 8.8.8.8 again."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].text == "8.8.8.8"
    assert results[1].text == "8.8.8.8"
    assert results[0].start != results[1].start

def test_numeric_non_ip_rejection(detector):
    """Verifies that dates, version numbers, and decimal numbers are ignored."""
    # Dates
    assert len(detector.detect("2026.08.13")) == 0
    # Version numbers
    assert len(detector.detect("Version 4.0.0")) == 0
    assert len(detector.detect("v1.2.3.4")) == 0
    # Large numbers
    assert len(detector.detect("100.000.000")) == 0
