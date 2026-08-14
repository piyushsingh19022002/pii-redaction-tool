# Commit 9 Learning Notes: SSN PII Detector

This document details the concepts and design decisions implemented in Commit 9 (`feat: add ssn pii detector`).

---

## 1. Commit Overview

### What SSN Means
An SSN (Social Security Number) is a nine-digit number issued to U.S. citizens, permanent residents, and temporary workers by the Social Security Administration (SSA). It is primarily used for tracking individuals for taxation and identification purposes.

### What This Commit Implements
This commit implements the `SSNDetector` inside `src/detectors/ssn.py`. It inherits from the abstract `BaseDetector` interface and detects formatted SSNs matching the `XXX-XX-XXXX` pattern, checks them against structural validation rules, and outputs validated `PIIEntity` objects.

### Why SSNs are PII
Because SSNs are unique, permanent, and linked directly to an individual's financial, medical, and employment records, they are one of the most sensitive forms of Personally Identifiable Information (PII). A compromised SSN can lead to identity theft and financial fraud.

### Why Regex Alone is Insufficient
A simple regex pattern like `\d{3}-\d{2}-\d{4}` only matches the **format** of an SSN. It cannot determine if the numbers conform to the structural rules established by the Social Security Administration. For example, it would match dummy values like `000-12-3456` or `123-45-0000`.

### Why Structural Validation Improves Precision
Applying structural validation rules (e.g. discarding invalid area, group, and serial codes) allows us to filter out dummy values and formatted test strings. This improves **precision** by reducing false positives.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` schema and the `PIIType.SSN` Enum member. | (None for this commit) | Data schema definitions |
| **`src/detectors/base.py`** | Establishes the parent `BaseDetector` interface class. | (None for this commit) | Abstract parent class |
| **`src/detectors/ssn.py`** | Extracts formatted SSN candidates using regex and applies structural validation rules. | Normalized text segment | List of `PIIEntity` matches |
| **`tests/test_ssn_detector.py`** | Tests valid/invalid SSN formats, boundary conditions, and numeric exclusions. | Test text strings | Unit test pass/fail results |

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow and file relationship diagram for Commit 9:

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
Normalized Text ───> │src/detectors/ssn.│ <──────── tests/test_ssn_detector.py
                     │   SSNDetector    │           (Tests the implementation)
                     └────────┬─────────┘
                              │ SSNDetector.detect(text)
                              ▼
                       SSN Candidate Regex ──────(Finds \d{3}-\d{2}-\d{4})
                              │
                              ▼
                         Candidate
                       "123-45-6789"
                              │
                              ▼
                     Validation Helper ──────────(AAA-GG-SSSS structural rules)
                              │
                           ┌──┴──┐
                           │     │
                        Invalid Valid
                           │     │
                        Discard  ▼
                             PIIEntity
                                 │
                                 ▼
                          list[PIIEntity]
                                 │
                                 ▼
                     [Future resolver stage]
```

---

## 4. Implementation Walkthrough

Here is a step-by-step example of how the input `"Employee SSN: 123-45-6789"` flows through the detector:

```text
Input text string:
"Employee SSN: 123-45-6789"
       │
       ▼
Regex Matching (SSNDetector.detect)
       │ Matches pattern: (?<![a-zA-Z0-9])(\d{3})-(\d{2})-(\d{4})(?![a-zA-Z0-9])
       ▼
Candidate found
       │ - Text:  "123-45-6789"
       │ - Segments: AAA="123", GG="45", SSSS="6789"
       ▼
Structural Validation
       │ Checks:
       │  - AAA ("123") is not "000", "666", or in range 900-999.
       │  - GG ("45") is not "00".
       │  - SSSS ("6789") is not "0000".
       │ Validation: PASSED!
       ▼
Offset Extraction
       │ - start = 14 (index of "1")
       │ - end = 25 (index after "9")
       ▼
PIIEntity construction
       │  PIIEntity(
       │      text="123-45-6789",
       │      entity_type=PIIType.SSN,
       │      start=14,
       │      end=25,
       │      confidence=0.95,
       │      source="SSNDetector"
       │  )
       ▼
Output list
[PIIEntity(text="123-45-6789", start=14, end=25, ...)]
```

