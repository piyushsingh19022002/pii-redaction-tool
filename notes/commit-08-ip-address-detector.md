# Commit 8 Learning Notes: IP Address PII Detector

This document details the concepts and design decisions implemented in Commit 8 (`feat: add ip address pii detector`).

---

## 1. Commit Overview

### What This Commit Accomplished
This commit implements the `IPDetector` inside `src/detectors/ip_address.py`. It inherits from the abstract `BaseDetector` contract and supports extracting both IPv4 and IPv6 addresses. It uses regular expressions to generate candidate strings and then validates them using the Python standard library's `ipaddress` module. It also includes unit tests in `tests/test_ip_address_detector.py` to verify the accuracy of the matching bounds.

### What an IP Address Is
An IP (Internet Protocol) address is a unique numerical label assigned to each device connected to a computer network. In PII redaction, IP addresses are treated as sensitive identifiers because they can be used to track or identify individuals.

### Difference Between IPv4 and IPv6
* **IPv4 (Version 4)**: The traditional format composed of four decimal numbers (each ranging from `0` to `255`) separated by periods.
  * *Example:* `192.168.1.1`
* **IPv6 (Version 6)**: The newer format designed to accommodate more devices. It consists of eight blocks of hexadecimal numbers (ranging from `0` to `ffff`) separated by colons. It also supports compressed representations (replacing blocks of zeros with a double colon `::`).
  * *Example:* `2001:0db8:85a3:0000:0000:8a2e:0370:7334` or its compressed form `2001:db8::8a2e:370:7334`.

### Why IP Detection Requires Validation
IP addresses look similar to other common dotted numeric strings:
* **Dates** (e.g. `2026.08.13`)
* **Software Version Numbers** (e.g. `4.0.0` or `1.2.3.4`)
* **Financial Metrics** (e.g. `100.000.000` in certain regional layouts)

To prevent redacting this non-sensitive data, we must run logical validations to ensure matches represent valid IP addresses.

### Why Regex Alone is Insufficient
Writing a regular expression to validate mathematical octet ranges (e.g. asserting that `256.0.0.1` is invalid because `256` exceeds `255`) is extremely complex and error-prone. A regex is designed for **syntactic pattern matching**, not **logical range validation**. Using regex alone leads to matching invalid IP addresses (such as `999.999.999.999`).

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` schema and the `PIIType.IP_ADDRESS` Enum member. | (None for this commit) | Data schema definitions |
| **`src/detectors/base.py`** | Establishes the parent `BaseDetector` interface class. | (None for this commit) | Abstract parent class |
| **`src/detectors/ip_address.py`** | Generates IP candidates using regex and validates them using the `ipaddress` library. | Normalized text segment | List of `PIIEntity` matches |
| **`tests/test_ip_address_detector.py`** | Tests IPv4/IPv6 boundary conditions, compression, and invalid cases. | Test text strings | Unit test pass/fail results |

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow for Commit 8:

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
Normalized Text ───> │src/detectors/ip_a│ 
                     │    IPDetector    │
                     └────────┬─────────┘
                              │ Matches text using
                              ▼
                        Candidate Regex
                              │
                              │ Extracts
                              ▼
                         Candidate IP
                              │
                              │ Validated by
                              ▼
                    ipaddress.ip_address()
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
                     [Future Candidate Resolver]
```

---

## 4. Data Flow Example

### Example A: IPv4 Address
```text
Input text string:
"Server: 192.168.1.1"
       │
       ▼
Regex matching (IPDetector.detect)
       │ Matches pattern: (?<![a-zA-Z0-9])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![a-zA-Z0-9])
       ▼
Candidate found
       │ - Text:  "192.168.1.1"
       │ - Span:  start = 8, end = 19
       ▼
Logical Validation
       │ `ipaddress.ip_address("192.168.1.1")`
       │ Validation: PASSED! (Matches valid IPv4 bounds)
       ▼
PIIEntity construction
       │  PIIEntity(
       │      text="192.168.1.1",
       │      entity_type=PIIType.IP_ADDRESS,
       │      start=8,
       │      end=19,
       │      confidence=0.98,
       │      source="IPDetector"
       │  )
```

