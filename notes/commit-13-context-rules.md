# Commit 13 Learning Notes: Context Aware PII Rules

This document details the design patterns, data flow, and concepts implemented in Commit 13 (`feat: add context aware pii rules`).

---

## 1. Commit Overview

### Why Context is Necessary
Pattern matchers (like regex) and Named Entity Recognition (NER) identify candidates based on formatting or syntactic structure. However, they lack semantic awareness:
* A 9-digit number matches phone number or SSN regexes, but context like `"Order Number"` indicates it is a non-PII sequence.
* A date like `01/02/1995` matches date formats, but context like `"Date of Incorporation"` indicates it is a company event rather than a person's birth date.
Adding context rules introduces semantic awareness, allowing us to evaluate the text surrounding a candidate.

### Why Detector Output is Not Automatically a Final Redaction Decision
Detectors only generate candidate matches. If a detector immediately redacted every match, it would corrupt non-sensitive data (such as invoice dates, order IDs, or general corporate terms). Final redaction decisions are deferred to a later resolution stage that evaluates all combined evidence.

### Difference Between Candidate Detection and Candidate Validation
* **Candidate Detection**: Finding text spans that match structural syntax (e.g. finding dates, numbers, or emails).
* **Candidate Validation**: Analyzing the surrounding semantics, checksums, and context rules to verify if the candidate represents actual PII.

### Positive Context
Surrounding keywords that support classification (e.g. `"born on"` before a date supports labeling it as `DOB`).

### Negative Context
Surrounding keywords that contradict classification (e.g. `"transaction date"` before a date indicates it is NOT a `DOB`).

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Defines the immutable `ContextEvidence` data structure. | (None for this commit) | Data schema definitions |
| **`src/context/__init__.py`** | Exports the public context evaluation interface. | (None for this commit) | Package entry point |
| **`src/context/rules.py`** | Implements the positive/negative context matching logic. | Surrounding text and candidate type | `ContextEvidence` object |
| **`tests/test_context_rules.py`** | Verifies positive/negative keyword matching, boundaries, and windows. | Test strings and candidate offsets | Test pass/fail results |

### Consumer Files
* **[src/detectors/dob.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/detectors/dob.py)** (and other detectors): Will consume this layer to evaluate context evidence.
* **Candidate Resolver** (Future Commit): Will consume the compiled `ContextEvidence` of each entity to make final redaction decisions.

---

## 3. Required Commit-Specific Implementation Flow Diagram

Here is the data flow and class relationship diagram for Commit 13:

```text
Candidate + surrounding text
            │
            ▼
      src/context/rules.py ──(evaluate_context())
            │
            ▼
      Context matching ──────(Case-insensitive, bounded matching)
            │
       ┌────┴─────┐
       ▼          ▼
   Positive    Negative
   Evidence    Evidence
   (DOB, etc)  (Order#, etc)
       │          │
       └────┬─────┘
            ▼
     ContextEvidence ────────(Created from src/models.py)
            │
            ▼
     Future Resolver ────────(Consumes context evidence)
```

Also showing the module dependencies:

```text
src/models.py
      │
      ▼ (Imports ContextEvidence)
src/context/rules.py
      │
      ▼ (Tests evaluate_context())
tests/test_context_rules.py
```

---

## 4. Step-by-Step Examples

### Example 1: `"Date of Birth: 01/02/1995"`
```text
Input: "Date of Birth: 01/02/1995"
Candidate: "01/02/1995" (start = 15, end = 25)
Category: PIIType.DOB

Surrounding Context:
- context_before = "Date of Birth: "
- context_after  = ""

Matching:
- Checked against DOB positive pattern: \b(date of birth|dob|birth date|birthdate|born on|born)\b
- Matches "Date of Birth" in context_before.
- Result: has_positive = True, matched_keyword = "Date of Birth", rule = "DOB_positive", distance = 15
```

