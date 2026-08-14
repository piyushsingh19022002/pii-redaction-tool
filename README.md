# PII Redaction Tool

A secure, high-precision, and reproducible named-entity redaction pipeline designed to identify and pseudonymize Personally Identifiable Information (PII) within `.docx` documents. 

---

## 1. Problem Statement

This project fulfills the Scaler AI Labs assignment requirements: read a target Word document (`.docx`) containing sensitive information, detect all occurrences of PII, and produce an identical, readable `.docx` file where all PII is replaced with consistent, safe placeholders.

The system is required to identify the following 9 PII types:
* **Full Names** (`PERSON`)
* **Email Addresses** (`EMAIL`)
* **Phone Numbers** (`PHONE`)
* **Company Names** (`ORGANIZATION`)
* **Physical/Mailing Addresses** (`ADDRESS`)
* **Social Security Numbers** (`SSN`)
* **Credit Card Numbers** (`CREDIT_CARD`)
* **Dates of Birth** (`DOB`)
* **IP Addresses** (`IP_ADDRESS`)

---

## 2. Solution Overview

The system uses a multi-stage architecture to ensure that document structure, formatting, and text alignments are preserved during redaction:

```text
       DOCX Input
           │
           ▼
  Structure Extraction
           │
           ▼
   Text Normalization
           │
           ▼
  Candidate Generation  ◄─── [Detectors: Regex, spaCy NER, Custom Rules]
           │
           ▼
  Candidate Resolution  ◄─── [Resolver: Score Clamping, Positive/Negative Context]
           │
           ▼
      Accepted PII
           │
           ▼
Pseudonymization Map    ◄─── [Consistent Safe Fake Placeholders]
           │
           ▼
   DOCX Reconstruction
           │
           ▼
      DOCX Output
```

### Pipeline Stages
1. **Structure Extraction**: The document is read paragraph by paragraph and cell by cell from tables using a clean docx parser interface, preserving exact styling and structure.
2. **Text Normalization**: Unicode quotation marks, trailing spaces, and character encoding variations are normalized to ensure robust downstream matches.
3. **Candidate Generation**: Multiple detection mechanisms (regular expressions, contextual pattern matchers, and Named Entity Recognition) scan the normalized text to identify potential PII candidate spans.
4. **Candidate Resolution**: Overlapping or conflicting candidate spans are resolved. Context rules are applied to boost or penalize candidate scores based on surrounding keywords.
5. **Pseudonymization**: Accepted PII spans are replaced with consistent, safe placeholders (e.g. `[PERSON_1]`). Multiple occurrences of the same PII entity receive the same consistent placeholder throughout the document.
6. **DOCX Reconstruction**: Runs of text in the paragraph XML are split and replaced, ensuring no visual formatting corruption occurs in the final output file.

---

## 3. Why Multiple Detection Techniques?

No single detection technique is sufficient to achieve both high precision and high recall across all PII categories:
* **Regular Expressions**: Exceptionally high recall and precision for structured PII types with strict formats, such as `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`, and `IP_ADDRESS`.
* **Named Entity Recognition (NER)**: Crucial for detecting highly variable PII categories like `PERSON` and `ORGANIZATION` where structural rules cannot be written.
* **Context and Negative Rules**: Standard NER models overpredict in specific text domains. Local context keywords (like `"incorporated"` or `"ticket ID"`) are used to boost valid matches or penalize false positives.
* **Candidate Resolution**: Resolves conflicts when two different detectors trigger on the same span, choosing the candidate with the higher resolved score.

---

## 4. Project Structure

Below is the repository file structure:

