# Commit 23: Final Evaluation and Reporting

This guide details the evaluation architecture, metrics calculations, reporting layer, and prospectus validation for **Commit 23** (`feat: add final evaluation report`).

---

## 1. Commit Overview

This commit creates the final reporting and evaluation layer required by the Scaler AI Labs assignment. It provides a formal, reproducible way to measure pipeline performance and verify output docx integrity.
* **Evaluation Strategy**: Measures exact match alignment of predictions against annotated ground-truth templates.
* **Evaluation Dataset**: A manually annotated set of 62 examples testing various formatting edge cases and negative contexts.
* **Metrics**: Micro-averaged precision, recall, accuracy, and F1-score across all 9 required PII types.
* **Final Report**: Saved to [evaluation/final_evaluation_report.md](file:///Users/piyushsengar/Desktop/pii-redaction-tool/evaluation/final_evaluation_report.md).
* **Real-document Smoke Test**: Formally verifies pipeline execution on the actual prospectus file.

---

## 2. Files Involved

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| [src/evaluator.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/evaluator.py) | Calculates micro-averaged precision, recall, accuracy, and F1 metrics. | Predicted list vs Ground Truth | Metrics dictionary |
| [scripts/evaluate.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/scripts/evaluate.py) | Console entry point that prints the evaluation table. | Ground truth JSON | Metric console stdout |
| [scripts/generate_evaluation_report.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/scripts/generate_evaluation_report.py) | Runs evaluation and smoke tests, validates generated outputs, and writes the report markdown. | Ground truth & prospectus | `final_evaluation_report.md` |
| [evaluation/ground_truth.json](file:///Users/piyushsengar/Desktop/pii-redaction-tool/evaluation/ground_truth.json) | The manual benchmark dataset. | N/A | Evaluation examples |
| [evaluation/final_evaluation_report.md](file:///Users/piyushsengar/Desktop/pii-redaction-tool/evaluation/final_evaluation_report.md) | The formal markdown report artifact. | Computed values | Report document |
| [tests/test_evaluation_report.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_evaluation_report.py) | Validates final report structure and asserts that no raw PII leaks into the document. | Markdown report content | Test assertions |

---

## 3. Required Flow Diagram

```text
Ground Truth
     │
     ▼
Predictions
     │
     ▼
Exact Span + Type Matching
     │
     ▼
TP / FP / FN / TN
     │
     ▼
Precision / Recall / Accuracy / F1
     │
     ▼
Final Evaluation Report (final_evaluation_report.md)

---------------------------------------------------

Red Herring Prospectus (Input)
     │
     ▼
Final Pipeline (src.main)
     │
     ▼
final_redacted.docx (Output)
     │
     ▼
DOCX validation (python-docx checks)
     │
     ▼
Smoke-test results (included in final report)
```

---

## 4. Metric Explanation

### Confusion Matrix
* **True Positive (TP)**: The system correctly identified a PII entity.
  * *Example*: Ground truth is `[12, 17) "Smith" (PERSON)`, prediction matches `[12, 17) "Smith" (PERSON)`.
* **False Positive (FP)**: The system flagged a non-PII span as PII.
  * *Example*: Prediction flags `[4, 7) "DNS" (ORGANIZATION)`, but ground truth does not mark `"DNS"` as PII.
* **False Negative (FN)**: The system missed an actual PII entity.
  * *Example*: Ground truth has `[10, 20) "9876543210" (PHONE)`, but prediction has nothing.
* **True Negative (TN)**: The system correctly rejected a candidate that looked like PII but was actually safe context.
  * *Example*: Ground truth has `[10, 21) "98765-43210"` annotated as `non_pii` (Ticket ID context), and the resolver rejected it.

### Calculations
* **Precision**: *"Of all predicted PII, how much was actually PII?"*
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
* **Recall**: *"Of all actual PII in the document, how much did we find?"*
  $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
* **Accuracy**: *"Of all explicitly annotated items, how many decisions were correct?"*
  $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$
* **F1-Score**: The harmonic mean balancing precision and recall.
  $$\text{F1} = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## 5. Why Accuracy Needs a Caveat

If we treated every non-PII character or word in a document as a True Negative (TN), the TN count would be in the millions. This would artificially inflate accuracy to `99.999%` even if the pipeline missed all actual PII.

Therefore:
1. **Accuracy is only calculated over explicitly annotated candidate spans** in the ground-truth benchmark.
2. A **100% benchmark accuracy** does **NOT** mean 100% accuracy on arbitrary documents. It is a benchmark-specific metric and should not be used to claim universal perfection.

---

## 6. Final Results

Computed dynamically from [evaluation/ground_truth.json](file:///Users/piyushsengar/Desktop/pii-redaction-tool/evaluation/ground_truth.json):

* **Total Examples**: 62
* **Overall Matching**: Exact Span and Type matching

| PII Type | TP | FP | FN | TN | Precision | Recall | Accuracy | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| PERSON | 11 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| EMAIL | 7 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PHONE | 6 | 0 | 0 | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| ORGANIZATION | 6 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| ADDRESS | 6 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| SSN | 6 | 0 | 0 | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| CREDIT_CARD | 6 | 0 | 0 | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| DOB | 6 | 0 | 0 | 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| IP_ADDRESS | 6 | 0 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **OVERALL (MICRO)** | **60** | **0** | **0** | **6** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

---

## 7. Improvement Journey

Our system progressed through the following milestones based on evaluation feedback:

```text
91.80% Precision / 93.33% Recall (Initial expanded benchmark)
      ↓
Address Improvement (Commit 20)
Fixed French prefix styles, unit formats, and zip code truncation.
Precision = 93.65%, Recall = 98.33%
      ↓
Organization Improvement (Commit 21)
Filtered out protocol terms/brands, fixed period span alignments.
Precision = 98.36%, Recall = 100.00%
      ↓
Phone Improvement (Commit 22)
Calibrated phone detector confidence to filter conflicting context.
Precision = 100.00%, Recall = 100.00%
```

---

## 8. Real Document Smoke Test

* **Controlled Evaluation**: Run on short, annotated templates with known ground-truth labels. Used to compute precision and recall metrics.
* **Prospectus Smoke Test**: Run on the actual `Red Herring Prospectus.docx` to verify the pipeline doesn't crash on large files.
* **Ground Truth Limitation**: The prospectus is not exhaustively labeled. Therefore, we cannot calculate precision/recall metrics for it, only redaction statistics.

---

## 9. Limitations

* **Synthetic Dataset**: The 62 evaluation examples are artificial.
* **Manually Annotated Dataset**: Ground truth annotations can suffer from human labeling errors.
* **Limited Size**: 62 examples are small compared with arbitrary business documents.
* **Exact Matching**: Enforces strict boundary checks; minor offsets count as errors.
* **NER Variance**: spaCy's small model is sensitive to capitalization and spelling variants.
* **No Exhaustive Prospectus Annotation**: 100% recall on the benchmark doesn't guarantee 100% recall on the prospectus.
* **OCR Limitations**: The pipeline doesn't extract text from scanned images inside DOCX files.
* **Complex DOCX Limitations**: Nested tables, charts, and drawings are not covered.

---

## 10. Interview Questions

### "How did you evaluate your PII redaction tool?"
"We used an exact span and type matching strategy against a manually annotated benchmark dataset, tracking micro-averaged precision, recall, and F1 metrics."

### "How did you calculate precision?"
"Precision was calculated as True Positives divided by total predicted positives ($TP / (TP + FP)$). It measures the percentage of redactions that were actually PII."

### "How did you calculate recall?"
"Recall was calculated as True Positives divided by ground-truth positives ($TP / (TP + FN)$). It measures our ability to find all sensitive data."

### "Why is recall important for PII redaction?"
"Redaction is a safety-critical task. Missing even a single PII entity (producing a False Negative) results in a data leak. High recall is vital."

### "Why can't you claim 100% recall on the real prospectus?"
"Because the prospectus does not have exhaustive ground truth annotations. The benchmark dataset tests specific patterns, but a real-world prospectus contains unseen context."

### "How did you improve your system?"
"We expanded the evaluation dataset, analyzed false positives and false negatives, and made targeted, generalizable fixes to the detectors and resolver."

### "How did you avoid overfitting?"
"We avoided hardcoding values from evaluation strings, adjusted detector confidence values mathematically, and wrote unit tests with negative examples."

---

## 11. Quick Revision

### 5 Key Concepts
1. **Exact Span Matching**: Requires prediction coordinates to align with ground truth.
2. **Micro-averaging**: Aggregating raw TP/FP/FN counts across all classes to calculate global metrics.
3. **Accuracy Caveat**: Calculating accuracy only over explicitly annotated candidate spans.
4. **Smoke Test**: High-volume end-to-end execution to verify performance and file integrity.
5. **Conflicting Context**: Adjusting detector confidence so negative context overrides positive context.

### 3 Interview Questions
1. *Why does micro-averaging prevent class-size bias in multi-class PII metrics?*
2. *What are the risks of using token-level accuracy to evaluate PII models?*
3. *How does post-filtering NER candidates preserve recall while boosting precision?*

### 3 Practical Examples
1. **Exact Match**: Ground truth `[0, 5) "Acme"` matches prediction `[0, 5) "Acme"`.
2. **False Positive**: System redacts `"TCP"` as an ORGANIZATION.
3. **Conflicting Context**: A phone-like string is rejected because it is preceded by `"Ticket ID"`.