### Example 2: `"Date of Incorporation: 01/02/1995"`
```text
Input: "Date of Incorporation: 01/02/1995"
Candidate: "01/02/1995" (start = 23, end = 33)
Category: PIIType.DOB

Surrounding Context:
- context_before = "Date of Incorporation: "
- context_after  = ""

Matching:
- Checked against DOB negative pattern: \b(date of issue|issue date|date of incorporation|incorporation date|...)\b
- Matches "Date of Incorporation" in context_before.
- Result: has_negative = True, matched_keyword = "Date of Incorporation", rule = "DOB_negative", distance = 23
```

### Example 3: `"Contact Number: +91 9876543210"`
```text
Input: "Contact Number: +91 9876543210"
Candidate: "+91 9876543210" (start = 16, end = 30)
Category: PIIType.PHONE

Surrounding Context:
- context_before = "Contact Number: "
- context_after  = ""

Matching:
- Checked against PHONE positive pattern.
- Matches "Contact Number" in context_before.
- Result: has_positive = True, matched_keyword = "Contact Number", rule = "PHONE_positive", distance = 16
```

### Example 4: `"Order Number: 123456789"`
```text
Input: "Order Number: 123456789"
Candidate: "123456789" (start = 14, end = 23)
Category: PIIType.PHONE (or PIIType.SSN)

Surrounding Context:
- context_before = "Order Number: "
- context_after  = ""

Matching:
- Checked against PHONE/SSN negative patterns.
- Matches "Order Number" in context_before.
- Result: has_negative = True, matched_keyword = "Order Number", rule = "PHONE_negative", distance = 14
```

---

## 5. Code Explanation

### 1. Context Window
We inspect a configurable window of text (`window_size` defaults to `30` characters) before and after the candidate. Inspecting nearby text balances performance and context accuracy, avoiding scanning the entire document.

### 2. Keywords
Predefined keyword lists associated with specific PII types. Phrases are sorted by length in reverse order before regex compilation to prevent early partial matches on shorter substrings.

### 3. Positive Evidence
Evidence gathered when supporting keywords are found, indicating the candidate is likely the intended PII type.

### 4. Negative Evidence
Evidence gathered when contradicting keywords are found, indicating the candidate is likely non-sensitive or represents a different entity type.

### 5. Word Boundaries
All keyword matching uses regex word boundary flags (`\b`) to prevent matching substrings of longer words (e.g. preventing the keyword `"mobile"` from matching in `"automobile"`).

### 6. `ContextEvidence`
The dataclass that encapsulates evaluation results. It is defined as a frozen (immutable) class to guarantee thread safety and prevent accidental modification downstream:
```python
@dataclass(frozen=True)
class ContextEvidence:
    has_positive: bool
    has_negative: bool
    matched_keyword: Optional[str] = None
    matched_rule: Optional[str] = None
    distance: Optional[int] = None
```

### 7. Why Rules Don't Redact Anything
Context rules are designed to gather evidence, not make final decisions. Separating context evaluation from redaction logic keeps the modules decoupled and allows future resolver stages to combine multiple signals (like NER, regex, and context) before deciding to redact.

---

## 6. Precision vs. Recall

```text
No Context Check ──────> High Recall (Catch all DOBs, but match all other dates)
Positive Context ──────> Strong Evidence (Only match dates with birth-related labels)
Negative Context ──────> High Precision (Filters out invoice/order dates, reducing false positives)
```

* **No Context**: High recall, low precision.
* **Positive Context**: Increases precision by confirming candidate intent.
* **Negative Context**: Prevents false positives on ambiguous numbers or dates.
* **Broad Keyword Risk**: Using overly broad keywords (like `"number"`) can create false positives by matching unrelated text. Word boundaries and specific phrasing are necessary to keep precision high.

---

## 7. Testing

We created **[tests/test_context_rules.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_context_rules.py)** to verify:
* **Positive & Negative Context**: Asserts correct matches for DOB, phone, email, address, and organization keywords.
* **Edge Cases**: Verifies case-insensitivity, word boundaries, distance values, and window limits.
* **No Redaction Logic in Tests**: Asserts that `evaluate_context()` returns evidence records, verifying that the rules do not make final redaction decisions.

