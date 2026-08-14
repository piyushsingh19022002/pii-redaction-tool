# Commit 22: Phone PII Precision Improvements

This guide details the error analysis, logic adjustments, and verification for **Commit 22** (`feat: improve phone pii precision`).

---

## 1. Commit Overview

After completing Commit 21, the only remaining False Positive in our entire evaluation suite was a single `PHONE` error:

```text
PHONE Class Metrics:
Precision = 85.71%
Recall    = 100.00%
F1-Score  = 92.31%
```

Since Recall was already at `100.00%` (meaning we were successfully catching all actual phone numbers), this was strictly a **precision problem** (we were capturing a non-phone number as a phone number). The goal was to remove the single False Positive without degrading our perfect recall.

---

## 2. Files Involved

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| [src/detectors/phone.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/detectors/phone.py) | Scans text for phone number candidates (mobile and landline formats) and outputs candidate `PIIEntity` objects with a baseline confidence. | Text segments | `PIIEntity` candidates |
| [tests/test_phone_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_phone_detector.py) | Verifies the phone regex patterns and resolver logic against positive, negative, and conflicting context cases. | Mock strings | Test assertions |

---

## 3. Required Flow Diagram

```text
PHONE candidate
      │
      ▼
[src/detectors/phone.py] PhoneDetector
      │
      ▼
[src/context/rules.py] evaluate_context()
      │
      ▼
[src/resolver.py] resolve_candidates()
      │
      ▼
Accepted / Rejected Decision
      │
      ▼
[src/evaluator.py] Evaluation
      │
      ▼
False Positive Identified (ex58)
      │
      ▼
Targeted Fix (Reduce Baseline Confidence to 0.80)
      │
      ▼
[tests/test_phone_detector.py] Regression Test
      │
      ▼
Re-evaluation (All 100% metrics)
```

---

## 4. False Positive

We identified exactly one False Positive in the expanded dataset:

* **Text**: `"Ticket ID 98765-43210 is not a valid mobile phone number."`
* **Predicted**: `[10, 21) "98765-43210"` (identified as `PHONE`)
* **Ground-Truth**: `NOT PII` (specifically, it is classified as `non_pii` for PHONE).
* **Why it was incorrectly matched**:
  The pattern `"98765-43210"` matched our Indian mobile phone regex.
  When resolving context, the resolver matched:
  * A positive suffix: `"mobile phone number"` (giving `+0.15` bonus).
  * A negative prefix: `"Ticket ID"` (giving `-0.30` penalty).
  With the default detector confidence of `0.90`, the conflicting context score was:
  $$\text{Score} = 0.90 + 0.15 - 0.30 = 0.75$$
  Since $0.75 \ge 0.70$ (the resolver acceptance threshold), the candidate was accepted as PII, producing the False Positive.

---

## 5. Fix

* **What Changed**: We reduced the default `confidence_level` inside `PhoneDetector` from `0.90` to `0.80`.
* **Why it Works**:
  Under the new math, a candidate in a conflicting context calculates:
  $$\text{Score} = 0.80 + 0.15 - 0.30 = 0.65$$
  Since $0.65 < 0.70$, the resolver now rejects this candidate, eliminating the False Positive.
* **Why it Generalizes**: It applies the same mathematical resolution logic we established for DOB in Commit 19. It avoids hardcoding `"98765-43210"`.
* **Why it doesn't harm valid phone detection**:
  * Phone numbers with positive context (or no context) will score `0.95` or `0.80` respectively, which are both $\ge 0.70$, remaining accepted.

---

## 6. Precision vs Recall

* **Precision**: *"Of detected phone numbers, how many were actually phones?"*
  * High precision means zero false alarms (we do not redact order/ticket IDs).
* **Recall**: *"Of actual phone numbers, how many did we detect?"*
  * High recall means zero leaked phone numbers (we redact all actual PII).

This commit focused exclusively on precision, since we already had 100% recall.

---

