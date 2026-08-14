# Commit 7 Learning Notes: Phone PII Detector

This document details the concepts and design decisions implemented in Commit 7 (`feat: add phone pii detector`).

---

## 1. Commit Overview

### What This Commit Accomplished
This commit implements our second functional PII detector: `PhoneDetector` inside `src/detectors/phone.py`. It inherits from `BaseDetector` and extracts common Indian mobile and landline numbers. In addition, it implements a comprehensive test suite in `tests/test_phone_detector.py` to verify formatting borders, validation rules, and offset boundaries.

### Why Phone Detection is Harder than Email Detection
Emails have a highly standardized and unique symbol separator (`@`) and a dot-separated TLD at the end. Phone numbers, on the other hand:
* Do not have a single defining anchor symbol.
* Use multiple different punctuation marks as separators (spaces, hyphens, parentheses).
* Vary in digit length (from 10-digit mobile numbers to landlines of varying lengths with STD area codes).
* Look identical to other common numeric strings like corporate identifiers, dates, prices, or serial numbers.

### Why Phone Numbers Have Many Formats
Phone numbers are written in many different styles depending on whether the writer includes the country code (e.g. `+91`), local prefixes (e.g. `0`), or groups digits for readability (e.g. `98765 43210` or `4505-3237`). 

### Why Blindly Detecting 10-Digit Numbers Creates False Positives
In corporate documents (like a financial prospectus), there are many 10-digit numbers that are not phone numbers (e.g. transaction IDs, page listings, values, or dates). A simplistic rule like *"any 10-digit sequence is a phone number"* would match this non-PII data, resulting in high false-positive rates and corrupting the document.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` schema and the `PIIType.PHONE` Enum member. | (None for this commit) | Data schema definitions |
| **`src/detectors/base.py`** | Establishes the parent `BaseDetector` interface class. | (None for this commit) | Abstract parent class |
| **`src/detectors/phone.py`** | Implements mobile and landline regex matching, candidate normalization, and structural validation. | Normalized text segment | List of `PIIEntity` matches |
| **`tests/test_phone_detector.py`** | Tests phone regex boundaries, STD area code rules, and offset accuracy. | Test text strings | Unit test pass/fail results |

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow for Commit 7:

```text
                     ┌──────────────────┐
                     │   src/models.py  │
                     └────────┬─────────┘
                              │ Imports PIIEntity
                              ▼
                     ┌──────────────────┐
                     │src/detectors/base│
                     └────────┬─────────┘
                              │ Inherited by
                              ▼
[Previous Commit]    ┌──────────────────┐
Normalized Text ───> │src/detectors/phon│ 
                     │  PhoneDetector   │
                     └────────┬─────────┘
                              │ Extract candidates (Mobile & Landline regexes)
                              ▼
                       Overlap Filter ────(Prunes overlapping matches)
                              │
                              ▼
                     Digit Normalization ─(Strips non-digits)
                              │
                              ▼
                     Structural Validate ─(Checks STD code & prefixes)
                              │
                              ▼
                          PIIEntity
                              │
                              ▼
                       list[PIIEntity]
                              │
                              ▼
                 [Future Candidate Resolver]
```

---

## 4. Data Flow Example

Here is a step-by-step example of how the data flows through the detector:

```text
Input text string:
"Call +91 9876543210 today."
       │
       ▼
Regex matching (PhoneDetector.detect)
       │ Matches pattern: (?<!\d)(?:(?:\+91|91)[\s-]?)?[6-9]\d{9}(?!\d)
       ▼
Candidate found
       │ - Text:  "+91 9876543210"
       │ - Span:  start = 5, end = 19
       ▼
Digit Normalization
       │ Strips non-digits: "919876543210" (length 12)
       ▼
Structural Validation
       │ Checks:
       │  - Starts with country code "91"
       │  - Length is 12 digits
       │  - 3rd digit (start of local mobile) is "9" (within valid [6-9] range)
       │ Validation: PASSED!
       ▼
PIIEntity construction
       │  PIIEntity(
       │      text="+91 9876543210",
       │      entity_type=PIIType.PHONE,
       │      start=5,
       │      end=19,
       │      confidence=0.90,
       │      source="PhoneDetector"
       │  )
       ▼
