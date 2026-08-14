# Commit 17 Learning Notes: End-to-End Redaction Pipeline and CLI

This document details the design patterns, orchestration layers, and verification of Commit 17 (`feat: add end to end redaction pipeline and cli`).

---

## 1. Commit Overview

### What an End-to-End Pipeline Is
An end-to-end pipeline links separate text processing tasks into a single run:
$$\text{Input Document} \rightarrow \text{Extraction} \rightarrow \text{Normalization} \rightarrow \text{Detection} \rightarrow \text{Context Evaluation} \rightarrow \text{Resolution} \rightarrow \text{Pseudonymization} \rightarrow \text{Redaction} \rightarrow \text{Redacted Output}$$

### Why Orchestration Should Be Separated from Component Logic
* **De-coupling**: Individual components (like detectors and mappers) remain simple and independent. They do not know about document layouts or CLI flags.
* **Maintainability**: If we want to replace the DOCX library or change context rules, we only edit that specific module. The pipeline's core structure remains untouched.
* **Testability**: We can test each component in isolation with standard unit tests, or run integration tests on the orchestrator using mock components.

### How All Previous Commits Connect
All previous commits were standalone modules. Commit 17 links them together:
* Commits 1–4 handle document reading and text segmentation.
* Commits 5–12 build the detector framework and implement the PII scanners.
* Commits 13–15 filter matches based on context keywords, resolve overlaps, and map accepted entities to pseudonyms.
* Commit 16 edits the document runs.
* Commit 17 orchestrates the entire process.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/pipeline.py`** | Coordinates all PII scanning, resolution, mapping, and redaction stages. | Input path, output path, and detectors | `PipelineResult` statistics |
| **`src/main.py`** | Exposes the CLI options, performs path validations, and configures logging. | Command-line arguments | Printed summary and exit codes |
| **`tests/test_pipeline.py`** | Runs end-to-end integration tests using synthetic DOCX files. | Temporary files and mock configurations | Test pass/fail results |

### Previous Components Called by the Pipeline
* **`src/docx_reader.py`**: Extracts text segments from paragraphs and table cells.
* **`src/normalizer.py`**: Prepares raw text for detectors (e.g. collapsing spaces).
* **`src/detectors/*`**: Runs regex scans and NER on each segment.
* **`src/context/rules.py`**: Gathers evidence keywords surrounding candidates.
* **`src/resolver.py`**: Scores candidates and filters out overlapping spans.
* **`src/pseudonymizer.py`**: Assigns consistent, deterministic replacements.
* **`src/docx_redactor.py`**: Modifies the document XML runs in-place.

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow for the end-to-end pipeline:

```text
Input DOCX
    │
    ▼
docx_reader.py ───────────────(extract_segments())
    │
    ▼
TextSegments ─────────────────(List of TextSegment objects)
    │
    ▼
Detector Registry ────────────(List of registered detectors)
    │
    ├── Regex detectors ──────(Email, Phone, IP, SSN, CC, DOB)
    └── NER Detector ─────────(spaCy PERSON and ORGANIZATION)
    │
    ▼
PII Candidates ───────────────(List of PIIEntity objects)
    │
    ▼
Context Rules ────────────────(evaluate_context() evidence)
    │
    ▼
Candidate Resolver ───────────(resolve_candidate() & resolve_overlaps())
    │
    ▼
Accepted Candidates ──────────(Filtered list of PIIEntity objects)
    │
    ▼
Pseudonymizer ────────────────(get_or_create_mapping() shared instance)
    │
    ▼
Replacements ─────────────────(List of (Segment, Entity, Replacement))
    │
    ▼
DOCX Redactor ────────────────(redact_docx() edits runs in-place)
    │
    ▼
Output DOCX ──────────────────(Redacted document saved successfully)
```

---

## 4. Step-by-Step Execution

When the user runs:
```bash
python3 -m src.main --input input.docx --output output.docx
```
the following sequence is executed:

1. **CLI Parsing**: `main.py` parses arguments using `argparse` and initializes the console logging level.
2. **Path Validation**: Confirms that `input.docx` exists, has a `.docx` suffix, and that the input and output paths are different.
3. **Pipeline Initialization**: Instantiates `PIIRedactionPipeline` (loading detectors and models).
4. **Document Extraction**: The pipeline calls `extract_segments()`, generating a list of paragraphs and table cells.
5. **PII Detection**: For each segment, the pipeline loops over the detector registry, collecting all matching candidates.
6. **Context Evaluation**: Runs keyword checks for each candidate to gather positive or negative evidence.
7. **Candidate Resolution**: Applies threshold scoring and resolves overlapping spans at the segment level.
8. **Consistent Pseudonymization**: Maps accepted candidates to fake names. A single `Pseudonymizer` instance is shared across all segments to keep replacements consistent.
9. **Document Reconstruction**: Calls `redact_docx()` to modify the xml runs in-place and save the file.
10. **Summary Report**: Prints the total count of processed segments and redacted PII types to stdout.

---

## 5. Component Responsibilities

The pipeline follows a strict separation of concerns:
* **`docx_reader.py`** extracts text segments. It does **not** scan for PII.
* **`detectors`** scan text and find candidates. They do **not** resolve overlaps or redact text.
* **`resolver`** filters candidates and resolves overlaps. It does **not** generate synthetic replacements.
* **`pseudonymizer`** generates fake replacements. It does **not** edit document files.
* **`docx_redactor`** applies replacements to document runs. It does **not** scan for PII.
* **`pipeline.py`** orchestrates these steps. It does **not** contain detection or redaction logic.

---

## 6. CLI

* **`argparse`**: Standard Python library used to parse command-line arguments.
* **`--input` / `--output`**: Required arguments defining the input and output file paths.
* **Validation**: Ensures that the input file exists and is a valid `.docx` file.
* **Exit Codes**: Exits with code `0` on success, or code `1` on error.
* **Logging**: Configured using standard logging. Supports the `--verbose` flag to toggle detailed debug-level logging.

---

## 7. Privacy-Safe Logging

Logs and summaries must **never** output raw PII. 

```text
Bad:  2026-08-14 01:37:28 [INFO] Detected PERSON: John Doe
Good: 2026-08-14 01:37:28 [INFO] Detected PERSON candidates: 1
```

**Why**: Writing raw PII to logs creates a secondary data leak, as log files are often stored in plain-text on servers. We only log entity types and counts.

---

## 8. Pseudonymizer Lifecycle

A single `Pseudonymizer` instance is created once at the beginning of the pipeline run and shared across all segments.

If we instantiated a new `Pseudonymizer` for each segment:
* The mapping cache would be cleared after each segment.
* The name `"John Doe"` in Paragraph 1 might map to `"Robert Miller"`, while the same name in Paragraph 2 maps to `"Emma Wilson"`, breaking the document's consistency.

---

## 9. Testing

We created **[tests/test_pipeline.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_pipeline.py)** to verify:
* **Integration Tests**: Tests the entire pipeline end-to-end using temporary DOCX files.
* **Shared Instance Checks**: Confirms that duplicate names located in different paragraphs map to the same pseudonym.
* **Error Handling**: Verifies that missing files raise a `FileNotFoundError`.
* **Prospectus Smoke-Test**: Verifies that the tool runs successfully on the prospectus, saving a readable document.

---

## 10. Connection Between Commits

Here is our pipeline's development timeline:

```text
Commit 1 (Project foundation, setup workspace)
   │
   ▼
Commit 2 (DOCX Structure Extraction: paragraphs and cells)
   │
   ▼
Commit 3 (Text Normalization: Unicode and space cleaning)
   │
   ▼
Commit 4 (PII Entity Model: definition of PIIEntity)
   │
   ▼
Commit 5 (Detector Framework: base detector class)
   │
   ▼
Commit 6 (Email Detector) ────► Commit 7 (Phone Detector) ────► Commit 8 (IP Detector)
   │
   ▼
Commit 9 (SSN Detector) ──────► Commit 10 (Credit Card) ──────► Commit 11 (DOB Detector)
   │
   ▼
Commit 12 (NER Detector: spaCy PERSON and ORGANIZATION)
   │
   ▼
Commit 13 (Context Aware Rules: positive/negative checks)
   │
   ▼
Commit 14 (Candidate Resolver: resolving overlap spans)
   │
   ▼
Commit 15 (Pseudonymization: deterministic replacements)
   │
   ▼
Commit 16 (DOCX Redaction: run-level edits)
   │
   ▼
Commit 17 (End-to-End Pipeline & CLI Orchestrator)
   │
   ▼
Future Commit 18 (Evaluation Framework metrics)
```

---

## 11. Common Beginner Mistakes

* **Putting All Logic in `main.py`**: Writing extraction, detection, and redaction logic directly in the CLI script, which makes the code hard to test and reuse.
* **Creating a New Pseudonymizer per Segment**: Clearing the mapping cache on each segment, which leads to inconsistent pseudonyms.
* **Loading Models Repeatedly**: Loading the spaCy model inside the loop for each segment, which severely degrades performance.
* **Opening and Saving DOCX Files Repeatedly**: Writing to the DOCX file after each replacement instead of editing the document in-memory and saving once.
* **Logging Raw PII**: Printing sensitive values in log outputs.
* **Swallowing Errors**: Using broad `try/except` blocks that catch and ignore exceptions, hiding bugs.
* **Overwriting the Original Input**: Overwriting the input file by default. The tool must write to a separate output path.

---

## 12. Interview Explanation

**Question:** *"How does your complete PII redaction pipeline work?"*

**Answer:**
> "The pipeline coordinates several steps: it extracts paragraphs and table cells, runs registered detectors to collect PII candidates, checks surrounding context keywords, resolves overlapping spans, maps accepted entities to deterministic pseudonyms, and edits the XML runs in-place before saving the document."

**Question:** *"Why did you separate orchestration from detection?"*

**Answer:**
> "Separating these steps decouples core detection logic from document formats and CLI configurations. Detectors can focus solely on scanning text strings, which makes them easier to test, update, and reuse."

**Question:** *"How do you ensure consistent pseudonymization?"*

**Answer:**
> "I instantiate the Pseudonymizer class once at the start of the pipeline run and share it across all segments. This keeps the mapping cache active throughout the run, ensuring that duplicate names receive matching pseudonyms."

**Question:** *"How do you prevent sensitive data from appearing in logs?"*

**Answer:**
> "We configure our logging handlers to only print entity types and counts (e.g. 'Redacted 5 PERSON entities') instead of writing the actual PII strings to stdout or log files."

**Question:** *"How would you add a new detector?"*

**Answer:**
> "We implement the new detector subclass using our base detector interface and register it in the detector list in pipeline.py. The orchestrator automatically runs it during execution."

---

## 13. Quick Revision

### 5 Key Concepts
1. An **orchestrator** connects separate processing stages into a single workflow.
2. A **detector registry** makes it easy to add or remove scanners.
3. The **Pseudonymizer instance** must be shared to keep replacements consistent.
4. **Logging** must only print entity types and counts to protect privacy.
5. The document should be **saved once** at the end of the run to optimize performance.

### 3 Interview Questions
1. *Why should model initialization happen outside the segment loop?*
2. *What is the difference between a unit test and an integration test in this pipeline?*
3. *Why is it insecure to write raw PII to logs?*

### 3 Practical Examples

#### Example 1: Injected Detectors
```python
# Speed up unit tests by only running specific detectors
pipeline = PIIRedactionPipeline(detectors=[EmailDetector()])
result = pipeline.run("input.docx", "output.docx")
```

#### Example 2: CLI Verbose Output
```bash
# Enable debug-level logging to inspect individual processing stages
python3 -m src.main --input doc.docx --output doc_out.docx --verbose
```

#### Example 3: Pipeline Stats Summary
```text
==================================================
PII REDACTION PIPELINE SUMMARY
==================================================
Segments Processed:  4288
Candidates Detected: 3548
Candidates Accepted: 3527
Candidates Rejected: 21
==================================================
```
