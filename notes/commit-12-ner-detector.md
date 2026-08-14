# Commit 12 Learning Notes: NER Detector for Person and Organization

This document details the concepts and design decisions implemented in Commit 12 (`feat: add ner detector for person and organization`).

---

## 1. Commit Overview

### What NER Means
NER (Named Entity Recognition) is a subtask of Information Extraction that identifies and classifies named entities in text into predefined categories (such as names of people, organizations, locations, expressions of times, quantities, etc.).

### Why Regex is Not Enough for Names and Organizations
Unlike email addresses or phone numbers, names and organization names do not follow strict syntax rules:
* A person's name (e.g. `John Doe`) consists of standard capitalized words, which look identical to the start of a sentence or other capitalized nouns.
* An organization name (e.g. `Scaler AI Labs`) can contain generic words, abbreviations, and vary in length.
* Writing regular expressions to match all possible name variations is impossible.

### Why spaCy is Being Introduced
To detect names and organizations, we need to analyze semantic and syntactic patterns in sentences. `spaCy` is an industrial-strength Natural Language Processing (NLP) library in Python that provides pre-trained models to extract named entities.

### What PERSON and ORG Mean
* **`PERSON`**: spaCy's entity label representing people, including fictional characters.
* **`ORG`**: spaCy's entity label representing companies, agencies, institutions, and organizations.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` schema and the `PIIType.PERSON` and `PIIType.ORGANIZATION` Enum members. | (None for this commit) | Data schema definitions |
| **`src/detectors/base.py`** | Establishes the parent `BaseDetector` interface class. | (None for this commit) | Abstract parent class |
| **`src/detectors/ner.py`** | Implements the `NERDetector` subclass wrapping the loaded spaCy model. | Normalized text segment | List of `PIIEntity` matches |
| **`tests/test_ner_detector.py`** | Tests PERSON/ORG classifications,Mixed sentences, and character boundary offsets. | Test text strings | Unit test pass/fail results |
| **`requirements.txt`** | Registers third-party library dependencies. | (None for this commit) | Dependency configuration |

---

## 3. Required Commit-Specific Implementation Flow Diagram

Here is the data flow and file relationship diagram for Commit 12:

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
Normalized Text ───> │src/detectors/ner.│ <──────── tests/test_ner_detector.py
                     │   NERDetector    │           (Tests the implementation)
                     └────────┬─────────┘
                              │ NERDetector.detect()
                              ▼
                       spaCy NLP Model ──────────(Loads 'en_core_web_sm')
                              │
                              ▼
                        Named Entities
                              │
                           ┌──┴──┐
                           │     │
                        PERSON  ORG
                           │     │
                           ▼     ▼
                    PIIType.PERSON  PIIType.ORGANIZATION
                           │     │
                           └─────┬─────┘
                                 ▼
                             PIIEntity
                                 │
                                 ▼
                          list[PIIEntity]
                                 │
                                 ▼
                     [Future Resolver Stage]
```

---

## 4. Step-by-Step Example

Here is a step-by-step example of how the input `"Rashi Patil joined Scaler AI Labs."` flows through the detector:

```text
Input text string:
"Rashi Patil joined Scaler AI Labs."
       │
       ▼
nlp(text) processing (NERDetector.detect)
       │ Runs the spaCy model over the text
       ▼
doc.ents matching
       │ Matches two entities:
       │  1. Text: "Rashi Patil" (label = PERSON, start_char = 0, end_char = 11)
       │  2. Text: "Scaler AI Labs" (label = ORG, start_char = 19, end_char = 33)
       ▼
PIIEntity conversion
       │ Maps PERSON -> PIIType.PERSON
       │ Maps ORG -> PIIType.ORGANIZATION
       │ Standard confidence = 0.85, source = "ner"
       ▼