## 7. Regression Tests

We added regression checks in [tests/test_phone_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_phone_detector.py):
* `test_6_true_positives_detection`: Asserts that all 6 ground-truth true positive PHONE formats from the evaluation set are successfully scanned by the detector.
* `test_phone_pipeline_regression_ex58`: Asserts that `"Ticket ID 98765-43210..."` is rejected as PHONE due to the negative context penalty.

---

## 8. Before vs After Metrics

### PHONE Metrics
* **Precision**: `0.8571` → `1.0000` (**+0.1429**)
* **Recall**: `1.0000` → `1.0000` (Unchanged)
* **F1-Score**: `0.9231` → `1.0000` (**+0.0769**)
* **False Positives (FP)**: 1 → 0 (**-1**)
* **False Negatives (FN)**: 0 → 0 (Unchanged)

### OVERALL Metrics
* **Precision**: `0.9836` → `1.0000` (**+0.0164**)
* **Recall**: `1.0000` → `1.0000` (Unchanged)
* **F1-Score**: `0.9917` → `1.0000` (**+0.0083**)

---

## 9. Connection Between Commits

```text
Commit 19 (Expanded Evaluation)
Added robust synthetic dataset to expose system boundaries.
    ↓
Commit 20 (Address Improvement)
Resolved address extraction failures and unit/zip truncation.
    ↓
Commit 21 (Organization Improvement)
Filtered brands/technical acronyms and aligned period spans.
    ↓
Commit 22 (Phone Improvement) [THIS COMMIT]
Reduced baseline phone confidence to handle conflicting context.
    ↓
Commit 23 (Final Evaluation/Report)
Prepare pipeline validation and packaging.
```

---

## 10. Interview Questions

### "Why was Phone a precision problem?"
"The regex matches sequences of digits that look like standard phone formats. However, transaction IDs, ticket IDs, and reference numbers often share the same formatting. This results in the system over-redacting safe numeric codes, causing a precision problem."

### "How did you remove the false positive?"
"We reduced the detector baseline confidence level to `0.80`. When a candidate matches both positive context (like `"mobile"`) and negative context (like `"Ticket ID"`), the negative penalty offsets the positive bonus, pulling the final score to `0.65` and rejecting it."

### "How did you make sure recall didn't decrease?"
"We verified all 6 true positive PHONE examples in our evaluation dataset. Since their scores remain at `0.80` (no context) or `0.95` (positive context), they are still above the `0.70` resolver threshold."

### "Why shouldn't you simply make the regex more restrictive?"
"Making the regex more restrictive (e.g. banning certain digit patterns) might prevent matching actual phone numbers, hurting recall. Using context-based resolution is a much more robust approach."

### "How did you use context?"
"We utilized positive context rules (`"mobile"`, `"phone"`) and negative context rules (`"ticket id"`, `"order number"`). The resolver uses these to mathematically boost or penalize candidate scores."

---

## 11. Quick Revision

### 5 Key Concepts
1. **Conflicting Context**: When both positive and negative keywords match around a candidate.
2. **Confidence Clamping**: Setting detector confidence to allow context to sway the resolver decision.
3. **Negative Penalty**: A score reduction (`-0.30`) applied when negative keywords match.
4. **Micro F1**: A micro-averaged performance metric representing overall pipeline health.
5. **Regression Verification**: Running tests on positive and negative cases to ensure stability.

### 3 Interview Questions
1. *What is the mathematical effect of conflicting context on a candidate with 0.80 confidence?*
2. *Why is it preferred to adjust confidence instead of modifying the regex pattern for ambiguous numeric structures?*
3. *How does F1-score balance precision and recall?*

### 3 Practical Examples
1. **Conflicting Context**: `"Ticket ID 98765-43210 is not a valid mobile phone number."` (Rejected).
2. **Positive Context**: `"Call me at 9876543210."` (Accepted).
3. **No Context**: `"Phone: 9876543210."` (Accepted).
