# Commit 4 Learning Notes: PII Entity Data Model

This document explains the concepts and design decisions implemented in Commit 4 (`feat: add pii entity data model`).

---

## 1. Commit Overview

### What This Commit Accomplishes
This commit defines a common data structure for representing PII (Personally Identifiable Information) entities. We created the `PIIType` Enum and the `PIIEntity` frozen dataclass inside `src/models.py`, along with unit tests verifying their validation behaviors. 

### Why `PIIEntity` is Needed & What Problem It Solves
Different PII detection mechanisms (such as Regular Expressions, Named Entity Recognition, or Context-aware heuristics) identify matches in different internal formats. Without a unified model:
* A Regex detector might return a tuple of `(matched_string, start_char, end_char)`.
* An NLP NER library might return a dictionary of dict-like tokens containing `{"label": "PER", "start": 12, "text": "Alice"}`.
* A Context Rules engine might return a custom object.

Passing different formats downstream makes the Candidate Resolver and Redaction pipelines extremely complex and brittle. They would have to check which detector generated which output and parse them case-by-case. 

### Why All Detectors Must Return a Common Representation
Using a single, common representation (`PIIEntity`) decouples the **detection** phase from the **resolution & redaction** phases. It establishes a contract: regardless of how an entity was found, it is described by the same structured fields, allowing downstream components to process all entities uniformly.

---

## 2. Files Involved

* **[src/models.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/models.py)**: Modified to add `PIIType` and `PIIEntity` definitions and checks.
* **[tests/test_models.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_models.py)**: Created to test entity creation, offset boundaries, type checks, and class immutability.

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Holds data classes representing structural blocks (`TextSegment`) and PII classifications (`PIIEntity`). | Developer parameters (text, type, start, end, confidence, source) | Validated, immutable `PIIEntity` objects |
| **`tests/test_models.py`** | Exercises assertions against the `PIIEntity` model to verify invariants. | Mock inputs and initialization states | Test execution success or failure logs |

---

## 3. Required Implementation Flow Diagram

Below is the layout showing how Commit 4 fits into the data flow:

```text
[Commit 3 Input]
Normalized Text (from TextSegment.normalized_text)
       │
       ▼
[Future Commit: Detector Framework]
Runs regex / NER engines on normalized text
       │
       │ Instantiates
       ▼
[This Commit: src/models.py]
   PIIEntity(text, entity_type, start, end, confidence, source)
       │
       │ Validates invariants in __post_init__
       ▼
Validated, Frozen PIIEntity Object
       │
       ▼
[Future Commit: Candidate Resolver]
Combines and resolves overlapping PIIEntity objects
       │
       ▼
[Future Commit: Redaction & Reconstruction]
Writes replacements back into DOCX paragraphs/tables
```

---

## 4. Data Flow

Here is a step-by-step example of how a piece of text flows into the model:

```text
Step 1: Input text string
"Sarthak Malvadkar" (found inside normalized text at index 15 to 33)
       │
       ▼
Step 2: Detector matches "Sarthak Malvadkar" and classifies it
       │  - Entity Type: PIIType.PERSON
       │  - Coordinates: Start 15, End 33
       │  - Confidence:  0.94
       │  - Source:      "ner"
       ▼
Step 3: Object Construction & Invariant Validation
       │  `PIIEntity(text="Sarthak Malvadkar", entity_type=PIIType.PERSON, start=15, end=33, ...)`
       │  Validation confirms:
       │    - start (15) >= 0 and is integer (True)
       │    - end (33) >= start (15) (True)
       │    - confidence (0.94) is in [0.0, 1.0] (True)
       ▼
Step 4: Output Object
PIIEntity(text="Sarthak Malvadkar", entity_type=<PIIType.PERSON: 'PERSON'>, start=15, end=33, confidence=0.94, source='ner')
       │
       ▼
Step 5: Sent to Future Resolver
Overlaps with other matches are merged or discarded before writing replacements
```

