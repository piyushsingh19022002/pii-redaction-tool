# Commit 15 Learning Notes: PII Pseudonymization and Consistent Mapping

This document details the design patterns, data flow, and verification of Commit 15 (`feat: add pii pseudonymization and consistent mapping`).

---

## 1. Commit Overview

### What Pseudonymization Means
Pseudonymization is a privacy preservation technique where sensitive PII data is replaced with synthetic, realistic-looking values (pseudonyms). Unlike anonymization (which makes the data unrecognizable), pseudonymized text retains its original structural and grammatical context.

### Why We Use Fake Alternatives Instead of Simply Deleting PII
Deleting or blanking out PII (e.g. replacing it with `[REDACTED]`) breaks paragraph readability, ruins sentence structure, and destroys context. For example, a contract reading `"John Doe agreed to pay Jane Smith"` becomes `"[REDACTED] agreed to pay [REDACTED]"`. Using pseudonyms like `"Robert Miller agreed to pay Emma Wilson"` preserves readability and formatting while ensuring no sensitive data is leaked.

### Why Consistent Mapping is Important
If the name `"Rashi Patil"` appears multiple times in a document, replacing it with a different fake name on every occurrence (e.g. `"John Doe"` first, then `"Jane Smith"`) would break the flow and confuse readers. Maintaining a consistent mapping ensures that each unique entity maps to the same pseudonym across the entire document.

### Why Pseudonymization is Separated from DOCX Reconstruction
Reconstruction requires navigating the low-level XML trees of a DOCX file. Pseudonymization is a purely logical step that matches text strings with synthetic values. Separating these steps decouples our core PII processing logic from document formatting libraries.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` model and `PIIType` enum. | (None for this commit) | Data schema definitions |
| **`src/pseudonymizer.py`** | Generates synthetic values and maintains mapping keys. | Accepted `PIIEntity` objects | Synthetic replacement strings |
| **`tests/test_pseudonymizer.py`** | Verifies mapping consistency, independent mappings, and formats. | Dummy candidate entities | Test pass/fail results |

### Input Feed from Commit 14
Commit 14's **Candidate Resolver** filters raw candidates and yields a list of accepted `PIIEntity` objects. These accepted entities are then passed sequentially to the `Pseudonymizer` to fetch or create their synthetic replacements.

---

## 3. Required Commit-Specific Implementation Flow Diagram

Here is the data flow for pseudonymization:

```text
Accepted PIIEntity
        │
        ▼
src/pseudonymizer.py ──(pseudonymize())
        │
        ▼
   Mapping Key ────────(original text + PII type)
        │
        ▼
Existing mapping?
     ┌──┴───┐
    YES     NO
     │      │
     ▼      ▼
  Return  Generate ────(Modular Generators: _generate_person(), etc.)
 existing  fake
  value   value
            │
            ▼
        Store mapping ──(Saved in self.mapping)
            │
     ┌──────┘
     ▼
Fake replacement
     │
     ▼
Future DOCX writer ────(Commit 16)
```

Also showing the module dependencies:

```text
src/models.py (PIIEntity)
      │
      ▼
src/pseudonymizer.py
      │
      ▼ (Tests consistency, formatting, & immutability)
tests/test_pseudonymizer.py
```

---

## 4. Step-by-Step Example

Here is a step-by-step example tracing the evaluation of the candidate `"Rashi Patil"`:

### Step 1: First Occurrence
```text
1. Input: PIIEntity(text="Rashi Patil", entity_type=PIIType.PERSON)
2. Generate Key: key = ("Rashi Patil", PIIType.PERSON)
3. Check self.mapping: Not found.
4. Call self._generate_person():
   - Selects name "John Doe" from pool.
   - Increments self.person_counter.
