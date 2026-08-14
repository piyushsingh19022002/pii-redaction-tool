# Commit 21: Organization PII Detection Improvements

This guide details the error analysis, logic adjustments, and verification for **Commit 21** (`feat: improve organization pii detection`).

---

## 1. Commit Overview

After completing Commit 20, we evaluated the PII Redaction Pipeline and identified `ORGANIZATION` as the weakest remaining category:

```text
ORGANIZATION:
Precision = 62.50%
Recall    = 83.33%
F1-Score  = 71.43%
```

Precision (`62.50%`) was our primary concern because the system was flagging generic nouns and common abbreviations (like `"DNS"`, `"Visa"`, and `"SSN"`) as PII. In a production pipeline, this hurts usability by over-redacting safe technical terms and card brand labels.

---

## 2. Files Involved

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| [src/detectors/ner.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/detectors/ner.py) | Scans for candidates using spaCy NER and organization suffix regexes, filters out false positive terms, and corrects trailing period alignments. | Text segments | `PIIEntity` candidates |
| [tests/test_ner_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_ner_detector.py) | Contains unit and regression test assertions for name, abbreviation, and organization detection. | Mock text strings | Test results |

---

## 3. Required Flow Diagram

```text
Organization Candidate
        │
        ▼
[src/detectors/ner.py] NER / Suffix Regex Detector
        │
        ▼
[src/context/rules.py] evaluate_context()
        │
        ▼
[src/resolver.py] resolve_candidates() / Overlaps
        │
        ▼
Accepted / Rejected
        │
        ▼
[src/evaluator.py] Evaluation
        │
        ▼
FP / FN Output
        │
        ▼
Targeted Suffix Regex & Filter Improvement
```

---

## 4. Error Analysis

We identified **3 False Positives (FP)** and **1 False Negative (FN)** in the evaluation dataset.

### A. False Positives

1. **FP 1 (`ex31`)**: `"TechSolutions Inc"`
   * *Expected*: `NOT PII` (for this specific span, expected `"TechSolutions Inc."`)
   * *Actual prediction*: `"TechSolutions Inc"` (at `[36, 53)`)
   * *Root Cause*: spaCy's tokenizer splits trailing periods when double dots are present (e.g. `Inc..` -> `Inc` + `.` + `.`), causing the entity span to end right before the dot.
   * *Fix*: Implemented a span alignment loop checking if the entity ends with `Inc`/`Corp`/`Ltd`/`Co` and is immediately followed by `"."` in the original text, extending the span to include it.
2. **FP 2 (`ex42`)**: `"Visa"`
   * *Expected*: `NOT PII`
   * *Actual prediction*: `"Visa"` (at `[0, 4)`)
   * *Root Cause*: spaCy classified the credit card brand `"Visa"` as an `ORG`.
   * *Fix*: Added card brands to the filtered terms list.
3. **FP 3 (`ex54`)**: `"DNS"`
   * *Expected*: `NOT PII`
   * *Actual prediction*: `"DNS"` (at `[4, 7)`)
   * *Root Cause*: spaCy classified the network protocol abbreviation `"DNS"` as an `ORG`.
   * *Fix*: Added protocol abbreviations to the filtered terms list.

### B. False Negative

1. **FN 1 (`ex31`)**: `"TechSolutions Inc."`
   * *Expected*: `"TechSolutions Inc."` (at `[36, 54)`)
   * *Actual prediction*: *nothing* (missed because only the dotless `"TechSolutions Inc"` was returned)
   * *Root Cause*: The same tokenizer split issue described in FP 1.
   * *Fix*: Extended the token span using the alignment loop, resolving the FN.

---

## 5. Precision

The baseline organization detector had poor precision (`62.50%`) because NER models are trained on general text corpuses where protocol abbreviations (like `DNS`) or card names (like `Visa`) are tagged as `ORG` (organization). Without post-filtering, these generic terms are incorrectly flagged as PII.

---

## 6. Recall

We missed `"TechSolutions Inc."` because the tokenizer separated the abbreviation period from the word. We recovered it by checking the adjacent character in the source text and modifying the `org_pattern` regex to use lookaheads `(?![a-zA-Z0-9])` instead of word boundaries `\b`, allowing dot boundaries to match correctly even in double-period layouts like `Inc..`.

---

## 7. NER + Context + Resolver Integration

1. **NER**: Generates initial candidate spans with a default confidence (e.g., `0.85`).
2. **Context**: Scans the candidate's neighborhood for keywords (`company`, `registered office`).
3. **Resolver**: Adds a context bonus (`+0.15`) or penalty (`-0.30`) and filters candidates below the `0.70` threshold, ensuring only verified candidates are accepted.