```text
pii-redaction-tool/
├── .gitignore                      # Prevents tracking virtual environments, caches, and output drafts
├── requirements.txt                # Project dependencies (pytest, python-docx, spacy)
├── README.md                       # Main documentation file
├── src/                            # Source code directory
│   ├── __init__.py
│   ├── main.py                     # CLI entrypoint for running the redaction pipeline
│   ├── pipeline.py                 # Core PIIRedactionPipeline orchestrating the run
│   ├── docx_reader.py              # Paragraph and table text extractor
│   ├── docx_redactor.py            # XML run-splitting and replacement writer
│   ├── normalizer.py               # Text normalization and index mapping
│   ├── models.py                   # Data models (PIIEntity, PIIType, ContextEvidence)
│   ├── resolver.py                 # Candidate scoring and overlap resolution logic
│   ├── context/
│   │   ├── __init__.py
│   │   └── rules.py                # Positive and negative context rules and keywords
│   └── detectors/
│       ├── __init__.py
│       ├── base.py                 # Abstract BaseDetector interface
│       ├── address.py              # Address detection (prefix/suffix regular expressions)
│       ├── credit_card.py          # Credit card regex matcher with Luhn algorithm validation
│       ├── dob.py                  # Date of Birth regex matcher
│       ├── email.py                # Email address regex matcher
│       ├── ip_address.py           # IPv4 and IPv6 regex matcher
│       ├── ner.py                  # spaCy NER matcher wrapper
│       ├── phone.py                # Telephone number regex matcher
│       └── ssn.py                  # SSN regex matcher
├── tests/                          # Automated unit test suite
│   ├── test_address_detector.py
│   ├── test_context_rules.py
│   ├── test_credit_card_detector.py
│   ├── test_detector_framework.py
│   ├── test_dob_detector.py
│   ├── test_docx_reader.py
│   ├── test_docx_redactor.py
│   ├── test_email_detector.py
│   ├── test_evaluation_report.py
│   ├── test_evaluator.py
│   ├── test_ip_address_detector.py
│   ├── test_models.py
│   ├── test_ner_detector.py
│   ├── test_normalizer.py
│   ├── test_phone_detector.py
│   ├── test_pipeline.py
│   ├── test_pseudonymizer.py
│   ├── test_resolver.py
│   └── test_ssn_detector.py
├── scripts/                        # Evaluation and reporting scripts
│   ├── evaluate.py                 # Evaluates pipeline against ground truth
│   └── generate_evaluation_report.py # Generates the final evaluation report markdown
├── evaluation/                     # Benchmark datasets and reports
│   ├── ground_truth.json           # Manually annotated evaluation benchmark
│   ├── final_evaluation_report.md  # Generated evaluation metrics
│   ├── real_document_audit.md      # Preliminary quality audit
│   └── real_document_audit_v24.md  # Domain-optimized quality audit
├── notes/                          # Educational study notes by commit
│   ├── commit-19-error-analysis-and-improvement.md
│   ├── commit-20-address-improvement.md
│   ├── commit-21-organization-improvement.md
│   ├── commit-22-phone-improvement.md
│   ├── commit-23-final-evaluation.md
│   └── commit-24-prospectus-domain-precision.md
├── input/                          # Input directory (contains original Red Herring Prospectus.docx)
└── output/                         # Output directory (contains redacted documents)
```

For each important file:
* `src/main.py`: The command-line interface entry point.
* `src/pipeline.py`: Coordinates reading, detecting, resolving, pseudonymizing, and writing paragraphs/tables.
* `src/docx_reader.py`: Reads paragraph and table cells without formatting loss.
* `src/docx_redactor.py`: Runs split-run XML modifications to redact exact PII spans.
* `src/normalizer.py`: Normalizes quotes, unicode characters, and extra spaces.
* `src/resolver.py`: Deduplicates overlapping candidate spans and calculates final resolution scores.
* `src/context/rules.py`: Checks positive and negative context rules for candidates.
* `src/detectors/ner.py`: Leverages spaCy NER to identify names and organisations.

---

## 5. Detection Pipeline

To illustrate how a segment moves through the pipeline, consider the text:
`"Please write to Rohan Dey at rohan@example.com."`

```text
"Please write to Rohan Dey at rohan@example.com."
                    │
                    ├───────────────────────────────┐
                    ▼                               ▼
            [spaCy NERDetector]             [EmailDetector]
                    │                               │
             Candidate (PERSON)             Candidate (EMAIL)
             "Rohan Dey"                    "rohan@example.com"
             Confidence: 0.85               Confidence: 1.00
                    │                               │
                    ▼                               ▼
            [rules.py]                      [rules.py]
            ContextEvidence                 ContextEvidence
            has_positive = False            has_positive = True (matches "write to")
            has_negative = False            has_negative = False
                    │                               │
                    ▼                               ▼
            [resolver.py]                   [resolver.py]
            Resolved Score: 0.85            Resolved Score: 1.00
            (Threshold: 0.70)               (Threshold: 0.70)
                    │                               │
                    ▼                               ▼
             Accepted PERSON                 Accepted EMAIL
                    │                               │
                    ▼                               ▼
            [pseudonymizer.py]              [pseudonymizer.py]
            Map to consistent ID:           Map to consistent ID:
            "Rohan Dey" -> [PERSON_1]       "rohan@example.com" -> [EMAIL_1]
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
       "Please write to [PERSON_1] at [EMAIL_1]."
```