### Example B: Compressed IPv6 Address
```text
Input text string:
"IPv6: 2001:db8::1"
       │
       ▼
Regex matching (IPDetector.detect)
       │ Matches pattern: (?<![a-zA-Z0-9:])(?:[0-9a-fA-F]{1,4}:|:){1,7}(?:[0-9a-fA-F]{1,4}|:)(?![a-zA-Z0-9:])
       ▼
Candidate found
       │ - Text:  "2001:db8::1"
       │ - Span:  start = 6, end = 17
       ▼
Logical Validation
       │ `ipaddress.ip_address("2001:db8::1")`
       │ Validation: PASSED! (Matches valid compressed IPv6 bounds)
       ▼
PIIEntity construction
       │  PIIEntity(
       │      text="2001:db8::1",
       │      entity_type=PIIType.IP_ADDRESS,
       │      start=6,
       │      end=17,
       │      confidence=0.98,
       │      source="IPDetector"
       │  )
```

---

## 5. Code Explanation

### 1. BaseDetector Inheritance
The `IPDetector` inherits from `BaseDetector` and implements `detect(text)`. This allows the orchestrator to query it alongside other detectors.

### 2. Regex Candidate Generation
We use two compiled regex patterns (one for IPv4 and one for IPv6) to extract candidate strings. Lookbehind and lookahead checks prevent matching sub-spans of longer invalid strings (such as version numbers).

### 3. `ipaddress` Module
We use Python's standard `ipaddress` module to validate the candidates. Calling `ipaddress.ip_address(string)` parses the text and raises a `ValueError` if the format is invalid.

### 4. IPv4 & IPv6
The `ipaddress.ip_address()` function automatically detects the IP version, allowing us to support both formats using a single validation step.

### 5. Candidate Validation
We wrap the validation check in a `try/except` block:
* If the validation succeeds, we create a `PIIEntity`.
* If a `ValueError` is raised, we discard the candidate and continue.

### 6. PIIEntity
We construct a `PIIEntity` for each match. It stores the match text, the type `PIIType.IP_ADDRESS`, the source `"regex"`, and a confidence score.

### 7. Offsets
We calculate character offsets on the **original text** using match boundary indexes, avoiding index shifting caused by string modifications.

---

## 6. Why Two-Stage Detection?

```text
Normalized Text ──> Regex Candidate Scan ──> ipaddress Validation ──> PIIEntity
```
Using a two-stage detection pipeline is highly efficient:
* **Stage 1 (Candidate Generation)**: Regex patterns quickly scan the text to identify potential matches, filtering out unrelated text.
* **Stage 2 (Validation)**: The `ipaddress` module checks the candidates to ensure they are valid IPs.
* **Why it is better than a giant regex**: Writing a single regex to handle both syntax matching and range validation would result in an unreadable, slow, and error-prone pattern. Splitting the process makes the code clean, fast, and easy to maintain.

---

## 7. Precision vs. Recall

We use a broad regex for candidate generation to achieve high recall, and then apply strict validation to maintain high precision:
* **Broad Candidate Regex**: Matches any four blocks of numbers separated by dots (e.g. matching `999.999.999.999`), ensuring we don't miss any valid IPs (high recall).
* **Validation Check**: Discards invalid matches like `999.999.999.999`, filtering out false positives (high precision).
* **Avoid False Negatives**: If our candidate regex was too strict (e.g., only matching IPs starting with `192.168.`), we would miss other valid IP addresses (low recall). Using a broad regex with a validation check balances both metrics.

---

## 8. Testing

