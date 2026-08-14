# Commit 5 Learning Notes: PII Detector Framework

This document explains the concepts and design decisions implemented in Commit 5 (`feat: add modular pii detector framework`).

---

## 1. Commit Overview

### What This Commit Accomplishes
This commit establishes the abstract detector interface framework. It creates the `src/detectors/` directory as a package and defines the abstract base class `BaseDetector` inside `src/detectors/base.py`. Additionally, it implements a suite of unit tests in `tests/test_detector_framework.py` that verifies that the abstract constraints and polymorphic behaviors function correctly.

### Why We Need a Detector Framework
Our system will support many different kinds of detectors (regex matches for emails and SSNs, NLP models for personal names, and context-dependent matches for dates of birth). Without a common framework, each detector would be written in a custom style, forcing the orchestrating code to treat each detector differently.

### What Problem Occurs if Every Detector Has a Different Interface
If every detector had a unique function signature:
* `email_detector.find_emails(text)`
* `ner_detector.extract_persons(text_list, model_name)`
* `phone_detector.match(paragraph)`

The core pipeline would need to hard-code integration code for every single detector class. Adding or removing a detector would require rewriting core files, making the project brittle, difficult to scale, and prone to import bugs.

### Why We Use a Common `detect()` Method
By defining a single abstract method—`detect(text: str)`—we enforce a standard API contract. The pipeline can maintain a simple list of detectors and run detection across all of them in a single, clean loop:
```python
all_entities = []
for detector in detectors:
    all_entities.extend(detector.detect(segment.normalized_text))
```

### Why Every Detector Returns `list[PIIEntity]`
To ensure the downstream **Candidate Resolver** (which resolves overlapping coordinates) and **Pseudonymizer** (which replaces values) do not care which engine found the PII, every detector is required to package its matches in the same uniform data structure: a list of `PIIEntity` objects.

---

## 2. Files Involved

* **[src/models.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/models.py)**: Unmodified, but referenced for its data model definitions.
* **[src/detectors/__init__.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/detectors/__init__.py)**: Created to mark the folder as a package and expose the base interface.
* **[src/detectors/base.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/detectors/base.py)**: Created to define the abstract `BaseDetector` class.
* **[tests/test_detector_framework.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_detector_framework.py)**: Created to verify the framework interface and validation rules.

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/models.py`** | Exposes the `PIIEntity` model structure. | (None for this commit) | Data class structure definition |
| **`src/detectors/__init__.py`** | Promotes clean imports at package boundaries. | Individual sub-modules | Package-level exports |
| **`src/detectors/base.py`** | Establishes the interface contract. | (None for this commit) | Abstract `BaseDetector` interface class |
| **`tests/test_detector_framework.py`** | Tests the framework constraints. | Mock classes and parameters | Verification test pass/fail results |

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow showing how the `BaseDetector` relates to the models and the pipeline:

```text
               ┌────────────────┐
               │  src/models.py │
               └───────┬────────┘
                       │
                       │ Imports PIIEntity
                       ▼
            ┌─────────────────────┐
            │ src/detectors/base.py│
            │     BaseDetector    │
            └──────────┬──────────┘
                       │
                       │ Inherited by
                       ▼
               [Future Detector] 
             (e.g., EmailDetector)
                       │
                       │ Receives
                       ▼
                Normalized Text
                       │
                       │ Processes inside detect()
                       ▼
                list[PIIEntity]
                       │
                       ▼
           [Future Candidate Resolver]
```

---

## 4. Data Flow

### The Pipeline Data Flow:
```text
Input (Normalized Text) ──> BaseDetector.detect() ──> Output (list[PIIEntity]) ──> Future Resolver
```

* **What is actually happening now (Commit 5):** The framework only defines the structure. When we execute tests, we define a small local dummy detector inside the test file to confirm that the text flows correctly into `detect()` and outputs standard `PIIEntity` instances.
* **What will happen in future commits:** Real detectors will implement this interface. When a segment of document text is normalized, it will be passed to a list of active detectors, generating a combined list of PII candidate findings.

---

## 5. Software Engineering Concepts

### 1. Interface/Contract
A set of rules defining how modules communicate. It lists what methods must exist, what parameters they accept, and what they return.

### 2. Abstract Base Class (ABC)
A class that cannot be instantiated on its own. It exists solely to define common structures and method names that child classes must implement.

### 3. ABC (Module)
Python's standard library module (`abc`) that provides the helper structures required to implement Abstract Base Classes.

### 4. `abstractmethod`
A decorator that marks a method in an ABC as abstract. Subclasses **must** override this method, or Python will raise an error when attempting to instantiate them.

### 5. Inheritance
A mechanism where a child class (subclass) adopts the properties and methods of a parent class.

### 6. Polymorphism
The ability of different objects to respond to the same method call in their own specific way. (For example, calling `.detect()` on an email detector vs. an NER name detector behaves differently, but the caller uses the exact same syntax).

### 7. Loose Coupling
Designing modules to have minimal direct dependencies on one another. This allows us to modify the inner workings of one detector without affecting the rest of the application.

### 8. Modularity
Splitting a large application into independent, self-contained files (modules).

### 9. Extensibility
The ease with which developers can add new features (like a new PII category detector) without breaking the existing codebase.

### 10. Type Hints
Special annotations in Python code declaring what data types variables and function signatures expect (e.g., `text: str` and `-> List[PIIEntity]`).

---

## 6. Code Explanation

### `BaseDetector` Walkthrough
```python
from abc import ABC, abstractmethod
from typing import List
from src.models import PIIEntity