---

## 8. Regression Tests

We added regression checks in [tests/test_ner_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_ner_detector.py):
* **False Positive Check**: Asserts `"Visa"`, `"DNS"`, and `"SSN"` are ignored.
* **False Negative Check**: Asserts `"TechSolutions Inc."` is matched cleanly with the period.
* **Correct Examples**: Verifies `"Google LLC"` and `"Acme Corporation"`.
* **Realistic Additions**: Verifies `"Amazon Web Services Inc."` and `"SpaceX Corp."`.
* **Negative Formatting Check**: Verifies generic terms like `"limited liability"` are ignored.

---

## 9. Before vs After Metrics

| Metric | Before (Baseline) | After (Improved) | Change |
| :--- | :--- | :--- | :--- |
| **Precision** | `0.6250` | `1.0000` | **+0.3750** |
| **Recall** | `0.8333` | `1.0000` | **+0.1667** |
| **F1-Score** | `0.7143` | `1.0000` | **+0.2857** |
| **False Positives (FP)**| 3 | 0 | **-3 FPs** |
| **False Negatives (FN)**| 1 | 0 | **-1 FN** |

---

## 10. Connection Between Commits

```text
Commit 18 (Evaluation)
Exposed evaluation framework and dataset metrics.
    ↓
Commit 19 (Dataset Expansion)
Expanded synthetic ground truth for robust testing.
    ↓
Commit 20 (Address Improvement)
Fixed address extraction and resolved truncation.
    ↓
Commit 21 (Organization Improvement) [THIS COMMIT]
Filtered card brands/technical terms and aligned trailing periods.
    ↓
Commit 22 (Phone Improvement)
Future improvements.
```

---

## 11. Common Beginner Mistakes

* **Trusting NER Blindly**: spaCy is powerful, but it makes context-dependent mistakes (e.g. tagging `"DNS"` or `"Visa"` as `ORG`). Always implement post-filtering.
* **Adding Static Company Lists**: Hardcoding lists of specific company names doesn't scale to new documents.
* **Overly Broad Suffix Regexes**: Using broad patterns that catch phrases like `"limited liability"` as positive organizations.
* **Ignoring False Positives**: Focusing only on recall while ignoring precision leads to over-redacted documents.
* **Altering Ground Truth to Fit Predictions**: Modifying `ground_truth.json` to make scores look better instead of fixing the code.
* **Lacking Regression Tests**: Fixing a bug without adding a unit test to prevent it from returning.

---

## 12. Interview Questions

### "Why did you need context for organization detection?"
"While suffix regexes match corporate suffixes, general business terms or card types can easily trigger false positives. Evaluating context keywords (like `issuer` or `registered office`) helps the resolver mathematically filter out generic nouns from actual organizations."

### "How did you reduce false positives?"
"We added technical/protocol terms (`"DNS"`) and credit card brands (`"Visa"`) to a blacklist inside the detector, preventing spaCy's over-predictions from passing through."

### "How did you handle NER errors?"
"We corrected span tokenization failures (where tokenizer separated trailing abbreviation periods) by checking the next character in the source text and extending the character span bounds to include the dot."

### "How did you ensure your fix generalized?"
"We implemented lookaheads and structural span alignment rather than hardcoding names, and wrote regression tests with generic negative examples."

### "How did you measure improvement?"
"By running `python -m scripts.evaluate` to calculate micro-averaged precision, recall, and F1 on our evaluation dataset before and after the change."

---

## 13. Quick Revision

### 5 Key Concepts
1. **Span Alignment**: Modifying bounds to capture trailing abbreviation periods.
2. **Post-NER Filtering**: Blacklisting common nouns and brand names.
3. **Negative Lookahead**: `(?![a-zA-Z0-9])` used to assert boundaries without failing on trailing dots.
4. **Precision Preservation**: Ensuring recall fixes do not cause new false alarms.
5. **Regression Verification**: Testing against fixed bugs to prevent regression.

### 3 Interview Questions
1. *Why does spaCy's tokenizer split periods in `Inc..`?*
2. *Why do we use negative lookahead instead of word boundaries for abbreviation suffix regexes?*
3. *What is the difference between a false positive and a false negative for organization PII?*

### 3 Practical Examples
1. **Span Correction**: Parse `"TechSolutions Inc."` fully instead of truncating to `"TechSolutions Inc"`.
2. **Abbreviation Check**: Match `"SpaceX Corp."` but reject `"corporation policy"`.
3. **Blacklist Filter**: Successfully skip `"Visa"` or `"DNS"` in prose.
