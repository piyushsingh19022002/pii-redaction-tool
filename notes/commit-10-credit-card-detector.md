# Commit 10 Learning Notes: Credit Card PII Detector

This document details the concepts and design decisions implemented in Commit 10 (`feat: add credit card pii detector`).

---

## 1. Commit Overview

### What This Commit Implements
This commit implements the `CreditCardDetector` inside `src/detectors/credit_card.py`. It inherits from the abstract `BaseDetector` contract and detects credit card numbers in the 13-19 digit range. It uses regular expressions to generate candidate strings, normalizes them by stripping spaces/hyphens, and validates them using a custom Python implementation of the Luhn checksum algorithm.

### Why Credit Card Numbers are PII
Credit card numbers are highly sensitive financial identifiers. If exposed, they can be used to make unauthorized purchases, leading to financial loss and identity theft. For this reason, they are classified as high-priority PII.

### Why Regex Alone Isn't Enough
A simple regex pattern like `\d{13,19}` only matches the **format** of a card number. It cannot verify if the numbers conform to the mathematical rules used by card issuers, and would match dummy values or serial numbers.

### Why We Combine Candidate Generation with Validation
* **Candidate Generation (Regex)**: Scans the text quickly to identify potential credit card patterns, filtering out unrelated text.
* **Validation (Luhn Check)**: Performs a mathematical validation on the candidates, filtering out invalid sequences.
* Splitting the process makes the code clean, fast, and easy to maintain.

### What the Luhn Algorithm Is
The Luhn algorithm (also known as the "modulus 10" algorithm) is a simple checksum formula used to validate identification numbers, such as credit card numbers. It was designed to protect against accidental typing errors.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` schema and the `PIIType.CREDIT_CARD` Enum member. | (None for this commit) | Data schema definitions |
| **`src/detectors/base.py`** | Establishes the parent `BaseDetector` interface class. | (None for this commit) | Abstract parent class |
| **`src/detectors/credit_card.py`** | Extracts card candidates using regex, normalizes them, and validates them using the Luhn checksum. | Normalized text segment | List of `PIIEntity` matches |
| **`tests/test_credit_card_detector.py`** | Tests valid/invalid card formats, separators, length boundaries, and checksums. | Test text strings | Unit test pass/fail results |

---

## 3. Required Commit-Specific Implementation Flow

Here is the data flow and file relationship diagram for Commit 10:

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
Normalized Text ───> │src/detectors/cred│ <──────── tests/test_credit_card_detector.py
                     │CreditCardDetector│           (Tests the implementation)
                     └────────┬─────────┘
                              │ CreditCardDetector.detect()
                              ▼
                       Regex Candidate ──────────(Finds card-like digits/separators)
                              │
                              ▼
                       Remove Separators ────────(Strips spaces & hyphens)
                              │
                              ▼
                       Length Validation ────────(Checks 13-19 digit range)
                              │
                              ▼
                        Luhn Validation ─────────(Mathematical checksum check)
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
                          [Future Resolver]
```

---

## 4. Step-by-Step Example

Here is a step-by-step example of how the input `"Card: 4111-1111-1111-1111"` flows through the detector:

```text
Input text string:
"Card: 4111-1111-1111-1111"
       │
       ▼
Regex Matching (CreditCardDetector.detect)
       │ Matches pattern: (?<![a-zA-Z0-9])(?:[0-9][\s-]?){12,18}[0-9](?![a-zA-Z0-9])
       ▼
Candidate found
       │ - Text:  "4111-1111-1111-1111"
       │ - Span:  start = 6, end = 25
       ▼
Original Candidate Preserved
       │ Raw string is stored: "4111-1111-1111-1111"
       ▼
Separator Removal for Validation
       │ Strips spaces and hyphens: "4111111111111111"
       ▼
Length Check
       │ Length is 16 digits (fits valid 13-19 range)
       ▼
Luhn Check
       │ Checks checksum algorithm (mod 10)
       │ Validation: PASSED!
       ▼
PIIEntity construction
       │  PIIEntity(
       │      text="4111-1111-1111-1111",
       │      entity_type=PIIType.CREDIT_CARD,
       │      start=6,
       │      end=25,
       │      confidence=0.99,
       │      source="CreditCardDetector"
       │  )
       ▼
Output list
[PIIEntity(text="4111-1111-1111-1111", start=6, end=25, ...)]
```