class BaseDetector(ABC):
```
* **`ABC` Inheritance**: Marks `BaseDetector` as an abstract class that cannot be initialized directly.

```python
    @abstractmethod
    def detect(self, text: str) -> List[PIIEntity]:
        pass
```
* **`@abstractmethod`**: Tells Python that any subclass (like `EmailDetector`) must implement `detect(self, text: str) -> List[PIIEntity]`.
* **Parameter**: Expects a `str` (which will be `normalized_text`).
* **Return Type**: Formally annotated as `List[PIIEntity]` to enforce standard output formats.

```python
    @property
    def name(self) -> str:
        return self.__class__.__name__
```
* **`name` Property**: A helper that automatically returns the class name. When writing a detector, we don't have to manually write its name; it dynamically exposes it for log files and entity source tags.

### Dependency Rules: Models and Detectors
* **Why it imports `PIIEntity`**: The base class needs to know the type definition of the return objects to enforce type annotations.
* **Why `models.py` must NOT import detectors**: The data models should represent raw data. If `models.py` imported detector classes, it would create circular imports, making the codebase highly coupled and difficult to maintain.

---

## 7. Future Detectors

In subsequent commits, we will expand the `BaseDetector` hierarchy:

```text
                 BaseDetector (ABC)
                         │
        ┌────────┬───────┴────────┬────────┐
        ▼        ▼                ▼        ▼
  EmailDetector PhoneDetector  SSNDetector  NERDetector
 (Commit 6)     (Future)       (Future)     (Future)
```

> [!NOTE]
> None of these concrete detectors are implemented in Commit 5. They will be added incrementally in future commits, ensuring our core base remains clean and tested.

---

## 8. Testing

We added **[tests/test_detector_framework.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_detector_framework.py)** to assert:
* **Abstract Enforcement**: Verifies that calling `BaseDetector()` raises a `TypeError`.
* **Concrete Subclassing**: Defines a local dummy detector (`MockPhoneDetector`) to verify that subclasses can be instantiated and run successfully.
* **Return Constraint**: Asserts that `detect()` returns a list of `PIIEntity` objects, and that it correctly returns an empty list if no matches are found.

**Why we use a fake detector in tests:** It allows us to verify that our base class interface contract functions correctly without needing to write any complex detection rules or NLP libraries.

---

## 9. Connection Between Commits

Our project is designed in a linear, logical stack:

1. **Commit 3 (Normalizer)**: Cleans and normalizes text, preparing it for matching.
2. **Commit 4 (PIIEntity)**: Establishes the standard, immutable data format for representating matches.
3. **Commit 5 (Detector Framework)**: Connects these by defining the `BaseDetector` interface, which takes normalized text (Commit 3) and outputs `PIIEntity` lists (Commit 4).
4. **Commit 6 (Email Detector)**: Will implement the first concrete detector subclassing `BaseDetector`.

---

## 10. Common Beginner Mistakes

* **Putting all detectors in one file**: Writing email, phone, and NER detectors inside `base.py`, defeating the purpose of modular design.
* **Duplicating detection interfaces**: Writing different function names for different detectors rather than overriding `detect()`.
* **Adding PII-specific logic to `BaseDetector`**: Hardcoding rules for specific PII categories directly in the base class.
* **Creating circular dependencies**: Importing detectors inside `models.py`.
* **Over-engineering**: Creating registry modules, configuration managers, or dependency injection setups before they are actually needed.

---

## 11. Interview Explanation

**Question:** *"Why did you create a BaseDetector abstraction?"*

**Answer:**
> "I created the BaseDetector abstraction to establish a formal API contract that decouples the detection engines from the main orchestrator. Since different detectors use different matching rules (like Regex or NLP), a common interface ensures they all accept a standard string input and return a uniform list of PIIEntity objects. This makes it easy to run detectors in a single execution loop and resolve candidates consistently."

**Question:** *"How would you add a new PII detector to your architecture?"*

**Answer:**
> "To add a new detector, I would create a new module in the detectors package, subclass BaseDetector, and implement the abstract detect() method to run our matching logic. Then, I would register the detector in our pipeline. Since the rest of the application only depends on the BaseDetector contract, no changes would be needed in the candidate resolver or document reconstruction modules."

---

## 12. Quick Revision

### 5 Key Concepts
1. **`BaseDetector`** is an Abstract Base Class (ABC) that cannot be directly instantiated.
2. The **`detect(text)`** method signature is an abstract contract that all subclasses must implement.
3. The detector always returns a **list of `PIIEntity`** objects.
4. **Polymorphism** allows us to run different detectors using the exact same code structure.
5. The **`name` property** dynamically extracts the detector's class name, simplifying debugging.

### 3 Interview Questions
1. *What happens if you try to initialize a subclass of BaseDetector that does not define a detect() method?*
2. *How does the BaseDetector contract help keep the candidate resolver decoupled from NLP or Regex libraries?*
3. *Why does BaseDetector define a name property using class names instead of a hardcoded string?*

### 3 Practical Examples

#### Example 1: Defining a Valid Subclass
```python
from src.detectors import BaseDetector
from src.models import PIIEntity

class MySimpleDetector(BaseDetector):
    def detect(self, text: str) -> list[PIIEntity]:
        # Implementation returns list of PIIEntities
        return []
```

#### Example 2: Verifying Abstract Enforcement
```python
import pytest
from src.detectors import BaseDetector

def test_instantiation():
    with pytest.raises(TypeError):
        BaseDetector()  # Raises TypeError: abstract methods not implemented
```

#### Example 3: Subclassing with Incomplete Interface (Will Fail)
```python
from src.detectors import BaseDetector

class BadDetector(BaseDetector):
    pass

# BadDetector() will raise a TypeError because detect() was not implemented
```
