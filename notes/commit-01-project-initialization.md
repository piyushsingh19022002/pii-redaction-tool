# Commit 1 Learning Notes: Project Initialization

This document contains a comprehensive, beginner-friendly guide to the concepts, folder structure, and workflows established in Commit 1.

---

## 1. Commit Overview

### What This Commit Accomplished
Commit 1 establishes the empty skeleton structure of our Python-based PII Redaction Tool. It creates the directories where code, tests, evaluation scripts, inputs, and outputs will live, configures the Git ignore rules, specifies initial package requirements, and marks the source folder as a Python package. No functional PII detection or file-parsing code has been written yet.

### Why We Started with Project Initialization
Creating a structured environment before writing code prevents clutter and avoids the need to reorganize files later. It establishes clean boundaries between:
1. Application logic
2. Testing scripts
3. Development data
4. Version control files

### Why We Are Building the Project Incrementally
Building a software system incrementally (commit-by-commit) lets us test and verify each component in isolation before integrating it into a larger system. Starting with an empty, verified workspace makes it easy to confirm that the environment is sound and dependencies compile successfully.

---

## 2. Files and Folders

Here is a breakdown of every directory and file initialized in this commit:

* **`src/`**: The core source code directory.
* **`tests/`**: The directory dedicated to automated unit and integration tests.
* **`evaluation/`**: The directory for storing metric calculations and gold-standard benchmarks.
* **`input/`**: The directory where raw, un-redacted documents are placed.
* **`output/`**: The directory where final, pseudonymized documents are saved.
* **`notes/`**: Holds human-readable learning notes documenting each commit step.
* **`README.md`**: High-level documentation explaining what the project is, the planned pipeline, and the current project state.
* **`requirements.txt`**: Lists third-party Python dependencies required for the project.
* **`.gitignore`**: Defines the exclusion rules that tell Git which files/folders should be omitted from tracking.
* **`src/__init__.py`**: An initialization file that tells Python to treat the `src` folder as a package.

### Responsibility and Consumer Table

| File/Folder | Responsibility | Used By |
| :--- | :--- | :--- |
| **`src/`** | Houses the modular python source files. | Downstream developers & import commands |
| **`tests/`** | Stores test scripts verifying software correctness. | Automated runners (`pytest`) |
| **`evaluation/`** | Stores evaluation scripts for measuring accuracy. | Quality assurance developers & benchmark runners |
| **`input/`** | Temporary storage for raw target DOCX files. | The DOCX extraction module (`docx_reader.py`) |
| **`output/`** | Stores final pseudonymized documents. | The DOCX reconstruction module |
| **`notes/`** | Stores developer learning logs for each commit. | Human readers & new developers |
| **`README.md`** | Explains goals, architecture, and current commit. | Users, interviewers, and team members |
| **`requirements.txt`** | Tracks third-party package definitions. | Python package managers (`pip`) |
| **`.gitignore`** | Excludes compiled bytes, envs, and system files. | Version control system (`git`) |
| **`src/__init__.py`** | Initializes the source folder as an importable module. | Python interpreter |

---

## 3. Required Implementation Flow Diagram

Below is the ASCII diagram illustrating the scope of Commit 1:

```text
[Developer]
     │
     ▼
[Project Structure]
  ├── src/                ──(Prepares for Commit 2 reader logic)
  │    └── __init__.py    ──(Allows modular package imports)
  ├── tests/              ──(Prepares for unit testing)
  ├── evaluation/         ──(Prepares for benchmark metrics)
  ├── input/              ──(Prepares to hold source docx)
  ├── output/             ──(Prepares to hold output docx)
  └── notes/              ──(Prepares to hold learning logs)
     │
     ▼
[Future Application Implementation] (Not present in Commit 1)
- DOCX Extraction (Commit 2)
- Normalization   (Commit 3)
- PII Entities    (Commit 4)
- Detectors       (Commit 5)
```

> [!IMPORTANT]
> **What Commit 1 DOES NOT do:** It does not read any DOCX files, search for PII, or execute any algorithms.
> **What Commit 1 DOES do:** It prepares the directory workspace. By defining `src/__init__.py`, it guarantees that in Commit 2, we can import models from `src` into `tests` without import path issues.

---

## 4. Project Development Flow

The project is designed to evolve incrementally:

```text
[Commit 1: Initialization] ──(Creates folders & configs)
            │
            ▼
[Commit 2: DOCX Extraction] ──(Reads paragraphs/tables into TextSegments)
            │
            ▼
[Commit 3: Normalization]   ──(Cleans whitespace & Unicode artifacts)
            │
            ▼
[Commit 4: PII Entity]      ──(Designs the standard validation dataclass)
            │
            ▼
[Future commits: Detection]  ──(Implements regex, NER, and context matching)
            │
            ▼
[Future commits: Redaction]  ──(Swaps text in-place & writes final DOCX)
            │
            ▼
[Future commits: Evaluation] ──(Calculates Precision and Recall metrics)
```

### Commit 1's Contribution to the Flow
Commit 1 provides the core structure for this entire pipeline. By configuring `.gitignore` and `requirements.txt` early on, we ensure that as we add DOCX extraction (Commit 2) or normalization (Commit 3), we do not accidentally commit temporary testing cache files or system files into version control.

---

## 5. Concepts

### Python Project Structure
A standardized way of organizing project directories to make the codebase clean, readable, and maintainable for team members.

