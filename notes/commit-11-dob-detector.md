# Commit 11 Learning Notes: Date of Birth PII Detector

This document details the concepts and design decisions implemented in Commit 11 (`feat: add date of birth pii detector`).

---

## 1. Commit Overview

### What Date of Birth PII Means
Date of Birth (DOB) is classification PII representing the day, month, and year an individual was born. Unlike phone numbers or emails, a date does not contain unique formatting that distinguishes it as DOB. It is highly sensitive because it is commonly used to verify identity.

### Why Dates are More Difficult than Emails
An email has a unique anchor symbol (`@`). Dates are written in common formats (e.g. `01/02/1995`) that are shared by non-sensitive events (such as invoice dates, transaction timestamps, or agreement sign-offs).

### Why a Date Alone Does Not Identify DOB
The sequence `01/02/1995` represents a point in time, not a birth event. Without context, we cannot determine its semantic meaning.

### Why Contextual Evidence is Important
To distinguish a birth date from other dates, we inspect surrounding text for keywords (e.g. `"Date of Birth"`, `"DOB"`, or `"Born"`). Combining pattern matching with context checks allows us to filter out non-PII dates, maintaining high precision.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` schema and the `PIIType.DOB` Enum member. | (None for this commit) | Data schema definitions |
| **`src/detectors/base.py`** | Establishes the parent `BaseDetector` interface class. | (None for this commit) | Abstract parent class |
| **`src/detectors/dob.py`** | Implements candidate regex checks, calendar parsing, and local context checks. | Normalized text segment | List of `PIIEntity` matches |
| **`tests/test_dob_detector.py`** | Tests valid/invalid date formats, keyword variations, and non-DOB date exclusions. | Test text strings | Unit test pass/fail results |

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow and file relationship diagram for Commit 11:

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
Normalized Text ───> │src/detectors/dob.│ <──────── tests/test_dob_detector.py
                     │   DOBDetector    │           (Tests the implementation)
                     └────────┬─────────┘
                              │ DOBDetector.detect()
                              ▼
                       Date Candidate ───────────(Four regex patterns)
                              │
                              ▼
                     Calendar Validation ────────(strptime + plausibility check)
                              │
                              ▼
                      Local Context Check ───────(inspects +/- 30 chars)
                              │
                           ┌──┴──┐
                           │     │
                      No Context Context Found
                           │     │
                        Discard  ▼
                             PIIEntity
                                 │
                                 ▼
                          list[PIIEntity]
```

---

## 4. Step-by-Step Data Flow

### Walkthrough A: `"Date of Birth: 01/02/1995"`
```text
Input text string:
"Date of Birth: 01/02/1995"
       │
       ▼
Regex Matching (DOBDetector.detect)
       │ Matches pattern: \d{1,2}[/\.-]\d{1,2}[/\.-]\d{4}
       ▼
Candidate found
       │ - Text:  "01/02/1995"
       │ - Span:  start = 15, end = 25
       ▼
Calendar Validation
       │ `strptime` parses "01-02-1995" as Feb 1 or Jan 2.
       │ Year 1995 is within reasonable birth bounds (1900 to present).
       │ Validation: PASSED!
       ▼
Local Context Check
       │ Inspects 30 characters before: "Date of Birth: "
       │ Checks for context regex: \b(date of birth|dob|birth date|birthdate|born on|born)\b
       │ Matches "Date of Birth".
       │ Check: PASSED!
       ▼
PIIEntity construction
       │  PIIEntity(
       │      text="01/02/1995",
       │      entity_type=PIIType.DOB,
       │      start=15,
       │      end=25,
       │      confidence=0.90,
       │      source="context"
       │  )
```

