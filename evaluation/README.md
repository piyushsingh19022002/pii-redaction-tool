# PII Redaction Tool - Evaluation Framework

This directory contains the ground truth dataset and evaluation scripts used to measure the PII detection pipeline's performance.

---

## 1. Ground Truth Schema

The manual annotations are stored in [evaluation/ground_truth.json](file:///Users/piyushsengar/Desktop/pii-redaction-tool/evaluation/ground_truth.json).

```json
{
  "examples": [
    {
      "id": "ex1",
      "text": "The raw input string containing PII.",
      "entities": [
        {
          "text": "Annotated PII value",
          "type": "PERSON",
          "start": 0,
          "end": 10
        }
      ],
      "non_pii": [
        {
          "text": "Ambiguous value that looks like PII but is not",
          "type": "SSN",
          "start": 20,
          "end": 31
        }
      ]
    }
  ]
}
```

### JSON Fields
* **`id`**: A unique string identifier for the example.
* **`text`**: The input segment string.
* **`entities`**: A list of positive PII annotations.
* **`non_pii`**: A list of explicitly annotated negative spans (e.g. order numbers resembling credit cards, transaction IDs resembling dates, etc.).

---

## 2. Evaluation Metrics Definition

* **True Positive (TP)**: A prediction matches a ground truth entity exactly in both type and character span:
  $$\text{predicted\_type} == \text{gt\_type} \quad \text{AND} \quad \text{predicted\_span} == \text{gt\_span}$$
* **False Positive (FP)**: A predicted PII entity that does not exist in the positive ground truth.
* **False Negative (FN)**: An annotated positive PII entity that the pipeline failed to predict.
* **True Negative (TN)**: A negative candidate in `non_pii` that was **not** predicted as PII.

> [!IMPORTANT]
> **True Negative Scope**: TN is computed only over the explicitly annotated `non_pii` candidates. We do not count every non-PII word or character block in the document as a TN. This prevents inflating accuracy metrics.

---

## 3. Formulas

* **Precision**: Measures the ratio of correctly predicted PII to all predicted PII:
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
* **Recall**: Measures the ratio of correctly predicted PII to all actual PII:
  $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
* **Accuracy**:
  $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$
* **F1-Score**: The harmonic mean of precision and recall:
  $$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## 4. Limitations of the Evaluation

1. **Manual Annotations**: Ground truth values are manually created, which is subject to human error or interpretation differences.
2. **Synthetic Data**: Synthetic examples help run tests predictably, but may not fully represent all formatting complexities of actual PDF/DOCX documents.
3. **Exact Matching**: We require exact character span matching. If a prediction overlaps but is off by one index (e.g. including a trailing comma), it counts as a False Positive and a False Negative.
4. **NER Variability**: spaCy Named Entity Recognition performance varies based on capitalization and sentence structure, which can cause deviations.
5. **No Universal Recall Proof**: A high recall score on the evaluation set does not guarantee that 100% of all real-world prospectus PII was successfully redacted, as new formats and names may escape coverage.
