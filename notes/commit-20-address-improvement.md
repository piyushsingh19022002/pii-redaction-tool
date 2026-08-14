# Commit 20: Address PII Detection Improvements

This guide details the error analysis, architectural refactoring, and code changes implemented in **Commit 20** (`feat: improve address pii detection`).

---

## 1. Baseline ADDRESS Metrics

Computed on [evaluation/ground_truth.json](file:///Users/piyushsengar/Desktop/pii-redaction-tool/evaluation/ground_truth.json):

* **Precision**: `0.7500`
* **Recall**: `0.5000`
* **F1-Score**: `0.6000`

---

## 2. False Positives & False Negatives (Error Analysis)

### A. False Negatives (FN)

1. **FN 1 (`ex33`)**: `"456 Oak Avenue, Apt 2B, Chicago, IL"`
   * *Ground Truth*: `[31, 66) 456 Oak Avenue, Apt 2B, Chicago, IL`
   * *Predicted*: `[31, 51) 456 Oak Avenue, Apt ` (Truncated)
   * *Root Cause*: Sub-pattern overlap. The optional city match `(?:,\s+[A-Z][a-zA-Z\s]+)?` matched the unit prefix `", Apt "`, cutting off the rest of the unit name `"2B"` (which begins with a number) and causing truncation.
2. **FN 2 (`ex35`)**: `"101 Boulevard Saint-Germain, Paris"`
   * *Ground Truth*: `[36, 70) 101 Boulevard Saint-Germain, Paris`
   * *Predicted*: `nothing`
   * *Root Cause*: Suffix assumption. The existing address patterns expected the road suffix (e.g. `Boulevard`) to appear *after* the name (e.g. `Saint-Germain Boulevard`), missing prefix-based structures (French style).
3. **FN 3 (`ex36`)**: `"505 Broadway Ave, Seattle, WA 98101"`
   * *Ground Truth*: `[28, 63) 505 Broadway Ave, Seattle, WA 98101`
   * *Predicted*: `nothing`
   * *Root Cause*: The suffix regex only matched `"Ave."` (with dot), missing `"Ave"` (without dot). Additionally, there was no support for trailing 5-digit ZIP codes.

### B. False Positive (FP)

1. **FP 1 (`ex33`)**: `"456 Oak Avenue, Apt "`
   * *Ground Truth*: `NOT PII` (for this truncated span)
   * *Predicted*: `[31, 51) 456 Oak Avenue, Apt (ADDRESS)`
   * *Root Cause*: Mismatched boundaries resulting from the sub-pattern overlap described in FN 1.

---

## 3. Implementation Flow Diagram

```text
Evaluation
    ↓
ADDRESS FP/FN
    ↓
Root Cause
    ↓
Address detector/context/resolver
    ↓
Regression Tests
    ↓
Evaluation
    ↓
Before vs After
```

#### Actual Files & Functions:
* **Detector**: [src/detectors/address.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/detectors/address.py) containing `AddressDetector.detect()`.
* **Registry**: [src/pipeline.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/pipeline.py) registering `AddressDetector()`.
* **Cleanup**: [src/detectors/ner.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/detectors/ner.py) removing regex-based address parsing.
* **Tests**: [tests/test_address_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_address_detector.py) and [tests/test_ner_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_ner_detector.py).

---

## 4. Code Changes & Architectural Refactoring

Instead of adding complex rules inside `NERDetector`, we made a clean architectural refactoring by extracting address logic into its own standalone detector:

1. **Standalone Detector** (`src/detectors/address.py`):
   * Created `AddressDetector` checking both suffix-based and prefix-based street address layouts.
   * Placed unit checks (`Apt`, `Suite`, etc.) *before* optional city/state/zip blocks to capture unit numbers completely and prevent truncation.
   * Added support for trailing 5-digit ZIP codes and suffix abbreviations without dots.
2. **NER Clean-up** (`src/detectors/ner.py`):
   * Deleted address matching loops to keep NER focused exclusively on spacy entity categorization (`PERSON` and `ORGANIZATION`).
3. **Pipeline Registration** (`src/pipeline.py`):
   * Lazy-imported and added `AddressDetector` to the active detectors registry.

---

## 5. Regression Tests

We added regression checks in [tests/test_address_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_address_detector.py) to protect against these errors returning:
* `test_regression_ex33_unit_truncation`: Asserts unit numbers are parsed completely.
* `test_regression_ex35_french_prefix`: Asserts prefix road structures match.
* `test_regression_ex36_abbreviation_zip`: Asserts zip codes and non-dotted suffixes match.
* `test_general_negative_cases`: Asserts standard prose containing street, road, city, or address keywords are safely ignored (preventing false positive creep).

---

## 6. Before-vs-After Metrics

### ADDRESS Class Metrics
* **Precision**: `0.7500` → `1.0000` (**+0.2500**)
* **Recall**: `0.5000` → `1.0000` (**+0.5000**)
* **F1-Score**: `0.6000` → `1.0000` (**+0.4000**)

### Overall Micro Metrics
* **Precision**: `0.9180` → `0.9365` (**+0.0185**)
* **Recall**: `0.9333` → `0.9833` (**+0.0500**)
* **F1-Score**: `0.9256` → `0.9593` (**+0.0337**)

---

## 7. Precision/Recall Tradeoff & Limitations

* **Tradeoff**: Adding prefix-based address patterns (like matching ` Boulevard [Capitalized]`) could increase false positives on general texts (e.g. `"2 Boulevard books"`). To prevent this, we enforce:
  1. Mandatory numeric leading digit (`\b\d+\s+`).
  2. Capitalized street names.
* **Limitations**: The address regex relies on numeric street numbers. Unnumbered general locations (like `"Registered Office, Saint-Germain, Paris"`) will be missed unless flagged by NER.