### Walkthrough B: `"Issue Date: 01/02/1995"`
```text
Input text string:
"Issue Date: 01/02/1995"
       │
       ▼
Regex Matching (DOBDetector.detect)
       │ Matches candidate: "01/02/1995" (start = 12, end = 22)
       ▼
Calendar Validation
       │ Parses successfully (year 1995 is valid).
       │ Validation: PASSED!
       ▼
Local Context Check
       │ Inspects 30 characters before: "Issue Date: "
       │ Inspects 30 characters after: ""
       │ Searches for DOB keywords. None match.
       │ Check: FAILED!
       ▼
Result: Discarded (Empty list returned)
```

---

## 5. Code Explanation

### 1. BaseDetector
The `DOBDetector` inherits from `BaseDetector` and implements `detect(text)`.

### 2. `DOBDetector`
The detector class responsible for extracting and validating DOB matches.

### 3. Date Regex
We use four compiled regex patterns with alphanumeric boundaries to match standard numeric and textual date structures.

### 4. Date Validation
We try parsing candidates using Python's standard `datetime.datetime.strptime`. Candidates that throw a `ValueError` or violate our birth-year bounds (`1900 <= year <= current_year`) are discarded.

### 5. Context Window
For each candidate, we inspect `text[max(0, start - 30):start]` and `text[end:min(len(text), end + 30)]`. A window of 30 characters is large enough to capture preceding or trailing labels while avoiding overlap with unrelated text.

### 6. Contextual Keywords
We search the context windows using a compiled regex containing our keywords (`date of birth`, `dob`, `birth date`, `birthdate`, `born on`, `born`) bounded by word boundary flags (`\b`) to ensure case-insensitive, whole-word matching.

### 7. PIIEntity
We construct a `PIIEntity` for each match. It stores the match text, the type `PIIType.DOB`, the source `"context"`, and a confidence score.

### 8. PIIType.DOB
The Enum member representing Date of Birth classifications.

### 9. Offsets
Offsets are calculated on the original text to ensure accurate replacement boundaries.

### 10. Source
The source property is set to `"context"`, indicating that matching relied on contextual validation.

### 11. Confidence
We assign a confidence score of `0.90` to verified matches.

---

## 6. Why Context Matters

```text
Date Alone ("01/02/1995") ──> Ambiguous (Could be sign-off, invoice, page, etc.)
Date + "DOB" Prefix ────────> Strong Evidence (Classified as DOB)
Date + "Issue Date" Prefix ──> Negative Evidence (Correctly rejected)
```

Without context, the detector would classify every date as a DOB. By requiring DOB-related keywords to appear in the local context window, we ensure only birth dates are matched, preventing false positives on other dates.

---

## 7. Precision vs. Recall