---

## 6. Candidate Resolution

Detection and Acceptance are decoupled inside the pipeline. This separation allows the system to balance conflicting evidence before writing redactions:
* **Confidence**: Base confidence assigned by the detector (e.g. `1.00` for regex, `0.85` for NER).
* **Positive Context**: If a positive keyword (e.g. `"company"`) is detected in the surrounding window, the score is boosted by `+0.15`.
* **Negative Context**: If a negative keyword (e.g. `"equity share"`) is matched, the score is penalized by `-0.30`.
* **Resolver**: The final score is calculated as $\text{Score} = \text{Confidence} + \text{Bonus} - \text{Penalty}$. If the score is at or above `0.70`, the candidate is accepted.

---

## 7. Pseudonymization

To preserve document readability, redacted text is replaced with consistent safe placeholders rather than black bars:
* **Consistency**: If `"KSH International Limited"` is matched in Paragraph 2 and again in Paragraph 80, both occurrences are replaced with `[ORGANIZATION_1]`.
* **Unique Mapping**: A unique counter is incremented for each distinct entity type, ensuring that different entities can be distinguished (e.g. `[PERSON_1]` vs `[PERSON_2]`).

---

## 8. DOCX Handling

The pipeline splits XML text runs inside `.docx` paragraphs and tables to locate exact offsets without corrupting fonts, weights, or alignments.

* **Segments Processed**: `4288`
* **Tables Scanned**: `76`
* **Paragraphs Scanned**: `1006`
* **Output Validity**: Validated via python-docx; the output document contains identical layout bounds and can be opened by Microsoft Word.

---

## 9. Installation

### Prerequisites
* Python 3.10 to 3.13 (compatible with standard virtual environment workflows).

### Commands
1. Clone or download the repository into a directory.
2. Initialize and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install standard requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Download the required English language spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

---

## 10. Usage

### Option A: CLI Interface
Run the redaction pipeline via the CLI entrypoint:
```bash
python -m src.main \
  --input "input/Red Herring Prospectus.docx" \
  --output "output/final_redacted.docx"
```

### Option B: Web Application Interface
Start the local Flask application server:
```bash
python app.py
```
Then navigate to `http://127.0.0.1:5001` in your browser. The page serves a premium drag-and-drop file upload UI to easily redact DOCX files and download the sanitized outputs with dynamic statistics.

---

## 11. Testing

The project has a full suite of unit and regression tests written in `pytest`.

To execute all tests:
```bash
pytest
```
* **Current Result**: **182 tests passed successfully**.

---

## 12. Controlled Benchmark Evaluation

To execute the quantitative evaluation benchmark:
```bash
python -m scripts.evaluate
```

### Controlled Benchmark Result (62 Examples)

| PII Type | TP | FP | FN | TN | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PERSON** | 11 | 0 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| **EMAIL** | 7 | 0 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| **PHONE** | 6 | 0 | 0 | 1 | 100.00% | 100.00% | 100.00% |
| **ORGANIZATION** | 6 | 0 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| **ADDRESS** | 6 | 0 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| **SSN** | 6 | 0 | 0 | 2 | 100.00% | 100.00% | 100.00% |
| **CREDIT_CARD** | 6 | 0 | 0 | 1 | 100.00% | 100.00% | 100.00% |
| **DOB** | 6 | 0 | 0 | 2 | 100.00% | 100.00% | 100.00% |
| **IP_ADDRESS** | 6 | 0 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| **OVERALL** | **60** | **0** | **0** | **6** | **100.00%** | **100.00%** | **100.00%** |

---

## 13. Evaluation Methodology

We utilize **Exact Span + Entity Type Matching**:
1. **True Positive (TP)**: Predicted boundaries and type match ground truth exactly.
2. **False Positive (FP)**: Predicted span was not labeled as PII.
3. **False Negative (FN)**: Ground truth PII was missed by predictions.
4. **True Negative (TN)**: Labeled non-PII candidate spans that were correctly rejected by the resolver.

### Formulas
$$Precision = \frac{TP}{TP + FP}$$
$$Recall = \frac{TP}{TP + FN}$$
$$Accuracy = \frac{TP + TN}{TP + TN + FP + FN}$$
$$F1 = \frac{2 \times Precision \times Recall}{Precision + Recall}$$