---

## 8. Connection Between Commits

Our project pipeline builds incrementally:

* **Commits 6–12 (Detectors)**: Build individual regex and NER detectors to locate candidates.
* **Commit 13 (Context Evidence)**: Adds semantic evaluation of the surrounding text for each candidate.
* **Commit 14 (Candidate Resolver)**: Will combine candidate and context evidence to resolve overlapping spans.
* **Commit 15 (Validation + Confidence)**: Will calculate global confidence scores and apply negative rules to make final redaction decisions.

---

## 9. Common Beginner Mistakes

* **Treating Context as Final Truth**: Assuming positive context guarantees PII presence, or that negative context immediately invalidates it.
* **Using Overly Broad Keywords**: Matching generic words like `"number"` or `"date"`, which triggers false matches.
* **Scanning the Entire Document**: Searching the entire string instead of using local context windows, causing major performance bottlenecks.
* **Ignoring Negative Context**: Only checking for positive keywords, which fails to filter out common false positives like order IDs.
* **Substring Matching**: Failing to use word boundaries (`\b`), leading to false positives on words like `"automobile"` for `"mobile"`.
* **Monolithic Keyword Functions**: Putting all keywords into one giant nested function, making the code hard to extend.
* **Mixing Context with Redaction**: Writing replacement or redaction code inside the context module.

---

## 10. Interview Explanation

**Question:** *"Why do you need context rules if you already have NER and regex?"*

**Answer:**
> "NER and regex locate candidate text based on structure and syntax, but they cannot determine semantic intent. For example, a 9-digit number matching an SSN regex could be an order ID. Context rules allow us to analyze surrounding text for keywords like 'order number' or 'social security' to verify the candidate's actual meaning."

**Question:** *"How do positive and negative context improve precision?"*

**Answer:**
> "Positive context confirms that surrounding text supports the entity's classification (e.g. 'DOB' before a date), while negative context flags conflicting patterns (e.g. 'issue date' before a date). By identifying both signals, we can filter out false positives while retaining actual PII matches."

**Question:** *"Why don't your context rules directly redact PII?"*

**Answer:**
> "Separating context evaluation from redaction logic keeps the code decoupled and modular. The context rules only gather evidence. Deferring the final decision to a candidate resolver allows us to weigh multiple signals, resolve overlapping spans, and apply global rules before redacting."

**Question:** *"How would you add a new context rule?"*

**Answer:**
> "To add a new rule, I would append the positive or negative keywords to the corresponding dictionary in `src/context/rules.py`. The module automatically compiles these lists into word-bounded, case-insensitive regex patterns, making it easy to support new categories."

---

## 11. Quick Revision

### 5 Key Concepts
1. **Context aware rules** add semantic verification to pattern matching.
2. Context rules gather **evidence**; they do not make final redaction decisions.
3. Uses a **configurable context window** (defaulting to 30 characters) to optimize performance.
4. Uses **word boundaries (`\b`)** to prevent partial substring matches.
5. `ContextEvidence` is **immutable** (`frozen=True`) to guarantee thread safety.

### 3 Interview Questions
1. *What is the difference between candidate detection and candidate validation?*
2. *How do word boundaries prevent false positives in context matching?*
3. *Why should context rules compile evidence rather than modify candidates directly?*

### 3 Practical Examples

#### Example 1: Supporting DOB Context
* **Input**: `"DOB: 01/02/1995"`
* **Evidence**: `has_positive = True`, `matched_keyword = "DOB"`

#### Example 2: Ambiguous Number Rejection
* **Input**: `"Order Number: 123456789"`
* **Evidence**: `has_negative = True`, `matched_keyword = "Order Number"`

#### Example 3: Substring Avoidance
* **Input**: `"My automobile is parked here."`
* **Evidence**: `has_positive = False` (substring `"mobile"` inside `"automobile"` is ignored).