---

## 5. Luhn Algorithm

Here is how the Luhn algorithm validates a digit string:

1. **Right-to-Left Processing**: Start from the rightmost digit (the check digit) and move left.
2. **Double Alternating Digits**: Double the value of every second digit.
3. **Subtract 9 When Necessary**: If doubling a digit results in a number greater than `9` (e.g., `8 * 2 = 16`), subtract `9` from the result (equivalent to summing its digits, e.g., `1 + 6 = 7`).
4. **Total Modulo 10**: Sum all digits. If the total is divisible by `10` (sum modulo 10 equals 0), the number is valid.

### Illustrative Example
Validate the 4-digit sequence `4992` (representing a simplified checksum structure):
1. **Reverse**: `2`, `9`, `9`, `4`
2. **Double alternating digits** (index 1, 3):
   * Index 0 (`2`): Not doubled $\rightarrow$ `2`
   * Index 1 (`9`): Doubled $\rightarrow 18$. Since $18 > 9$, subtract 9 $\rightarrow$ `9`
   * Index 2 (`9`): Not doubled $\rightarrow$ `9`
   * Index 3 (`4`): Doubled $\rightarrow 8$. Since $8 \le 9$, keep $\rightarrow$ `8`
3. **Sum**: `2 + 9 + 9 + 8 = 28`
4. **Modulo 10 check**: `28 % 10 = 8` (not 0).
5. **Result**: Invalid!

> [!IMPORTANT]
> The Luhn algorithm only verifies that a number is mathematically structured like a valid credit card. It does not prove that a real card exists or has been issued.

---

## 6. Code Explanation

### 1. `CreditCardDetector`
The detector class responsible for extracting and validating credit card matches.

### 2. BaseDetector
The `CreditCardDetector` inherits from `BaseDetector` and implements `detect(text)`.

### 3. Regex
We compile the regular expression:
`(?<![a-zA-Z0-9])(?:[0-9][\s-]?){12,18}[0-9](?![a-zA-Z0-9])`
This matches sequences of 13 to 19 digits separated by optional single spaces or hyphens. Lookbehind and lookahead checks prevent matching sub-spans of longer digit blocks.

### 4. Candidate Normalization
Separators are removed (`re.sub(r"[\s-]", "", raw_match)`) to get a clean digit string for validation, while preserving the original string in the match.

### 5. Length Validation
Verifies that the normalized digit string contains between 13 and 19 digits.

### 6. Luhn Helper
A custom implementation of the Luhn checksum algorithm.

### 7. PIIEntity
We construct a `PIIEntity` for each match. It stores the match text, the type `PIIType.CREDIT_CARD`, the source `"CreditCardDetector"`, and a confidence score.

### 8. Offsets
Offsets are calculated on the original text to ensure accurate replacement boundaries.

### 9. `source="regex"`
Denotes that the match was identified using regular expressions.

---

## 7. Precision vs. Recall

* **Regex-Only Pipeline**: Matches any 13-19 digit block, resulting in high recall but low precision (matching random serial numbers or barcodes).
* **Regex + Length + Luhn**: Applying length and Luhn checksum validation filters out invalid digit blocks, significantly improving precision.
* **Luhn-Valid Non-Card Identifiers**: Certain numeric identifiers (such as local business codes, barcodes, or custom serials) may pass both the length check and the Luhn checksum by coincidence (1-in-10 probability). To filter these out, we would need to implement card brand prefix validation or context rules in future commits.

---

## 8. Testing

We created **[tests/test_credit_card_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_credit_card_detector.py)** to verify:
* **Valid Synthetic Card Fixtures**: Standard Visa test cards.
* **Separators**: Card formats containing spaces or hyphens.
* **Invalid Checksums**: Discarding invalid Luhn numbers.
* **Length Boundaries**: Discarding numbers outside the 13-19 digit range.
* **Boundary & Offset Tests**: Matches adjacent to punctuation and character boundary offsets.
* **Duplicates**: Asserts that duplicate card numbers in the same text block are returned individually.

### Why Synthetic Test Numbers are Used
Using real credit card numbers in test files is a security risk. Using standard synthetic card numbers intended for testing allows us to verify the detector safely.

