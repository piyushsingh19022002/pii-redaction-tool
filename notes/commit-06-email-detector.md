# Commit 6 Learning Notes: Email PII Detector

This document details the concepts and design decisions implemented in Commit 6 (`feat: add email pii detector`).

---

## 1. Commit Overview

### What This Commit Accomplished
This commit implements our first functional PII detector: `EmailDetector` inside `src/detectors/email.py`. It inherits from the `BaseDetector` contract and uses regular expressions to find email addresses. Additionally, it implements a suite of unit tests inside `tests/test_email_detector.py` to verify the accuracy of the matching bounds.

### Why Email Detection is Our First PII Detector
Email addresses have a structured and predictable syntactic format (local part, `@`, domain root, TLD). This structure makes them an excellent candidate to test the initialization of the detection framework without introducing the complexity of machine-learning models (NER) or context heuristics.

### Why Regex is Suitable for Email Detection
Because emails follow standard pattern rules, regular expressions (regex) are highly efficient at matching them. Regex can parse text for emails in milliseconds, and the matching rules are highly deterministic compared to machine learning classification.

### Why We Avoid an RFC-Complete Email Parser
The official grammar rules for email addresses (RFC 5322) are extremely complex, permitting unusual cases like nested quotes, spaces inside brackets, and IP addresses as domains. Building a parser to capture 100% of these theoretical edge cases is highly complex and unnecessary. For practical PII redaction, a clean, readable regex matching $99.9\%$ of real-world emails is preferred.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` model and the `PIIType.EMAIL` Enum member. | (None for this commit) | Data schema definitions |
| **`src/detectors/base.py`** | Establishes the parent `BaseDetector` interface class. | (None for this commit) | Abstract parent class |
| **`src/detectors/email.py`** | Implements the compiled regex matching and search loops. | Normalized text segment | List of `PIIEntity` matches |
| **`tests/test_email_detector.py`** | Asserts email regex behaviors, boundaries, and offsets. | Test text strings | Unit test pass/fail results |

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow for Commit 6, showing the relations between files:

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
Normalized Text ───> │src/detectors/emai│ 
                     │  EmailDetector   │
                     └────────┬─────────┘
                              │ Matches text using
                              ▼
                         Email Regex
                              │
                              │ Creates
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

## 4. Data Flow

Here is a step-by-step example of how the data flows through the detector:

```text
Step 1: Input text string
"Contact john@example.com today."
       │
       ▼
Step 2: Regex Scan (EmailDetector.detect)
       │ Matches pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
       ▼
Step 3: Match extraction
       │ - Text:  "john@example.com"
       │ - Span:  start = 11, end = 27
       ▼
Step 4: PIIEntity construction
       │  PIIEntity(
       │      text="john@example.com",
       │      entity_type=PIIType.EMAIL,
       │      start=11,
       │      end=27,
       │      confidence=0.95,
       │      source="EmailDetector"
       │  )
       ▼
Step 5: Output list
[PIIEntity(text="john@example.com", start=11, end=27, ...)]
       │
       ▼
