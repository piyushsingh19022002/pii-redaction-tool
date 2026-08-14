# Commit 14 Learning Notes: Candidate Resolver and Overlap Handling

This document details the design patterns, scoring logic, and verification of Commit 14 (`feat: add candidate resolver and overlap handling`).

---

## 1. Commit Overview

### What a Candidate Is
A candidate is a text segment flagged by a detector as potential PII. It has a baseline confidence score, start/end index offsets, and a source label.

### Why Detector Output is Not Automatically Final PII
Detectors operate in isolation. A regex matches number strings like `123456789`, which could represent an SSN candidate but might also represent a non-sensitive invoice reference. Classifying every match as final PII causes false positives and data corruption.

### Why a Resolver is Required
The resolver acts as a unified coordinator. It evaluates detector candidates, incorporates contextual signals, resolves overlaps, and applies acceptance criteria to determine the final list of redactable entities.

### What Confidence Scoring Means
Confidence scoring represents the probability that a candidate is the intended PII type. The score starts at the baseline detector confidence and is adjusted based on positive or negative context.

### What Overlap Resolution Means
When different detectors find matches in the same or overlapping text blocks (e.g. NER matches `"John Doe"` while a regex matches `"John"`), we must select the single best candidate and discard the overlapping ones.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Defines `PIIEntity`, `ContextEvidence`, and the immutable `ResolutionResult`. | (None for this commit) | Data schema definitions |
| **`src/context/rules.py`** | Evaluates local text context for keywords. | text, candidate bounds, and category | `ContextEvidence` record |
| **`src/resolver.py`** | Implements the scoring, thresholding, and overlap logic. | Candidates and text | Sorted list of resolved accepted entities |
| **`tests/test_resolver.py`** | Asserts correct resolver output, scores, tie-breakers, and deduplication. | Candidate lists and dummy text | Test pass/fail results |

### Consumer Files
* **[src/docx_redactor.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/docx_redactor.py)** (Future Commit): Will consume the output of the resolver pipeline to perform replacements.

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow for candidate resolution:

```text
Detector candidates
       │
       ▼
   PIIEntity  ───┐
                 ├─> src/resolver.py (resolve_candidate())
ContextEvidence ─┘
       │
       ▼
Score Calculation ───────(Adjusted: base + positive - negative)
       │
   ┌───┴────┐
   ▼        ▼
 ACCEPT   REJECT ────────(Evaluated against threshold = 0.70)
   │
   ▼
Overlap Resolution ──────(resolve_overlaps())
   │
   ▼
Accepted Candidates
```

Also showing the module dependencies:

```text
src/models.py (PIIEntity & ContextEvidence)
      │
      ▼
src/resolver.py
      │
      ▼ (Tests candidate resolution & overlap tie-breakers)
tests/test_resolver.py
```

---

## 4. Scoring

The resolution score is calculated deterministically as:

$$\text{score} = \text{detector\_confidence} + \text{context\_bonus} \cdot \mathbb{I}(\text{has\_positive}) - \text{context\_penalty} \cdot \mathbb{I}(\text{has\_negative})$$

* **Detector Confidence**: Baseline probability assigned by the detector (e.g. `0.90` for IPAddress, `0.85` for NER).
* **Positive Evidence**: Adds `+0.15` to the score if supporting keywords are found.
* **Negative Evidence**: Subtracts `-0.30` from the score if contradicting keywords are found.
* **Clamping**: To keep scores in a standard range, the value is clamped using `0.0 <= score <= 1.0` and rounded to 4 decimal places:
  ```python
  score = round(max(0.0, min(1.0, score)), 4)
  ```

---

## 5. Acceptance

The resolver compares the final score against a configurable threshold. We use an acceptance threshold of **`0.70`**:

* **High Score**: An email candidate with baseline confidence `0.95` and no context:
  $$\text{score} = 0.95 \quad (\ge 0.70) \quad \rightarrow \quad \text{\textbf{ACCEPTED}}$$
* **Medium Score**: A DOB candidate with baseline confidence `0.60` and positive context:
  $$\text{score} = 0.60 + 0.15 = 0.75 \quad (\ge 0.70) \quad \rightarrow \quad \text{\textbf{ACCEPTED}}$$
* **Low Score**: A phone candidate with baseline confidence `0.80` and negative context:
  $$\text{score} = 0.80 - 0.30 = 0.50 \quad (< 0.70) \quad \rightarrow \quad \text{\textbf{REJECTED}}$$

---

## 6. Conflicting Evidence

When both positive and negative context are present (`has_positive = True` and `has_negative = True`), the resolver applies both adjustments:

$$\text{score} = \text{detector\_confidence} + 0.15 - 0.30 = \text{detector\_confidence} - 0.15$$

Because a penalty is larger than the bonus, conflicting evidence reduces the final score, helping prevent false positives. The resolver records a descriptive explanation in the result object:
> `"Conflicting context: positive keyword 'dob' found, but negative keyword decreased final score."`

---

## 7. Overlap Resolution

We define offsets using **half-open intervals `[start, end)`**.

### Overlap Condition
Two spans, `A` and `B`, overlap if:

$$A.\text{start} < B.\text{end} \quad \text{AND} \quad B.\text{start} < A.\text{end}$$

### Priority & Tie-Breaking
Overlap resolution uses a deterministic priority queue to filter out overlapping spans:
1. **Stronger Score**: Spans with higher resolution scores are processed first.
2. **Longer Span**: If scores are equal, the longer span wins (`end - start`).
3. **Deterministic Tie-Break**: If still equal, tie-breakers evaluate the entity type name alphabetically, and then the earlier start offset.