---

## 5. Code Explanation

### 1. `SSNDetector`
The detector class responsible for extracting and validating SSN matches.

### 2. BaseDetector Inheritance
The `SSNDetector` inherits from `BaseDetector` and implements `detect(text)`. This allows the orchestrator to query it alongside other detectors.

### 3. Regex
We compile the regular expression:
`(?<![a-zA-Z0-9])(\d{3})-(\d{2})-(\d{4})(?![a-zA-Z0-9])`
This matches three groups of digits separated by hyphens. Capturing groups extract AAA, GG, and SSSS. Alphanumeric boundaries prevent matching subparts of longer numeric strings.

### 4. Candidate Generation
The `finditer` loop matches strings that fit the format and captures their boundary indexes.

### 5. Validation Helper
We run structural checks on the captured segments (AAA, GG, SSSS) to ensure they conform to valid ranges.

### 6. `PIIType.SSN`
The Enum member representing Social Security Number classifications.

### 7. `PIIEntity`
We construct a `PIIEntity` for each match. It stores the match text, the type `PIIType.SSN`, the source `"regex"`, and a confidence score.

### 8. Start/End Offsets
Offsets are calculated on the original text to ensure accurate replacement boundaries.

### 9. Confidence
We assign a confidence score of `0.95`. Since the formatted pattern `XXX-XX-XXXX` is highly specific to SSNs, this score is extremely reasonable.

### 10. `source="regex"`
Denotes that the match was identified using regular expressions.

---

## 6. SSN Validation Rules

An SSN is divided into three parts: `AAA-GG-SSSS` (Area-Group-Serial):

```text
AAA (Area Number) ───[3 digits]───> Cannot be 000, 666, or between 900-999
GG (Group Number) ───[2 digits]───> Cannot be 00
SSSS (Serial Code) ──[4 digits]───> Cannot be 0000
```

### Why These are Rejected
* **`000-XX-XXXX`**: The SSA has never assigned an area code of `000`.
* **`666-XX-XXXX`**: Area code `666` is unassigned due to its association with the "number of the beast."
* **`900-999 area ranges`**: The `900` range is reserved for national numbering and state-issued cards, and has never been assigned to individuals.
* **`XXX-00-XXXX`**: The group number starts at `01`. A group number of `00` is invalid.
* **`XXX-XX-0000`**: The serial number starts at `0001`. A serial number of `0000` is invalid.

> [!IMPORTANT]
> Structural validation only verifies that a number matches the format and range constraints of a valid SSN. It does not prove that the number belongs to a real person.

---

## 7. Precision vs. Recall

* **High False-Positive Risk of `\d{9}`**: A pattern matching any 9-digit number would yield high recall but very low precision. In corporate documents, 9-digit numbers are commonly used for financial indicators, registration numbers, or phone numbers.
* **Formatted vs. Unformatted Trade-off**:
  * **Formatted (`XXX-XX-XXXX`)**: Restricting the detector to formatted numbers ensures high precision (reducing false positives), but means we will miss unformatted numbers (lower recall).
  * **Unformatted (`\d{9}`)**: Matching unformatted numbers increases recall, but results in high false-positive rates.
  * For this assignment, we prioritize precision by matching formatted numbers to avoid false positives on financial data.

---

## 8. Testing

We created **[tests/test_ssn_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_ssn_detector.py)** to verify:
* **Positive Tests**: Formatted valid SSNs, embedded SSNs, and multiple matches.
* **Negative Tests**: Invalid area codes (`000`, `666`, `900`-`999`), invalid group codes (`00`), and invalid serial codes (`0000`).
* **Boundary & Offset Tests**: Matches adjacent to punctuation and character boundary offsets.
* **Numeric Exclusions**: Discarding plain 9-digit numbers.

### Why Synthetic SSNs are Appropriate
Using real SSNs for testing is a security risk. Using synthetic SSNs that follow the correct formatting and validation rules allows us to verify the detector safely.

---

## 9. Real Document Testing