Step 6: Sent to Future Resolver (Overlap resolution & replacement)
```

---

## 5. Code Explanation

### 1. BaseDetector Inheritance
The `EmailDetector` inherits from `BaseDetector` and implements `detect(text)`. This allows it to interface seamlessly with our pipeline.

### 2. Compiled Regex
Compiling a regular expression (`re.compile`) parses the pattern string into an in-memory matching engine. This speeds up matching when scanning multiple paragraphs.

### 3. Regular Expressions & Pattern Matching
A sequence of characters defining a search pattern. The system matches this pattern against the text to locate targets.

### 4. Match Spans & Offsets
When a match is found, Python's regex engine provides its boundary offsets:
* `start()`: The inclusive start index of the match in the string.
* `end()`: The exclusive end index.
Using the slice notation `text[start:end]` returns the exact email address.

### 5. `PIIEntity` Creation
We construct a `PIIEntity` for each match. It stores the match text, the type `PIIType.EMAIL`, the source `"regex"` (which denotes how it was found), and a confidence score.

### 6. Detector-Level Confidence
We assign a confidence of `0.95` to our matches. Since email regex matches are highly reliable, we use a high confidence score.

---

## 6. Regex Explanation

Here is the compiled regular expression used in our implementation:
```python
r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}"
```

### Pattern Breakdown:
1. **`[a-zA-Z0-9._%+-]+`**: Matches one or more characters in the email username. This includes letters, numbers, dots (`.`), underscores (`_`), percent signs (`%`), plus signs (`+`), and hyphens (`-`).
2. **`@`**: Matches the literal `@` character.
3. **`[a-zA-Z0-9]`**: Requires the domain name to start with an alphanumeric character (preventing invalid domains like `@.com`).
4. **`[a-zA-Z0-9.-]*`**: Matches the rest of the domain name (alphanumeric characters, dots, and hyphens).
5. **`\.[a-zA-Z]{2,}`**: Matches the TLD (Top-Level Domain). It requires a literal dot followed by at least two letters (e.g. `.com`, `.org`, or `.co.in`).

### Why Regex is Not Perfect for Every Email Syntax
* **False Positives**: Codes like `user@class.method` look like emails but are actually code syntax.
* **False Negatives**: Highly unusual emails (like `admin@company.123`) containing numbers in the TLD will be skipped.

---

## 7. Precision vs. Recall

In machine learning and search engines, we balance two metrics:
* **Precision**: The percentage of matches that are actually correct (fewer false positives).
* **Recall**: The percentage of targets in the text that we successfully matched (fewer false negatives).

### Precision/Recall Balance Examples:

#### Scenario A: High Precision, Lower Recall
If we make our email regex very strict (e.g., only allowing `.com` or `.org` TLDs):
* **Result**: High Precision (we will rarely match anything that isn't a valid email).
* **Downside**: Lower Recall (we will miss valid emails ending in `.in`, `.io`, or `.edu`).

#### Scenario B: High Recall, Lower Precision
If we make our regex very loose (e.g., matching any characters around an `@` symbol):
* **Result**: High Recall (we will catch almost every email).
* **Downside**: Lower Precision (we will match non-emails like `x@y` or code snippets).

Our regex balances both metrics by validating domain boundaries while supporting common TLDs.

---

## 8. Testing

We created **[tests/test_email_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_email_detector.py)** to verify:
* **Valid Emails**: Verifies detection of corporate, Gmail, subdomain, and plus-tag emails.
* **Invalid Emails**: Asserts that malformed inputs (like `@example.com` or `john@.com`) are ignored.
* **Multiple Emails**: Asserts that multiple emails in the same text are all detected.
* **Boundary Punctuation**: Verifies that trailing punctuation is excluded from matches.
* **Offsets**: Asserts that start and end offsets align exactly with the email text.
* **Duplicate Occurrences**: Asserts that duplicate emails are returned as separate entities.

---

## 9. Connection Between Commits

Our project pipeline builds incrementally:

* **Commit 3 (Normalizer)**: Cleans up whitespace and formatting artifacts.
* **Commit 4 (PIIEntity)**: Defines the data model for matches.
* **Commit 5 (BaseDetector)**: Defines the interface contract.
* **Commit 6 (EmailDetector)**: Subclasses `BaseDetector`, processes normalized text, and outputs `PIIEntity` lists.
* **Commit 7 (PhoneDetector)**: Will build on this structure to implement phone number detection.

---

## 10. Common Beginner Mistakes

* **Overly Simple Regex** (e.g. `.*@.*`): Matches too much text, causing high false-positive rates.
* **Trailing Punctuation**: Matching trailing punctuation (like `"john@example.com."`), which corrupts the email text.
* **Off-by-One Offsets**: Calculating incorrect start or end offsets, resulting in misaligned redactions later.
* **Deduplicating Too Early**: Deduplicating matches inside the detector. The detector should return every match; duplicates will be handled by the resolver.
* **Adding Redaction Logic**: Placing pseudonymization or replacement rules inside the detector module.

---

## 11. Interview Explanation

**Question:** *"Why did you use regex for email detection?"*

**Answer:**
> "I used regular expressions for email detection because email addresses follow a highly predictable syntactic structure. Regex matches are fast, lightweight, and deterministic, making them ideal for parsing emails. It also avoids the overhead of loading machine-learning models for patterns that can be defined using structural syntax rules."

**Question:** *"How does your EmailDetector fit into the modular detector architecture?"*

**Answer:**
> "The EmailDetector inherits from our abstract BaseDetector. It implements the detect() method and returns PIIEntity data classes containing character offsets and a confidence score. Because the core pipeline only depends on the BaseDetector contract, it can process EmailDetector output exactly the same way it will process future detectors, keeping the system decoupled."

**Question:** *"How do you balance precision and recall for regex-based PII detection?"*

**Answer:**
> "I balanced them by designing a regex that checks for standard email formatting (like requiring an alphanumeric character at the start of a domain and at least two letters in the TLD) to avoid false positives (high precision). At the same time, it supports subdomains, hyphens, and plus-tags to avoid missing valid emails (high recall). Trailing punctuation is also excluded to ensure accurate matches."

---

## 12. Quick Revision

### 5 Key Concepts
1. **`EmailDetector`** inherits from `BaseDetector` and implements `detect(text)`.
2. Matches are returned as a list of **`PIIEntity`** instances with type `PIIType.EMAIL`.
3. The domain part must start with an alphanumeric character to prevent invalid matches.
4. The TLD is restricted to alphabetical characters to exclude trailing punctuation.
5. Duplicate occurrences are preserved as separate entities.

### 3 Interview Questions
1. *How does your regex ensure trailing punctuation is excluded from matches?*
2. *What is the difference between precision and recall in PII detection?*
3. *Why does the detector preserve duplicate occurrences instead of deduplicating them?*

### 3 Practical Email-Regex Examples

#### Example 1: Standard Corporate Email Match
* **Input**: `"Send to john.doe@company.com."`
* **Match**: `"john.doe@company.com"`
* **Offsets**: `8` to `28`

#### Example 2: Plus-Tag Email Match
* **Input**: `"Register using customer+tag@domain.co.in,"`
* **Match**: `"customer+tag@domain.co.in"`
* **Offsets**: `15` to `40`

#### Example 3: Invalid Email Rejection
* **Input**: `"Invalid email: john@.com"`
* **Match**: No match (rejected because the domain starts with a dot).