### Concrete Example
```text
Text: "Yesterday John Doe visited Google."

Candidates:
1. Candidate A: "John Doe" (PERSON, start=10, end=18, score=0.90)
2. Candidate B: "doe" (ORG, start=15, end=18, score=0.85)

Overlap Check:
- A.start (10) < B.end (18)  --> True
- B.start (15) < A.end (18)  --> True
- Spans overlap!

Resolution:
- Candidate A has a higher score (0.90 vs. 0.85).
- Candidate A is accepted; Candidate B is discarded.
```

---

## 8. Duplicates

Exact duplicate candidates (sharing the same start offset, end offset, and entity type) are treated as overlapping spans. One candidate is processed first due to stable sorting, and the other is identified as overlapping and automatically discarded, preventing duplicate redactions.

---

## 9. Precision vs. Recall

* **High Threshold**: Increases precision (fewer false positives) but lowers recall (misses valid PII).
* **Low Threshold**: Increases recall (catches all PII) but lowers precision (matches non-sensitive data).
* **Resolver Tuning**: Deferring the final decision to the resolver allows us to tune these weights using evaluation datasets.

---

## 10. Testing

We created **[tests/test_resolver.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_resolver.py)** to verify:
* **Scoring Rules**: Verifying that positive context increases scores and negative context decreases scores.
* **Clamping Bounds**: Confirms that scores are clamped to `[0.0, 1.0]`.
* **Tie-Breaker Priorities**: Verifying that overlaps prioritize higher scores, longer spans, and deterministic order.
* **Exact Duplicates**: Confirms that duplicate candidates are deduplicated.
* **Invariants**: Verifying that candidate text and boundaries are preserved during resolution.

---

## 11. Connection Between Commits

Our project pipeline builds incrementally:

* **Commits 6–12 (Detectors)**: Build individual detectors to locate candidates.
* **Commit 13 (Context Evidence)**: Adds semantic evaluation of the surrounding text.
* **Commit 14 (Candidate Resolver)**: Combines candidate and context evidence to resolve overlapping spans.
* **Commit 15 (Redaction/Pseudonymization)**: Will perform text replacement and map redactable entities.
* **Commit 16 (DOCX Reconstruction)**: Will compile replacements back into the original document structures.

---

## 12. Common Beginner Mistakes

* **Redacting Directly inside Detectors**: Replacing text within detectors, which prevents overlap handling.
* **Mixing Detection and Replacement**: Coupling detection and redaction logic in a single module, making the code hard to test.
* **Ignoring Overlaps**: Failing to handle overlapping spans, which leads to nested or corrupted redaction blocks.
* **Accepting Every NER Result**: Failing to verify NER candidates, which matches non-sensitive capitalized nouns.
* **Using Arbitrary Source Priority**: Rejecting regex matches in favor of NER without comparing their confidence scores.
* **Creating an Opaque Score**: Using complex non-linear score formulas that are difficult to debug.
* **Modifying Candidate Offsets**: Modifying start/end offsets during resolution, which breaks downstream replacement logic.

---

## 13. Interview Explanation

**Question:** *"Why did you separate detection from resolution?"*

**Answer:**
> "Separating detection from resolution decouples the modules. Detectors can focus on locating potential PII based on syntax or structure. Deferring the final decision to a resolver allows us to weigh context evidence, resolve overlapping spans, and tune acceptance thresholds using evaluation datasets."

**Question:** *"How do you handle conflicting evidence?"*

**Answer:**
> "When both positive and negative context are present, we apply both adjustments. Since the negative penalty (-0.30) is larger than the positive bonus (+0.15), conflicting evidence reduces the final score. This helps prevent false positives in ambiguous contexts."

**Question:** *"How do you handle overlapping PII?"*

**Answer:**
> "We check for overlaps using half-open intervals [start, end). Overlapping spans are resolved deterministically by prioritizing the higher score. If scores are equal, we prioritize the longer span, and then use the entity type name and start index as stable tie-breakers."

**Question:** *"How did you choose the confidence threshold?"*

**Answer:**
> "We use an acceptance threshold of 0.70 as a baseline. This allows high-confidence regex candidates (like email or IP address matches) to be accepted immediately, while low-confidence candidates require supporting context to pass."

**Question:** *"How would you tune the resolver?"*

**Answer:**
> "I would run the pipeline against an evaluation dataset containing annotated PII. By comparing the resolver's output against the ground truth, I could tune the threshold, bonus, and penalty weights to optimize precision and recall."

---

## 14. Quick Revision

### 5 Key Concepts
1. The **resolver** calculates resolution scores and verifies them against the threshold.
2. The score starts at baseline detector confidence and is adjusted by **context rules**.
3. All scores are clamped to **`[0.0, 1.0]`** and rounded to 4 decimal places.
4. Overlapping spans are resolved using **half-open boundaries `[start, end)`**.
5. Ties are resolved using **score, span length, entity name, and start index**.

### 3 Interview Questions
1. *Why should context rules compile evidence rather than make final redaction decisions?*
2. *How does the resolver determine if two candidates overlap?*
3. *What tie-breakers are used when two overlapping candidates have the same score?*

### 3 Practical Examples

#### Example 1: Accepted Email
* **Candidate**: `"john@example.com"` (confidence `0.95`)
* **Context**: None
* **Score**: `0.95` (Accepted)

#### Example 2: Rejected Date
* **Candidate**: `"01/02/1995"` (confidence `0.85`)
* **Context**: `"Issue Date"` (negative context penalty `-0.30`)
* **Score**: `0.55` (Rejected)

#### Example 3: Overlap Resolution
* **Candidate A**: `"John Doe"` (PERSON, score `0.90`)
* **Candidate B**: `"doe"` (ORG, score `0.85`)
* **Output**: `"John Doe"` is accepted; `"doe"` is discarded.