5. Save in self.mapping: self.mapping[key] = "John Doe"
6. Return: "John Doe"
```

### Step 2: Second Occurrence
```text
1. Input: PIIEntity(text="Rashi Patil", entity_type=PIIType.PERSON)
2. Generate Key: key = ("Rashi Patil", PIIType.PERSON)
3. Check self.mapping: Found! self.mapping[key] exists.
4. Return: "John Doe" (without incrementing counter or generating a new name)
```

---

## 5. Different PII Types

The mapping key consists of both the text and the PII type: `(text, entity_type)`. This is necessary because the same text string can represent different PII types in different contexts:

```text
"John" (PERSON)       ──> Key: ("John", PIIType.PERSON)       ──> Maps to "John Doe"
"John" (ORGANIZATION) ──> Key: ("John", PIIType.ORGANIZATION) ──> Maps to "Example Technologies"
```

Keeping the type in the key prevents naming collisions and ensures that each entity is replaced with a contextually appropriate pseudonym.

---

## 6. Code Explanation

### 1. Mapping Dictionary
We use an internal dict (`self.mapping`) on the `Pseudonymizer` instance to store mapping keys and their pseudonyms.

### 2. Mapping Key
Structured as a tuple `(text, entity_type)` to keep mappings unique.

### 3. PIIType
The Enum used to dispatch candidates to their corresponding generators.

### 4. Generator Functions
Private methods (e.g. `_generate_person()`, `_generate_email()`) that construct realistic, synthetic values.

### 5. Deterministic Behavior
The generators use sequential counters (like `self.person_counter`) to select names from predefined pools. This guarantees deterministic behavior during a session, making tests stable.

### 6. Replacement Formatting
Replacements retain the formatting of the original entity where practical:
* **Credit Cards**: Preserves space or hyphen separators and passes the detector's Luhn checksum.
* **SSNs**: Retains hyphen formatting and uses the unassigned `999-` prefix.
* **DOBs**: Preserves the original delimiter (`/`, `-`, or `.`).
* **Phone numbers**: Preserves country code prefixes like `+91`.

### 7. PIIEntity Preservation
The resolver and pseudonymizer must treat `PIIEntity` as read-only. The original text boundaries are required for DOCX replacements in the next commit, so modifying `PIIEntity.text` directly would corrupt the replacement offsets.

---

## 7. Privacy

* **Internal Mapping Only**: The original-to-fake mapping dictionary is kept in-memory and is never printed in production logs, ensuring no sensitive data is leaked.
* **Safe Synthetic Ranges**: We use unassigned ranges (like U.S. SSN `999-00-xxxx` and documentation IP block `192.0.2.x`) to guarantee we do not generate active real-world data.

---

## 8. Testing

We created **[tests/test_pseudonymizer.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_pseudonymizer.py)** to verify:
* **Unique Mapping**: Asserts that all 9 PII types generate unique, non-empty synthetic replacements.
* **Consistent Replacements**: Verifies that repeated entities map to the same pseudonym.
* **Independent Classifications**: Verifies that the same text with different types maps independently.
* **Immutability Invariant**: Confirms that original properties on `PIIEntity` are not modified.

---

## 9. Connection Between Commits

Our project pipeline builds incrementally:

* **Commit 12 (NER)**: Introduces Named Entity Recognition for person and organization names.
* **Commit 13 (Context)**: Adds positive and negative keyword checking around candidates.
* **Commit 14 (Candidate Resolver)**: Resolves overlapping spans and applies threshold criteria to accept/reject candidates.
* **Commit 15 (Pseudonymization)**: Maps accepted candidates to synthetic, consistent replacements.
* **Commit 16 (DOCX Reconstruction)**: Will compile replacements back into the original document structures.
* **Commit 17 (End-to-End Pipeline)**: Will coordinate the complete pipeline from input DOCX to redacted output.
* **Commit 18 (Evaluation)**: Will measure redaction precision and recall.

---

## 10. Common Beginner Mistakes

* **Nondeterministic Replacements**: Using the `random` module without a seed, which causes test failures.
* **Modifying `PIIEntity.text`**: Overwriting original values in the entity object, which breaks replacement offsets.
* **Using Real Replacement Data**: Using real people's names or addresses as pseudonyms.
* **Exposing Mappings**: Printing the mapping dictionary in logs, leaking sensitive relationships.
* **Mixing Pseudonymization with DOCX Editing**: Combining replacement generation and XML editing in a single class.
* **Ignoring the PII Type in Mapping Keys**: Using the text string alone as the key, causing collisions when the same text represents different PII types.

---

## 11. Interview Explanation

**Question:** *"How do you ensure the same person's name is replaced consistently?"*

**Answer:**
> "I use a mapping dictionary inside the Pseudonymizer class. For each candidate, we generate a unique key using its original text and PII type. If the key exists in our map, we return the registered pseudonym; otherwise, we generate a new synthetic name and store it in the map before returning."

**Question:** *"Why don't you modify PIIEntity during pseudonymization?"*

**Answer:**
> "We treat PIIEntity as read-only. The downstream DOCX writer requires the original offsets and text to identify the replacement targets. Overwriting PIIEntity.text during resolution would break this logic."

**Question:** *"Why is the PII type part of the mapping key?"*

**Answer:**
> "The same string can represent different PII categories. For example, the string 'John' could be a person's first name or part of a company name like 'John & Sons'. Using a compound key (text, type) prevents collisions and ensures each candidate gets a contextually appropriate pseudonym."

**Question:** *"Why did you separate pseudonymization from DOCX reconstruction?"*

**Answer:**
> "Separating these steps decouples our core PII processing logic from low-level XML libraries. Pseudonymization is a purely logical step, while reconstruction is document-specific. This makes the code easier to test and modify."

**Question:** *"How would you make pseudonymization deterministic across multiple runs?"*

**Answer:**
> "I replaced the random module with instance-based counters and predefined lists of names. Because the generation follows a fixed sequence, the mapping remains consistent and reproducible during a session."

---

## 12. Quick Revision

### 5 Key Concepts
1. **Pseudonymization** replaces sensitive values with realistic, fake pseudonyms.
2. The mapping dictionary uses a compound key: **`(original_text, entity_type)`**.
3. **Sequential counters** are used to select names from predefined pools, ensuring deterministic mapping.
4. Replacements preserve original **delimiters and prefixes** where practical.
5. `PIIEntity` candidates are treated as **read-only** to protect replacement offsets.

### 3 Interview Questions
1. *Why should pseudonymization be decoupled from document file editing?*
2. *Why is the PII type included in the mapping dictionary key?*
3. *What safety constraints are used when generating credit cards or SSN replacements?*

### 3 Practical Examples

#### Example 1: Consistent PERSON Match
* **Input**: `"Rashi Patil"`, `"Rashi Patil"`
* **Output**: `"John Doe"`, `"John Doe"` (same pseudonym returned on both matches).

#### Example 2: Safe SSN Replacement
* **Input**: `"123-45-6789"`
* **Output**: `"999-00-0001"` (retains hyphen formatting and uses the unassigned `999` prefix).

#### Example 3: Formatting Retention (Credit Card)
* **Input**: `"4111-1111-1111-1111"`
* **Output**: `"4111-2222-3333-4001"` (passes the mathematical Luhn checksum and retains dash separations).