---

## 9. Real Document Testing

Running the detector against `input/Red Herring Prospectus.docx` returned **0 matches**. This is the correct behavior:
* A corporate prospectus does not contain credit card numbers.
* The detector successfully ignored large financial figures, dates, and account identifiers by verifying length and Luhn checksums.
* We must not weaken the validation rules to force a match, as this would increase false positives in other documents.

---

## 10. Connection Between Commits

Our project pipeline builds incrementally:

* **Commit 6 (EmailDetector)**: Implements regex matching for email formats.
* **Commit 7 (PhoneDetector)**: Implements regex and validation for phone numbers.
* **Commit 8 (IPDetector)**: Implements regex and validation for IP addresses.
* **Commit 9 (SSNDetector)**: Implements regex and validation for SSNs.
* **Commit 10 (CreditCardDetector)**: Subclasses `BaseDetector` and implements candidate generation and validation for Credit Card numbers.
* **Commit 11 (DOBDetector)**: Will build on this structure to implement Date of Birth detection.

---

## 11. Common Beginner Mistakes

* **Treating Any 16 Digits as a Card**: Failing to validate the Luhn checksum, leading to matching serial numbers.
* **Forgetting Spaces/Hyphens**: Failing to allow spaces or hyphens, which misses formatted numbers (low recall).
* **Modifying the Original Matched Text**: Returning normalized numbers instead of the original text, which breaks replacement logic.
* **Forgetting Luhn**: Relying only on regex and length validation.
* **Confusing Luhn Validity with Real-World Validity**: Assuming that a structurally valid number represents a real card.
* **Losing Offsets after Removing Separators**: Calculating offsets on normalized text where spaces have been stripped, resulting in misaligned redactions in the final document.
* **Adding Redaction Logic**: Placing replacement rules inside the detector module.

---

## 12. Interview Explanation

**Question:** *"How do you detect credit-card numbers?"*

**Answer:**
> "I implemented a two-stage detection pipeline. First, I used a regex with alphanumeric boundaries to match candidates in the 13-19 digit range, allowing spaces and hyphens as separators. Second, I normalized the candidates by stripping separators and validated them using a custom Python implementation of the Luhn checksum algorithm."

**Question:** *"Why did you use the Luhn algorithm?"*

**Answer:**
> "I used the Luhn algorithm because it is the mathematical checksum formula used by card issuers to validate credit cards. Applying it filters out invalid digit blocks and random sequences, which improves precision."

**Question:** *"Does passing Luhn mean the credit card is real?"*

**Answer:**
> "No. The Luhn algorithm only verifies that a number is mathematically structured like a valid credit card. It does not prove that a real card exists or has been issued."

**Question:** *"How did you preserve the original formatting?"*

**Answer:**
> "I separated candidate generation from validation. The regex matches the formatted candidate and captures its boundary indexes on the original text. The separators are removed only for validation, while the original matched text is preserved in the returned PIIEntity."

---

## 13. Quick Revision

### 5 Key Concepts
1. **`CreditCardDetector`** inherits from `BaseDetector` and implements `detect(text)`.
2. Candidates range between **13 and 19 digits**.
3. Separators (spaces/hyphens) are allowed in patterns but **stripped for validation**.
4. Validation uses a custom **Luhn checksum algorithm** to verify digits.
5. Character offsets are calculated on the **original text** to ensure accurate replacement bounds.

### 3 Interview Questions
1. *What is the Luhn checksum algorithm and how does it validate identification numbers?*
2. *Why do we separate candidate generation from validation?*
3. *How do you prevent credit card detectors from matching sub-spans of longer digit blocks?*

### 3 Practical Examples

#### Example 1: Valid Formatted Match
* **Input**: `"Charge card 4111-1111-1111-1111."`
* **Match**: `"4111-1111-1111-1111"`
* **Offsets**: `12` to `31`

#### Example 2: Invalid Checksum Rejection
* **Input**: `"The fake card is 4111111111111112"`
* **Match**: No match (rejected because the checksum is invalid).

#### Example 3: Invalid Length Rejection
* **Input**: `"Code: 123456789012"`
* **Match**: No match (rejected because it is too short).