---

## 5. Code Explanation

### Dataclass
A `@dataclass` is a class decorator that automatically implements standard helper methods like `__init__()` (constructor), `__repr__()` (string representation), and `__eq__()` (comparison operator). This saves writing boilerplate code.

### Enum
An `Enum` (Enumeration) is a set of symbolic names bound to unique, constant values. It restricts variables to taking only one of the predefined options, preventing typing mistakes.

### `PIIType` (Enum)
A controlled list of PII types supported by our application (e.g. `PERSON`, `EMAIL`, `PHONE`, etc.). Using an Enum ensures that developers cannot supply arbitrary string types like `"Name"` or `"Email-Address"`; they must use `PIIType.PERSON` or `PIIType.EMAIL`.

### `PIIEntity` (frozen dataclass)
The data container for a single PII match. Defining it with `frozen=True` makes it **immutable**. Once created, its values (e.g. text or offsets) cannot be changed. This guarantees that data remains consistent as it flows down the pipeline.

### Fields
* **`text`**: The raw string match.
* **`start` & `end`**: The character offsets inside the analyzed segment. We follow the standard Python slice convention: **`[start, end)`** where `start` is inclusive and `end` is exclusive.
* **`confidence`**: A floating-point number representing how confident the detector is in its match. We define this range strictly as `0.0` to `1.0` inclusive.
* **`source`**: A label denoting the detector type (e.g. `"regex"`, `"ner"`, `"context"`), which is useful for debugging and tracing why a match occurred.

### Validation (`__post_init__`)
Because `PIIEntity` is frozen, we perform validations inside `__post_init__` immediately after construction. We verify parameter types and value ranges, raising `ValueError` or `TypeError` if they violate basic rules.

---

## 6. Why Each Field Exists

| Field | Meaning | Why needed later |
| :--- | :--- | :--- |
| `text` | The exact matched substring. | Used by the validator to check checksum rules (e.g., Luhn check on a credit card number) and by the pseudonym engine to map it to a consistent pseudonym. |
| `entity_type` | Category of PII (e.g., `EMAIL`, `SSN`). | Tells the pseudonym engine which fake entity type to generate (e.g. replacing an email with a fake email, or a name with a fake name). |
| `start` | Starting character index of the match. | Used by the resolver to detect overlapping candidates and by the reconstructor to align replacements. |
| `end` | Ending character index of the match. | Used alongside `start` to calculate lengths and slice/replace targeted text. |
| `confidence` | Numeric rating of detection certainty. | Used by the resolver to decide which candidate wins when multiple rules overlap (e.g., keeping a high-confidence match over a low-confidence one). |
| `source` | Identifies the generator strategy. | Used for logging, auditing, and debugging rule conflicts. |

---

## 7. Connection With Other Commits

```text
[Commit 3: Normalizer] ──(Normalized Text)──> [Commit 4: PIIEntity Model] ──(Structured Entities)──> [Commit 5: Detectors]
```

* **What Commit 4 receives conceptually from Commit 3:** Normalization cleans text for matching. Future detectors in Commit 5 will run search algorithms on `TextSegment.normalized_text` (Commit 3) and locate character index positions.
* **What future detector frameworks will use from Commit 4:** When a detector finds a match, it wraps the match coordinates inside a `PIIEntity` (Commit 4) and returns it.
* **Why this common model makes the architecture modular:** It establishes a clear boundary. We can swap out detector implementations, update NLP libraries, or add new regex rules without changing the resolver or redaction engine, as long as all output models adhere to the `PIIEntity` format.

---

## 8. Testing