We created **[tests/test_ip_address_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_ip_address_detector.py)** to verify:
* **Valid IPv4 & IPv6**: Tests standard IPv4, IPv6, loopback, and compressed addresses.
* **Invalid Formats**: Asserts that invalid addresses (like `999.999.999.999` or `256.1.1.1`) are discarded.
* **Surrounding Punctuation**: Verifies that trailing punctuation is excluded.
* **Non-IP Rejection**: Asserts that dates (`2026.08.13`) and version numbers (`v1.2.3.4`) are ignored.
* **Duplicates**: Asserts that duplicate IPs are returned as separate entities.

---

## 9. Real Document Testing

Corporate documents rarely contain raw server IP addresses. Running the detector against `input/Red Herring Prospectus.docx` returned **0 candidates**. This helps verify that the detector does not generate false positives on dates or financial metrics present in the document.

---

## 10. Connection Between Commits

Our project pipeline builds incrementally:

* **Commit 5 (BaseDetector)**: Defines the parent interface contract.
* **Commit 6 (EmailDetector)**: Implements regex matching for email formats.
* **Commit 7 (PhoneDetector)**: Implements regex and validation for phone numbers.
* **Commit 8 (IPDetector)**: Subclasses `BaseDetector` and implements candidate generation and validation for IP addresses.
* **Commit 9 (SSNDetector)**: Will build on this structure to implement Social Security Number detection.

---

## 11. Common Beginner Mistakes

* **Regex-Only Validation**: Relying only on regex and missing out-of-range octets (like `256.0.0.1`).
* **Confusing Dates with IPv4**: Matching dates like `2026.08.13` as IP addresses.
* **Forgetting IPv6**: Only implementing IPv4 matching and missing IPv6 addresses.
* **Including Punctuation**: Matching trailing punctuation (like `"192.168.1.1."`), which corrupts the IP text.
* **Losing Original Offsets**: Calculating offsets on normalized text where spaces have been stripped.

---

## 12. Interview Explanation

**Question:** *"How did you detect IP addresses?"*

**Answer:**
> "I implemented a two-stage detection pipeline. First, I used regex patterns with negative lookbehinds and lookaheads to identify candidate strings while ignoring version numbers and dates. Second, I passed the candidates to Python's standard ipaddress module to validate their ranges and formats. Valid matches are returned as PIIEntity objects."

**Question:** *"Why did you use Python's ipaddress module?"*

**Answer:**
> "I used the standard ipaddress module because it handles all IPv4 and IPv6 validation rules, including compressed representations. This avoids the need to write complex range-validation code, making the detector clean and reliable."

**Question:** *"Why didn't you rely only on regex?"*

**Answer:**
> "Regex is designed for pattern matching, not logical validation. A regex can confirm that a string matches the format of four numbers separated by dots, but checking that each number is between 0 and 255 requires logical validation. Using regex alone would result in matching invalid IPs like 999.999.999.999."

---

## 13. Quick Revision

### 5 Key Concepts
1. **`IPDetector`** inherits from `BaseDetector` and implements `detect(text)`.
2. It supports both **IPv4 and IPv6** addresses.
3. Candidate generation uses regex patterns with **alphanumeric boundaries** to avoid false positives.
4. Validation uses the standard **`ipaddress`** module to check ranges and formats.
5. Character offsets are calculated on the **original text** to ensure accurate replacement bounds.

### 3 Interview Questions
1. *Why is it difficult to write a regex that validates octet ranges?*
2. *How does the IP detector prevent false positives on dates like 2026.08.13?*
3. *What are the benefits of separating candidate generation from validation?*

### 3 Practical Examples

#### Example 1: Valid IPv4 Match
* **Input**: `"Connect to 192.168.1.1."`
* **Match**: `"192.168.1.1"`
* **Offsets**: `11` to `22`

#### Example 2: Valid Compressed IPv6 Match
* **Input**: `"IPv6: fe80::1"`
* **Match**: `"fe80::1"`
* **Offsets**: `6` to `13`

#### Example 3: Invalid IP Rejection
* **Input**: `"Version: v1.2.3.4"`
* **Match**: No match (rejected due to the leading alphanumeric character `v`).