### `src` Directory
Stands for **source**. It separates execution logic from test suites, datasets, or build configurations.

### `tests` Directory
A dedicated directory for automated test files. It is separated from the source folder so that testing dependencies are not packaged in production code.

### `evaluation` Directory
A workspace for computing performance metrics (Precision, Recall, F1) to verify model quality.

### `input/output` Directories
Separates input source documents from output results, ensuring raw data is never overwritten.

### `requirements.txt`
A plain-text manifest file listing the names and versions of third-party libraries needed to run the software.

### `.gitignore`
A text file containing rules that tell Git which directories (like virtual environments) or files (like configuration files or operating system metadata) to ignore.

### `__init__.py`
A special file used by Python to mark a directory as a package. This enables importing files in that directory as submodules (e.g. `from src.models import TextSegment`).

### Virtual Environment
An isolated workspace on a computer containing its own Python installation and library packages, preventing package version conflicts between projects.

### Git Repository
A directory tracking the history of file changes, allowing developers to collaborate and manage code versions.

### Git Commit
A saved snapshot of the repository's files at a specific point in time, complete with a message detailing what changed.

---

## 6. Why Modular Development?

Instead of generating the entire codebase all at once, we build the application incrementally. This practice provides several benefits:
* **Easier Debugging**: If something breaks, we know the issue lies within the code added in the most recent commit.
* **Smaller Changes**: Small, atomic edits are easier to understand.
* **Easier Testing**: We can write unit tests for each individual component (like testing normalization before writing detectors).
* **Easier Code Review**: Reviewers can evaluate logical steps rather than checking thousands of lines of code.
* **Easier Rollback**: If a design choice fails, we can easily revert the codebase to a previous stable commit.
* **Clearer Git History**: A chronological log of how the system was designed and constructed.
* **Easier Explanation in Interviews**: We can walk an interviewer through the logical design stages step-by-step.

---

## 7. Connection to Next Commit

```text
[Commit 1: Structural Setup] ──(Provides package layout)──> [Commit 2: DOCX Extraction]
```
Commit 2 introduces `src/docx_reader.py` and `src/models.py`. It requires reading DOCX files.
* **Why it needs Commit 1:** Without Commit 1, we wouldn't have a `src/` directory initialized as a package to write our reader in, an `input/` folder to store test documents, or a `requirements.txt` to install `python-docx`.

---

## 8. Common Beginner Mistakes

* **Putting all code in one file**: Making a single, giant script containing file parsing, regex, validation, and redaction logic, which is very hard to test.
* **Committing virtual environments**: Forgetting to add `.venv/` or `venv/` to `.gitignore`, resulting in committing thousands of third-party dependency files.
* **Committing secrets**: Storing passwords, API keys, or personal credentials directly in the code or environment files instead of using `.env` files.
* **Installing unnecessary dependencies**: Adding libraries to `requirements.txt` that are not yet needed, which bloats the project environment.
* **Creating too many abstractions**: Over-engineering simple structures with complex class hierarchies too early in development.
* **Making huge Git commits**: Bundling unrelated changes (like fixing a typo and adding a major feature) into a single commit.

---

## 9. Testing & Verification

To verify that Commit 1 was configured correctly, the following terminal commands were executed:

1. **Verify Python packages and package paths**:
   ```bash
   python3 -c "import src; print('Import succeeded')"
   ```
   *Checks if python recognizes the `src` folder as an importable module via `src/__init__.py`.*
2. **Compile python files to verify syntax**:
   ```bash
   python3 -m compileall src/
   ```
   *Ensures that there are no syntax errors in the package files.*
3. **Verify directory structure**:
   ```bash
   find . -maxdepth 2 -not -path '*/.*'
   ```
   *Verifies that the folder skeleton matches our design layout.*

---

## 10. Interview Explanation

**Question:** *"How did you structure your PII Redaction Tool project?"*

**Answer:**
> "I structured the project using a clean, modular layout that separates concerns and facilitates incremental development. The core application logic lives in a `src/` directory initialized as a Python package, while automated tests are kept in a separate `tests/` folder to ensure regression testing is easy to run. Data flows are separated using dedicated `input/` and `output/` directories to prevent overwriting raw documents. Finally, I added an `evaluation/` folder for running performance benchmarks, alongside standard configuration files like `.gitignore` and `requirements.txt` to manage dependencies cleanly from day one."

---

## 11. Quick Revision

### 5 Key Things to Remember
1. **Separation of concerns** is achieved by dividing code (`src/`), tests (`tests/`), and evaluation metrics (`evaluation/`).
2. **`__init__.py`** marks a directory as a Python package, enabling clean absolute/relative imports.
3. **`requirements.txt`** acts as a dependency manifest for reproducible environments.
4. **`.gitignore`** protects the repository from build caches, virtual environments, and secrets.
5. **Incremental commits** serve as progress checkpoints, keeping the codebase manageable.

### 3 Interview Questions
1. *Why should you separate application code from test files in a professional repository?*
2. *What is the purpose of `__init__.py` in Python packages?*
3. *Why is it important to omit virtual environment folders from version control?*

### 3 Important Commands
1. **Initialize virtual environment**:
   ```bash
   python3 -m venv venv
   ```
2. **Install dependency manifest**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run automated test suite**:
   ```bash
   pytest
   ```