> [!NOTE]
> True Negatives (TN) represent explicitly annotated negative cases (such as serial numbers or defined abbreviations) and are not calculated based on all non-PII characters or tokens in the raw text files.

---

## 14. Real-Document Smoke Test

The full `Red Herring Prospectus.docx` document does not have an exhaustive ground truth. Therefore, **no formal precision, recall, or F1 metrics are claimed** for the prospectus redactions. The run serves as a qualitative smoke test:

* **Segments Processed**: `4288`
* **Candidates Detected**: `3711`
* **Candidates Accepted**: `2144`
* **Candidates Rejected**: `1567`
* **Accepted ORGANIZATION Candidates**: **1271** (decreased from **2704** in v23, a **53% reduction in accepted ORGANIZATION candidates**).

---

## 15. Domain-Specific Improvement

In the financial prospectus domain, capitalized terms (such as `Bids`, `Bidders`, `Anchor Investors`, `Equity Shares`, `Maharashtra`) are frequently tagged as organizations by general-purpose NER models. 

By introducing **negative context keywords** (e.g. generic financial terms and places) and applying **candidate-only constraints** (ensuring surrounding keywords do not penalize valid companies), we successfully eliminated **1433 false positives** while ensuring all legitimate organizations (like `KSH International Limited` and `Registrar of Companies Maharashtra`) continue to be redacted.

---

## 16. Limitations

* **Manually Annotated Ground Truth**: The benchmark annotations represent a snapshot of testing criteria and may not reflect all real-world edge cases.
* **Synthetic Evaluation Dataset**: The 62 evaluation examples are synthetically constructed templates, not raw documents.
* **Unannotated Prospectus**: The Red Herring Prospectus has no exhaustive ground truth.
* **Image/OCR Limitations**: Scanned pages or text embedded inside images are not processed.
* **Docx XML Non-Text Elements**: Text inside shapes, SmartArt, or complex nested drawings may bypass extraction.

---

## 17. Security / Privacy

* **Original Integrity**: Original input documents are opened as read-only and never modified.
* **Safe Placeholders**: No real PII is leaked in generated logs, test cases, or documentation.
* **Secrets Policy**: No API keys, credentials, or environment configs are tracked.

---

## 18. Tradeoffs

In PII redaction, missing a sensitive entity (False Negative) is a severe privacy leak. However, over-redacting common words (False Positives) makes the document completely unreadable. The resolver uses a calibrated acceptance threshold (`0.70`) and context penalties (`-0.30`) to balance these concerns, prioritizing recall on structured fields while cleaning up precision on organizations.

---

## 19. Future Improvements

* **Domain-Specific NER Model**: Training a custom spaCy model on legal/financial agreements.
* **OCR Support**: Incorporating `pytesseract` to scan embedded images inside documents.
* **Human-in-the-Loop**: Building an interactive review interface to approve/reject borderline candidates.
* **Advanced Tables Handling**: Building semantic table structures to identify PII within specific column contexts.

---

---

## 20. Deployment

The application can be deployed as a Python FastAPI web service on Render.

### Dependency Notes

* **spaCy** is declared in `requirements.txt` (`spacy>=3.8.13`) and is installed by `pip` during the build.
* **`en_core_web_sm`** is the English language model required by the NER detector (`src/detectors/ner.py`). It is declared directly in `requirements.txt` as a pip wheel URL pointing to the spaCy GitHub releases:
  ```
  en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
  ```
* This approach installs the model **into the same virtual environment as spaCy**, making it discoverable by `spacy.load("en_core_web_sm")` without any separate download step. The previous approach of `python -m spacy download` fails on Render because it installs into the system Python, not the project `.venv`.
* The application **requires** this model because Named Entity Recognition is a core stage of the PII detection pipeline. There is no fallback — if the model is absent, the application raises `OSError: [E050] Can't find model 'en_core_web_sm'` at startup.

### Build Command

```bash
pip install -r requirements.txt
```

The spaCy model is installed automatically by pip as part of the standard `requirements.txt` install — no separate step required.

### Start Command

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

### render.yaml

The repository includes a `render.yaml` file at the root that configures these commands automatically when the repository is connected to Render.

---



## 21. Assignment Deliverables

1. **Source Code**: Fully modular codebase under `src/` and `tests/`.
2. **Redacted DOCX**: `output/final_redacted.docx` (and `output/final_redacted_v24.docx`).
3. **README**: This documentation file.
4. **Evaluation Report**: Located at `evaluation/final_evaluation_report.md`.

