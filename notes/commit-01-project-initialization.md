# Commit 1 Learning Notes: Project Initialization

This document contains beginner-friendly concepts, examples, and roadmap descriptions for the first phase of the PII Redaction Tool project.

---

## 1. What This Commit Accomplished
This commit establishes the foundational scaffolding for the PII Redaction Tool. It creates the core directory structure, specifies exclusion rules for version control, defines testing-related package requirements, and initializes the source folder as a Python package. No functional Python logic or libraries for PII extraction have been added yet, focusing solely on clean configurations.

---

## 2. Why We Created This Project Structure
A structured directory layout separates different parts of your project (e.g., source code, tests, datasets, and configurations). This keeps the workspace organized, facilitates automation, and makes the project easy to navigate for other developers.
* **Simple Example:** Instead of having test scripts, raw input files, processed output files, and Python code mixed together in one flat folder, we group them into dedicated directories.
* **How it will be used later:** We will add individual modules under `src/`, write test cases in `tests/`, place performance evaluation scripts in `evaluation/`, and process documents through `input/` and `output/`.

---

## 3. What `src/` Means
`src` stands for **Source**. This directory houses all the actual source code of the application. The file `src/__init__.py` initializes the directory as a Python package, making it importable.
* **Simple Example:** By writing source code in `src/detector.py`, we can run python commands from other files using `from src.detector import PiiDetector`.
* **How it will be used later:** It will store the modules for extracting text from DOCX, building regex and NER detectors, resolving overlapping candidates, mapping entities to pseudonyms, and reconstructing documents.

---

## 4. What `tests/` Means
The `tests` directory is dedicated to automated tests (such as unit and integration tests) that verify that our code behaves exactly as expected.
* **Simple Example:** A test function `test_email_redactor()` checks if passing `"alice@example.com"` through the redaction system returns a pseudonym like `"[EMAIL_1]"`.
* **How it will be used later:** We will run automated tests from this folder using `pytest` to verify that code changes or updates do not break existing regex rules or document mapping.

---

## 5. What `evaluation/` Means
This directory holds evaluation datasets (sometimes called "gold standard" datasets) and benchmarking scripts to measure the quality of our PII detection algorithms.
* **Simple Example:** An evaluation script reads a set of 100 synthetic documents with known PII locations and computes how many names or phone numbers our tool correctly identified.
* **How it will be used later:** We will place evaluation scripts here to compute Precision, Recall, and F1-scores, allowing us to adjust thresholds and improve accuracy scientifically.

---

## 6. What `input/` and `output/` Mean
These directories represent the boundary of our processing pipeline:
* `input/`: Stores the raw source documents containing sensitive PII.
* `output/`: Stores the redacted or pseudonymized results.
* **Simple Example:** `input/medical_record.docx` is read by the program, and the redacted version is saved to `output/medical_record_redacted.docx`.
* **How it will be used later:** This separation ensures we never corrupt or overwrite the original source data and provides a dedicated directory to check our output files.

---

## 7. What `requirements.txt` Is
This text file lists all external Python packages (libraries) that our project depends on, including their version rules.
* **Simple Example:** Putting `pytest>=8.0.0` in this file tells the package installer to download and install a version of Pytest equal to or greater than 8.0.0.
* **How it will be used later:** As we implement more features, we will append libraries like `python-docx` (for reading and writing DOCX files) and `spacy` (for Named Entity Recognition) to this file.

---

## 8. What `.gitignore` Is
A `.gitignore` file tells Git which files and directories to ignore (not track). This prevents local configurations, temporary cache folders, virtual environments, and secrets from being committed to public repositories.
* **Simple Example:** Adding `.venv/` prevents Git from uploading thousands of third-party package files installed on your local system.
* **How it will be used later:** It ensures that local testing caches (like `.pytest_cache/`) and compiled bytecodes (like `__pycache__/`) generated when executing python commands are kept out of your git commits.

---

## 9. Why Virtual Environments Are Used
A virtual environment (e.g., `.venv`) is an isolated environment on your machine. It allows you to install project-specific Python dependencies without affecting other projects or your system-wide Python installation.
* **Simple Example:** Project A requires `spacy==3.0.0`, while Project B requires `spacy==2.0.0`. Virtual environments allow you to run both projects on the same machine without dependency conflicts.
* **How it will be used later:** We will create a local virtual environment to install and manage the libraries needed for DOCX manipulation and machine learning.

---

## 10. What Git Commits Are
A Git commit is a snapshot of your project files at a specific point in time. It behaves like a save point in a game, recording what changed and who changed it.
* **Simple Example:** Initializing the workspace and committing these files records the "Initial Commit" baseline in your repository's history.
* **How it will be used later:** As each feature (e.g., regular expression detection, NER detection, document writing) is finalized, we make a commit, which makes debugging and code reviews much easier.

---

## 11. Why We Are Developing This Project Incrementally
Incremental development breaks down a complex application into small, manageable, and testable stages. Building the project this way ensures that each component is fully verified before adding the next layer of complexity.
* **Simple Example:** Creating the project structure (Commit 1) before introducing DOCX reading libraries or PII regex rules.
* **How it will be used later:** It prevents major compilation or integration errors from occurring all at once, leading to a much smoother debugging process.

---

## 12. How This Commit Fits Into the Final PII Redaction Architecture
Before executing structure extraction, candidate resolution, or pseudonymization, we must define where our assets live. This commit provides the core workspace scaffolding to support the development of each pipeline component cleanly and safely.

---

## Interview Explanation

**Question:** *"How did you structure your PII redaction project?"*

**Answer:**
> "I structured the project using a clean, modular layout that separates concerns and facilitates incremental development. The core application logic lives in a `src/` directory initialized as a Python package, while automated tests are kept in a separate `tests/` folder to ensure regression testing is easy to run. Data flows are separated using dedicated `input/` and `output/` directories to prevent overwriting raw documents. Finally, I added an `evaluation/` folder for running performance benchmarks, alongside standard configuration files like `.gitignore` and `requirements.txt` to manage dependencies cleanly from day one."