Running the detector against `input/Red Herring Prospectus.docx` returned **0 matches**. This is the correct behavior:
* An Indian Red Herring Prospectus does not contain U.S. Social Security Numbers.
* The detector successfully ignored dates, Indian phone codes, financial metrics, and numeric tables, verifying its high precision.
* We must not weaken the validation rules to force a match, as this would increase false positives in other documents.

---

## 10. Connection Between Commits

Our pipeline builds incrementally:

* **Commit 5 (BaseDetector)**: Defines the parent interface class.
* **Commit 6 (EmailDetector)**: Implements regex matching for email formats.
* **Commit 7 (PhoneDetector)**: Implements regex and validation for phone numbers.
* **Commit 8 (IPDetector)**: Implements regex and validation for IP addresses.
* **Commit 9 (SSNDetector)**: Subclasses `BaseDetector` and implements candidate generation and validation for SSNs.
* **Commit 10 (CreditCardDetector)**: Will build on this structure to implement Credit Card Number detection.

---

## 11. Common Beginner Mistakes

* **Assuming Every `XXX-XX-XXXX` is Valid**: Skipping structural validation and matching dummy values.
* **Detecting Every 9-Digit Number**: Matching plain numbers and generating false positives on financial data.
* **Regex-Only Reliance**: Failing to validate segment ranges.
* **Matching Inside Larger Identifiers**: Matching sub-spans of longer digit blocks (e.g. `1123-45-67890`).
* **Incorrect Offsets**: Calculating offsets on normalized text where spaces have been stripped.
* **Modifying Original Text**: Returning normalized numbers instead of the original text, which breaks replacement logic.
* **Confusing Validation with Real Issuance**: Assuming that a structurally valid number represents a real person.

---

## 12. Interview Explanation

**Question:** *"How did you detect SSNs?"*

**Answer:**
> "I used a two-stage detection process. First, I used a regex with alphanumeric boundaries to match candidates in the formatted XXX-XX-XXXX representation. Second, I applied structural validation on the captured segments, rejecting invalid area codes, group codes, and serial codes."

**Question:** *"Why did you use regex plus validation?"*

**Answer:**
> "Regex is designed for pattern matching, not range validation. A regex can confirm that a string matches the format of three hyphen-separated blocks, but checking that each block conforms to SSA range constraints requires logical validation. Splitting the process keeps the code clean and reliable."

**Question:** *"How did you reduce SSN false positives?"*

**Answer:**
> "I applied structural validation rules to discard dummy values (like 000 or 666 area codes). I also used negative lookbehinds and lookaheads in the regex to avoid matching sub-spans of longer digit blocks, and restricted the detector to formatted numbers to ignore plain 9-digit values."

**Question:** *"What would be the tradeoff of detecting unformatted SSNs?"*

**Answer:**
> "Detecting unformatted 9-digit numbers would increase recall (we would catch unformatted SSNs), but would significantly lower precision by matching financial data, serial numbers, and other non-sensitive numeric sequences common in corporate filings."

---

## 13. Quick Revision

### 5 Key Concepts
1. **`SSNDetector`** inherits from `BaseDetector` and implements `detect(text)`.
2. Matches are restricted to formatted **`XXX-XX-XXXX`** patterns.
3. Area codes (AAA) cannot be **`000`**, **`666`**, or in the **`900` to `999`** range.
4. Group numbers (GG) cannot be **`00`**, and serial numbers (SSSS) cannot be **`0000`**.
5. Offsets are calculated on the **original text** to ensure accurate replacement boundaries.

### 3 Interview Questions
1. *What are the validation rules for U.S. Social Security Numbers?*
2. *Why do we ignore unformatted 9-digit numbers in corporate filings?*
3. *How do regex boundaries prevent matching sub-spans of longer numeric strings?*

### 3 Practical Examples

#### Example 1: Valid SSN Match
* **Input**: `"My SSN is 123-45-6789."`
* **Match**: `"123-45-6789"`
* **Offsets**: `10` to `21`

#### Example 2: Invalid Area Code Rejection
* **Input**: `"The dummy code 666-12-3456 is invalid."`
* **Match**: No match (rejected because the area code is `666`).

#### Example 3: Unformatted Number Rejection
* **Input**: `"Registration number is 123456789."`
* **Match**: No match (rejected because it is unformatted).