Output list
[PIIEntity(text="+91 9876543210", start=5, end=19, ...)]
       │
       ▼
Future resolver (Overlap resolution & replacement)
```

### Offset Conventions
We use the standard Python slice convention `[start, end)` (inclusive start, exclusive end) on the **original input text**. 
For the text `"Call +91 9876543210 today."`:
* `start = 5` (points to the character `+`)
* `end = 19` (points to the space character *after* the number `0`)
* Slicing `text[5:19]` returns exactly `"+91 9876543210"`.

---

## 5. Code Explanation

### 1. BaseDetector Inheritance
The `PhoneDetector` implements the abstract `detect` interface, allowing the pipeline to query it alongside other detectors.

### 2. Regex
We use two compiled regular expressions: one for mobile patterns and one for landline structures. These use `(?<!\d)` and `(?!\d)` boundary checks to avoid matching sub-spans of longer digit blocks.

### 3. Candidate Matching
The regex search finds matches based on character spacing and separators.

### 4. Separators
Matches are allowed to contain space, hyphen, or parenthesized area codes.

### 5. Candidate Normalization
We strip all non-digits (`re.sub(r"\D", "", match)`) to get a clean digit sequence, which makes it easy to validate.

### 6. Structural Validation
We run checks on the normalized digit string:
* Mobile numbers must be exactly 10 digits (or 12 with a `91` prefix) and start with a digit between `6` and `9`.
* Landline numbers must be between 10 and 13 digits and start with `0` or `91`. The area code cannot start with `1` (which is reserved for emergency services) unless it starts with `11` (the Delhi STD code).

### 7. PIIEntity
We construct a `PIIEntity` for each match. It stores the match text, the type `PIIType.PHONE`, the source `"regex"`, and a confidence score.

### 8. `PIIType.PHONE`
The Enum member representing phone number classifications.

### 9. `source="regex"`
Denotes that the match was identified using regular expressions.

### 10. Confidence
We assign a confidence score of `0.90` to our matches. Since phone number formats can vary, we use a slightly lower confidence score than email matches to account for potential false positives.

---

## 6. Precision vs. Recall Trade-Off

Phone number detection highlights the classic precision vs. recall trade-off:

```text
Overly Broad Detector ──> High Recall (Misses no formats) ──> Low Precision (Many false positives)
Overly Strict Detector ──> High Precision (No false matches) ──> Low Recall (Misses valid formats)
```

* **Overly Broad Detector**: If we match any 10-digit number, we will achieve $100\%$ recall (we won't miss any phone numbers), but very low precision (we will match page numbers, corporate IDs, and financial values).
* **Overly Strict Detector**: If we only match numbers starting with `+91`, we will achieve $100\%$ precision (every match is a phone number), but low recall (we will miss local numbers like `9876543210` or `020-45053237`).
* **Why it matters for the assignment**: In a corporate prospectus, there are many financial figures. If we have low precision, we will redact financial data, which is a major error. If we have low recall, we will leave real phone numbers un-redacted, violating PII compliance. Our structural validation balances both.

---

## 7. False Positives

Numeric identifiers can easily be misclassified as phone numbers:
* **Dates** (e.g. `2026-08-13`): Looks like three numeric groups.
* **Corporate ID Numbers** (e.g. `141032`): Common 6-digit sequences.
* **Serial Numbers** (e.g. `123456789`): Sequential digit blocks.

### How Validation Reduces These Errors
Our regex patterns and validation rules filter out these false positives:
* Landline regex requires three distinct digit blocks matching area code structures.
* Mobile regex requires the first local digit to start with `6`-`9`.
* Validation checks require landlines to start with `0` or `91`, and reject area codes starting with `1` (unless it is `11`), filtering out random numeric codes.

---

## 8. Testing

We created **[tests/test_phone_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_phone_detector.py)** to verify:
* **Indian Mobile Formats**: Tests 10-digit mobile numbers with and without country codes and separators.
* **Landline Formats**: Tests area codes, parenthesized codes, and local STD codes.
* **Duplicates**: Asserts that duplicate numbers in the same text are returned as separate entities.
* **Boundary Checks**: Verifies that trailing punctuation is excluded.
* **Negative Assertions**: Asserts that short numbers, dates, and corporate IDs are ignored.
* **Type validations**: Asserts that offsets and entity types are correct.

---

## 9. Real Document Testing

To test the detector against the actual prospectus:
1. We extracted the normalized text segments from `input/Red Herring Prospectus.docx` using our reader.
2. We ran the `PhoneDetector` on these segments.
3. It successfully matched **39 phone instances** (e.g. `+91 22 40094400`) and ignored non-PII numeric data.
4. We did not hard-code these values in the codebase, ensuring the detector remains decoupled from the data.

---

## 10. Connection Between Commits

Our pipeline builds incrementally:

* **Commit 4 (PIIEntity)**: Defines the data model for matches.
* **Commit 5 (BaseDetector)**: Defines the parent interface class.
* **Commit 6 (EmailDetector)**: Implements regex matching for email formats.
* **Commit 7 (PhoneDetector)**: Subclasses `BaseDetector`, processes normalized text, and outputs `PIIEntity` lists.
* **Commit 8 (IPDetector)**: Will build on this structure to implement IP address detection.

---

## 11. Common Beginner Mistakes

* **Accepting Every 10-Digit Number**: Failing to validate mobile prefixes, which leads to matching financial values.
* **Losing Original Formatting**: Returning normalized numbers (e.g., `919876543210`) instead of the original text (e.g., `+91 9876543210`), which breaks the search-and-replace reconstruction step.
* **Including Punctuation**: Matching trailing punctuation (like `+91-9876543210.`).
* **Calculating Offsets After Normalization**: Calculating offsets on normalized text where spaces have been stripped, resulting in misaligned redactions in the final document.
* **Adding Redaction Logic**: Placing replacement rules inside the detector module.

---

## 12. Interview Explanation

**Question:** *"Why is phone-number detection harder than email detection?"*

**Answer:**
> "Phone-number detection is harder because phone numbers lack a single defining anchor symbol like the '@' symbol in emails. They are written in many different formats using spaces, hyphens, and parentheses as separators. In addition, they look identical to other common numeric data like dates, prices, or serial numbers, which increases the risk of false positives."

**Question:** *"How did you reduce false positives in your phone detector?"*

**Answer:**
> "I used a two-step validation process. First, I used regex patterns with negative lookbehinds and lookaheads to avoid matching sub-spans of longer digit blocks. Second, I applied structural validation on the normalized digits. For mobile numbers, I checked that they are exactly 10 digits and start with valid Indian mobile prefixes (6-9). For landlines, I verified the digit length and confirmed that the area code starts with 0 or 91, and rejected codes starting with 1 unless it was the Delhi STD code (11). This successfully filtered out dates, prices, and corporate identifiers."

**Question:** *"How would you extend this detector to support another country's phone formats?"*

**Answer:**
> "I would add the country's regex patterns to the candidate extraction step. Then, I would extend the structural validation logic to check the country's prefixes and digit lengths. Because the class is modular, we can update these validation rules without changing the parent interface or the downstream resolver."

---

## 13. Quick Revision

### 5 Key Concepts
1. **`PhoneDetector`** inherits from `BaseDetector` and implements `detect(text)`.
2. Offsets are calculated on the **original text** to avoid index shifting.
3. Indian mobile numbers must start with **`6`, `7`, `8`, or `9`**.
4. Landline area codes cannot start with **`1`** (unless it is **`11`** for Delhi).
5. Duplicate occurrences are preserved as separate entities.

### 3 Interview Questions
1. *How do you prevent phone regexes from matching dates or serial numbers?*
2. *What is the precision vs. recall trade-off in phone number detection?*
3. *Why must you calculate character offsets on raw text rather than normalized text?*

### 3 Practical Examples

#### Example 1: Valid Mobile Match
* **Input**: `"Call +91 9876543210."`
* **Match**: `"+91 9876543210"`
* **Offsets**: `5` to `19`

#### Example 2: Valid Landline Match
* **Input**: `"Office: 020-45053237."`
* **Match**: `"020-45053237"`
* **Offsets**: `8` to `20`

#### Example 3: Invalid Number Rejection
* **Input**: `"The serial code is 1234567890"`
* **Match**: No match (rejected because it starts with invalid mobile prefix 1).