Output list
[
    PIIEntity(text="Rashi Patil", entity_type=PIIType.PERSON, start=0, end=11, ...),
    PIIEntity(text="Scaler AI Labs", entity_type=PIIType.ORGANIZATION, start=19, end=33, ...)
]
```

---

## 5. Code Explanation

### 1. BaseDetector
The `NERDetector` inherits from `BaseDetector` and implements `detect(text)`.

### 2. `NERDetector`
The detector class responsible for running spaCy NER and mapping entities.

### 3. spaCy
The NLP library used to parse sentences and identify named entities.

### 4. `en_core_web_sm`
The standard, small English model downloaded from spaCy. It is optimized for speed and size.

### 5. `nlp(text)`
Executes the spaCy pipeline over the input string, performing tokenization, tagging, parsing, and entity recognition.

### 6. `doc.ents`
A tuple of named entity spans extracted by the model.

### 7. `ent.label_`
The classification label assigned to the entity (e.g. `PERSON` or `ORG`).

### 8. `ent.start_char`
The starting character offset of the entity span in the original string.

### 9. `ent.end_char`
The ending character offset of the entity span in the original string.

### 10. PIIEntity Mapping
Matches are mapped to their corresponding `PIIType` categories:
* `PERSON` $\rightarrow$ `PIIType.PERSON`
* `ORG` $\rightarrow$ `PIIType.ORGANIZATION`

### 11. `source="ner"`
Denotes that the match was identified using Named Entity Recognition.

---

## 6. NER vs. Regex

| Feature | Regex | NER |
| :--- | :--- | :--- |
| **Strengths** | Fast, deterministic, matches structured patterns with 100% precision. | Context-sensitive, matches unstructured names and concepts. |
| **Weaknesses** | Cannot match variable names (like human names) or companies. | Slower, non-deterministic, can produce false positives on capitalized nouns. |
| **Best Used For** | Emails, Phone Numbers, IP Addresses, SSNs, Credit Cards. | Person Names, Company/Organization Names. |

---

## 7. Model Limitations

* **False Positives**: General capitalized words (like `"Offer"` in financial text) or locations (like `"Baner"`) can be misclassified as people or companies.
* **False Negatives**: The model can miss unfamiliar or newly coined company names (e.g. `"Scaler"`) if the surrounding context is ambiguous.
* **Context Sensitivity**: A word's classification depends on its position in the sentence. Capitalizing words in headers or tables can confuse the model.
* **Domain Mismatch**: Pre-trained models are trained on news corpora, not financial prospectuses. This leads to false positives on financial terms and locations in corporate filings.
* **Entity Boundary Issues**: The model can include surrounding words in the entity span (e.g. matching `"the Acme Corporation"` instead of `"Acme Corporation"`).
* **Model Confidence Limitations**: The standard spaCy transition-based parser does not expose individual entity confidence scores. To address this, we assign a default detector-level confidence of `0.85`.

---

## 8. Precision vs. Recall

* **Recall**: NER improves recall by matching names that do not follow fixed patterns, ensuring we catch potential PII.
* **Precision**: The model's flexibility leads to false positives on capitalized nouns, lowering precision.
* **Resolution**: To balance these metrics, future commits will introduce a candidate resolver and context rules (such as whitelists/blacklists) to filter out false positives.

---

## 9. Testing

We created **[tests/test_ner_detector.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_ner_detector.py)** to verify:
* **PERSON/ORG Classifications**: Testing standard names (e.g. `"Rashi Patil"`) and organizations (e.g. `"Acme Corporation"`).
* **Mixed Sentences**: Verifying that both entity types are extracted correctly from the same sentence.
* **Offset Verification**: Verifying the slice invariant `text[start:end] == entity.text`.
* **Duplicates**: Asserts that duplicate names are returned as separate entities.

> [!WARNING]
> Because model behavior varies by version, we use clear, standard names in our tests to prevent model-version classification failures.

---

## 10. Real Document Testing

Running the detector against `input/Red Herring Prospectus.docx` returned:
* **Total PERSON entities detected**: 781
* **Total ORGANIZATION entities detected**: 2658
* **Correct Detections**: Successfully matched real people names (e.g. `Sarthak Malvadkar`) and company names (e.g. `KSH INTERNATIONAL LIMITED`).
* **False Positives (PERSON)**: Matches geographic locations (`Chakan Taluka - Khed`, `Baner`) and general nouns (`Offer`) as people because of their capitalization.
* **False Positives (ORGANIZATION)**: Matches document titles (`RED HERRING PROSPECTUS`) and financial categories (`Anchor Investors`, `Bid/Offer Closing Day`) as organizations.

---

## 11. Connection Between Commits

Our project pipeline builds incrementally:

* **Commit 8 (IPDetector)**: Implements regex and range validation for IP addresses.
* **Commit 9 (SSNDetector)**: Implements regex and validation for SSNs.
* **Commit 10 (CreditCardDetector)**: Implements regex and Luhn validation for credit card numbers.
* **Commit 11 (DOBDetector)**: Implements regex, calendar validation, and local context checks for DOBs.
* **Commit 12 (NERDetector)**: Subclasses `BaseDetector` and implements spaCy-based NER for Person and Organization names.

> [!NOTE]
> NER is complementary to regex. It handles unstructured data (names, companies), while regex handles structured formats (emails, phone numbers, IPs).

---

## 12. Common Beginner Mistakes

* **Assuming NER Detects Every Name**: Expecting 100% accuracy from pre-trained models.
* **Treating ORG as Automatically Safe to Redact**: Redacting every ORG match, which would redact generic terms like `"Anchor Investors"` or `"RED HERRING PROSPECTUS"`.
* **Reloading the Model on Every `detect()` Call**: Loading the model in `detect()` instead of `__init__`, which causes major performance bottlenecks.
* **Losing Offsets**: Calculating offsets on normalized text where spaces have been stripped.
* **Modifying Detected Text**: Returning normalized text in `PIIEntity.text` instead of the original text, which breaks replacement logic.
* **Relying Entirely on NER**: Using NER for structured data like phone numbers or emails, which are more accurately handled by regex.
* **Assuming Model Confidence is Always Available**: Trying to access entity confidence scores from spaCy's default parser, which are not exposed.

---

## 13. Interview Explanation

**Question:** *"Why did you use NER for names and organizations?"*

**Answer:**
> "Unlike emails or phone numbers, human names and company names do not follow fixed syntax rules. They consist of standard capitalized words that look identical to other capitalized nouns in text. For this reason, regex is insufficient, and we must use a pre-trained Named Entity Recognition model to analyze the sentence structure and identify entities based on context."

**Question:** *"Why didn't you use regex for names?"*

**Answer:**
> "Names are highly variable and draw from a massive vocabulary of words across different cultures. Writing a regex to match all possible name variations is impossible. A regex would also generate numerous false positives on capitalized nouns at the start of sentences."

**Question:** *"Which NER model did you use?"*

**Answer:**
> "I used spaCy's standard English model, en_core_web_sm. It is a lightweight, transition-based NER pipeline that is optimized for speed and size, making it suitable for processing text segments efficiently."

**Question:** *"What are the limitations of spaCy NER?"*

**Answer:**
> "The model is trained on news corpora, not financial prospectuses, which leads to false positives on capitalized financial terms and locations in corporate filings. It also does not expose individual entity confidence scores, so we assign a default detector-level confidence of 0.85."

**Question:** *"Why do you still need regex detectors if you have NER?"*

**Answer:**
> "NER is non-deterministic and can miss structured formats like phone numbers or emails. Regex is much faster and guarantees 100% accuracy for structured patterns, while NER is complementary and is reserved for unstructured names and organizations."

---

## 14. Quick Revision

### 5 Key Concepts
1. **`NERDetector`** inherits from `BaseDetector` and implements `detect(text)`.
2. It uses spaCy's **`en_core_web_sm`** model to extract entities.
3. The model is **loaded once** during initialization (`__init__`) to optimize performance.
4. It maps **`PERSON`** to `PIIType.PERSON` and **`ORG`** to `PIIType.ORGANIZATION`.
5. `source` is set to **`"ner"`** and confidence is set to **`0.85`**.

### 3 Interview Questions
1. *Why is NER better suited for name detection than regular expressions?*
2. *What performance problems occur if you load an NLP model inside a detect() loop?*
3. *Why does a model trained on news articles generate false positives in a financial prospectus?*

### 3 Practical Examples

#### Example 1: Valid PERSON Match
* **Input**: `"John Doe works here."`
* **Match**: `"John Doe"` (PERSON, offsets `0` to `8`)

#### Example 2: Valid ORG Match
* **Input**: `"Acme Corporation released a report."`
* **Match**: `"Acme Corporation"` (ORGANIZATION, offsets `0` to `16`)

#### Example 3: False Positive Example
* **Input**: `"This is a Red Herring Prospectus."`
* **Match**: `"Red Herring Prospectus"` (ORGANIZATION, offsets `10` to `32`) - mismatched due to capitalization.
