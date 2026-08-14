import os
import pathlib
import pytest

@pytest.fixture
def report_content():
    report_path = pathlib.Path("evaluation") / "final_evaluation_report.md"
    assert report_path.exists(), "The final evaluation report was not generated!"
    return report_path.read_text(encoding="utf-8")

def test_report_sections_exist(report_content):
    """Verifies that all required sections exist in the report."""
    assert "## 1. Evaluation Methodology" in report_content
    assert "## 2. Metric Definitions & Calculations" in report_content
    assert "## 3. Final Evaluation Results" in report_content
    assert "## 4. Baseline vs Final Comparison" in report_content
    assert "## 5. Per-PII Interpretation" in report_content
    assert "## 6. Real-Document Smoke Test" in report_content
    assert "## 7. Pipeline Limitations" in report_content

def test_report_contains_metrics(report_content):
    """Verifies that precision, recall, accuracy, and F1 calculations appear in the report."""
    assert "Precision" in report_content
    assert "Recall" in report_content
    assert "Accuracy" in report_content
    assert "F1-Score" in report_content or "F1" in report_content

def test_report_contains_pii_types(report_content):
    """Verifies that all required PII types appear in the results table."""
    pii_types = [
        "PERSON", "EMAIL", "PHONE", "ORGANIZATION", "ADDRESS",
        "SSN", "CREDIT_CARD", "DOB", "IP_ADDRESS", "OVERALL (MICRO)"
    ]
    for t in pii_types:
        assert t in report_content

def test_report_contains_caveat(report_content):
    """Verifies that the important Accuracy Caveat is included."""
    assert "Accuracy Caveat" in report_content or "Accuracy is calculated only over the explicitly annotated candidate" in report_content

def test_report_contains_baseline_comparison(report_content):
    """Verifies that the stage-by-stage improvements are documented."""
    assert "Initial expanded benchmark" in report_content
    assert "After Address" in report_content
    assert "After Organization" in report_content
    assert "Final" in report_content

def test_no_raw_real_pii_in_report(report_content):
    """Ensures no raw, real sensitive mock PII values leak into the documentation report."""
    raw_pii_leaks = [
        "john@example.com", "9876543210", "4111-1111-1111-1111", 
        "U74999MH2018PTC307777", "1600 Amphitheatre Parkway"
    ]
    for leak in raw_pii_leaks:
        assert leak not in report_content