We created **[tests/test_models.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_models.py)** to assert that the validation checks work correctly.
* **Valid initializations**: Tests that proper `PERSON`, `EMAIL`, and source parameters initialize without errors.
* **Range checks**: Asserts that `[start, end)` conventions match slice index ranges.
* **Confidence limits**: Verifies that values like `0.0` and `1.0` pass, while values like `-0.1` or `1.1` raise a `ValueError`.
* **Negative/inverted offsets**: Asserts that negative start indexes or end indexes that occur before start indexes are rejected.
* **Type-checking**: Asserts that strings are rejected when assigned to `entity_type`, forcing the use of the `PIIType` Enum.
* **Immutability checks**: Verifies that trying to overwrite properties on a created `PIIEntity` raises a `FrozenInstanceError`.

**Why validation tests are useful:** They catch bugs during development. If a detector developer accidentally returns a negative start offset or incorrect confidence boundaries, the code will fail immediately at construction rather than causing silent offset corruption bugs in the final document reconstruction step.

---

## 9. Common Mistakes

1. **Incorrect Offset Mapping**: Forgetting that `start` is inclusive and `end` is exclusive, leading to off-by-one errors when slicing text.
2. **Mutating Entities In-Place**: Trying to change the confidence or class type of a `PIIEntity` directly. Since the dataclass is frozen, this will raise a `FrozenInstanceError`. Instead, use `dataclasses.replace(entity, confidence=new_val)`.
3. **Using Arbitrary Strings for Entity Types**: Passing a string like `"Person"` to `entity_type` instead of the Enum member `PIIType.PERSON`, which fails our type validations.
4. **Mixing Logic into the Data Model**: Writing detection regexes or loading NER models directly inside the `PIIEntity` class. The data model should remain a simple, lightweight structure that only represents facts.

---

## 10. Interview Explanation

**Question:** *"Why did you create a common PIIEntity model instead of letting each detector return its own result format?"*

**Answer:**
> "I created a common PIIEntity model to establish a clear contract between detection and redaction, decoupling the two phases. Different detection engines—like Regex, NER, and Context Rules—produce outputs in different shapes. If each detector returned its own custom format, the downstream candidate resolver and document writer would need complex logic to handle each variant. By enforcing a single, immutable, and validated PIIEntity model as the output for all detectors, we ensure that the resolver and reconstruction pipelines can process all findings uniformly. This keeps the architecture clean, modular, and easy to extend."

---

## 11. Quick Revision

### 5 Key Things to Remember
1. `PIIEntity` is a **frozen (immutable) dataclass**, meaning its attributes cannot be changed after creation.
2. `PIIType` is an **Enum** that restricts entity classifications to controlled categories.
3. Character offsets follow the standard Python slice convention: **`[start, end)`** where `start` is inclusive and `end` is exclusive.
4. Confidence scores must strictly be float/int values in the range **`[0.0, 1.0]`**.
5. Validations run in **`__post_init__`** to verify parameters immediately upon construction.

### 3 Interview Questions
1. *What is a frozen dataclass, and why is it preferred for representing detection results?*
2. *Why do we validate data model attributes inside `__post_init__` rather than in standard methods?*
3. *How does having a common PII model decouple detection engines from the candidate resolution pipeline?*

### 3 Practical Examples

#### Example 1: Instantiating a Valid Person Candidate
```python
from src.models import PIIEntity, PIIType
entity = PIIEntity("John Doe", PIIType.PERSON, 0, 8, 0.95, "regex")
# Valid construction, passes all assertions
```

#### Example 2: Accessing Text Slices Using Offsets
```python
segment_text = "Contact Alice at 555-0199"
# Alice is at index 8 to 13
entity = PIIEntity("Alice", PIIType.PERSON, 8, 13, 0.99, "ner")
assert segment_text[entity.start : entity.end] == "Alice"
```

#### Example 3: Immutability Verification
```python
from dataclasses import replace
entity = PIIEntity("Mumbai", PIIType.ADDRESS, 0, 6, 0.8, "regex")

# Trying to modify directly raises FrozenInstanceError:
# entity.confidence = 0.9  <-- Throws Error!

# Correct way to update attributes:
updated_entity = replace(entity, confidence=0.9)
assert updated_entity.confidence == 0.9
```