* **Broad Date Detection**: Matching every date yields $100\%$ recall (we won't miss any DOBs) but very low precision (we will match all dates in the document).
* **Strict DOB Context**: Checking for specific keywords maintains high precision (only matching birth dates) but may miss DOBs that use unlisted keywords or have large label separations (lower recall).
* **Conservative Choice**: In this commit, we prioritize precision. False positives on financial or document dates would corrupt non-sensitive data, so we restrict matching to candidates with clear DOB context.

---

## 8. Testing

We created **[tests/test_dob_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_dob_detector.py)** to verify:
* **Positive DOB Tests**: Valid formats prefixed with different keywords.
* **Invalid Calendar Dates**: Rejecting invalid dates like `31/02/1995`.
* **Negative Context Tests**: Rejecting issue, agreement, and incorporation dates.
* **Offset & Boundary Tests**: Verifying that match indexes are correct.
* **Multiple Occurrences**: Asserts that multiple or duplicate DOBs are returned individually.

---

## 9. Real Document Testing

Running the detector against `input/Red Herring Prospectus.docx` returned **0 matches**. This is the correct behavior:
* Corporate prospectus documents contain many dates (issue dates, filing dates, incorporation dates) but rarely list individuals' birth dates.
* The detector successfully ignored the dates in the prospectus because they lacked DOB context, verifying its high precision.
* We must not weaken the validation rules to force a match, as this would increase false positives in other documents.

---

## 10. Connection Between Commits

Our project pipeline builds incrementally:

* **Commit 8 (IPDetector)**: Implements regex and range validation for IP addresses.
* **Commit 9 (SSNDetector)**: Implements regex and validation for SSNs.
* **Commit 10 (CreditCardDetector)**: Implements regex and Luhn validation for credit card numbers.
* **Commit 11 (DOBDetector)**: Implements candidate generation, date validation, and local context checks for DOBs.
* **Commit 12 (NER Detector)**: Will build on this structure to integrate Named Entity Recognition (NER) for person and organization names.

> [!NOTE]
> DOB is the first detector that requires local context validation. Emails, phone numbers, IPs, and credit cards are structurally unique, whereas dates require contextual evidence to determine their meaning.

---

## 11. Common Beginner Mistakes

* **Detecting Every Date as DOB**: Failing to verify context, which matches all dates.
* **Ignoring Context Word Boundaries**: Matching `"born"` inside words like `"stubborn"` or `"airborne"`.
* **Accepting Invalid Calendar Dates**: Matching non-existent dates like `31/02/1995`.
* **Losing Original Formatting**: Returning normalized dates instead of the original text.
* **Incorrect Offsets**: Calculating offsets on normalized text where spaces have been stripped.
* **Creating a Global Context Framework Too Early**: Building complex context classes instead of keeping keyword checks local to the detector.
* **Confusing Date Detection with DOB Detection**: Assuming date patterns represent DOBs without validation.

---

## 12. Interview Explanation

**Question:** *"Why can't you detect DOB using only regex?"*

**Answer:**
> "Unlike emails or phone numbers, dates do not have unique structural formatting. The string '01/02/1995' can represent an invoice date, a transaction date, or a birth date. Regex can only verify the formatting of the date, so we must inspect surrounding text for contextual keywords to identify it as a DOB."

**Question:** *"How did you reduce false positives for DOB?"*

**Answer:**
> "I implemented a two-step validation check. First, I validated that candidate matches represent valid calendar dates using python's datetime module. Second, I inspected a local context window of 30 characters before and after the date for case-insensitive keywords (e.g. 'DOB', 'Born') using a whole-word boundary regex. This successfully filtered out other dates like issue or incorporation dates."

**Question:** *"Why did you keep the context logic local in this commit?"*

**Answer:**
> "I kept the context logic local to follow the project's incremental design pattern. This allowed us to verify the DOB detector logic in isolation without introducing the complexity of a generalized context engine, which will be built in future commits."

**Question:** *"How would you improve DOB detection in a production system?"*

**Answer:**
> "I would extend the keyword list to support other languages, and implement semantic proximity scoring. Proximity scoring calculates how close a keyword is to a date, which helps resolve ambiguous cases in complex layouts or tables."

---

## 13. Quick Revision

### 5 Key Concepts
1. **`DOBDetector`** inherits from `BaseDetector` and implements `detect(text)`.
2. Dates are validated as **valid calendar dates** using `strptime`.
3. Valid matches require **local context keywords** (e.g., `"DOB"`, `"Born"`).
4. The context window extends **30 characters** before and after the candidate date.
5. `source` is set to **`"context"`** and confidence is set to **`0.90`**.

### 3 Interview Questions
1. *Why do dates require contextual validation to be classified as DOB?*
2. *How do you prevent context checks from matching substrings of unrelated words?*
3. *What are the precision/recall tradeoffs when implementing local context checks?*

### 3 Practical Examples

#### Example 1: Valid DOB Match
* **Input**: `"DOB: 01/02/1995"`
* **Match**: `"01/02/1995"`
* **Offsets**: `5` to `15`

#### Example 2: Invalid Calendar Date Rejection
* **Input**: `"Born on 31/02/1995"`
* **Match**: No match (rejected because February 31st is invalid).

#### Example 3: Unrelated Date Rejection
* **Input**: `"Issue Date: 01/02/1995"`
* **Match**: No match (rejected due to lack of DOB context).
