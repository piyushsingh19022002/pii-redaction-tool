# Commit 25: Final Project Submission & Documentation

This study guide details the final submission packaging, verification results, development journey, educational learnings, and technical interview questions for the **PII Redaction Tool** project.

---

## 1. What Makes the Project Submission-Ready

A project is ready for submission when it meets three criteria:
1. **Core Verification**: 100% of automated unit and regression tests pass (`182 passed`).
2. **Quantitative Benchmarking**: Evaluated metrics on a controlled test dataset are perfect (`100% F1-score` across all required PII types).
3. **Qualitative Domain Validation**: Tested end-to-end on a complex real-world document without crashing, structural corruption, or excessive over-redaction.

---

## 2. Final Architecture Diagram

The system operates as a modular, decoupled pipeline:

```text
DOCX
  ↓
Extraction
  ↓
Normalization
  ↓
Candidate Generation
 ├── Regex
 ├── NER
 └── Context
  ↓
Candidate Resolver
 ├── Validation
 ├── Negative Rules
 └── Confidence
  ↓
Pseudonymization
  ↓
DOCX Reconstruction
  ↓
Evaluation / Audit
```

### Architecture Component Description
* **Extraction**: Reads raw text from DOCX paragraph and table XML components using `docx_reader.py`.
* **Normalization**: Normalizes whitespaces, curly quotes, and encoding variants via `normalizer.py`.
* **Candidate Generation**: Standardized detectors scan text to create list of candidates with base confidence values.
* **Candidate Resolver**: Scores and dedupes overlapping spans using confidence levels plus positive/negative context scoring modifications.
* **Pseudonymization**: Safely replaces accepted PII spans with consistent placeholders (e.g., `[PERSON_1]`).
* **DOCX Reconstruction**: Reconstructs the Word document using split-run replacement algorithms in `docx_redactor.py`.
* **Evaluation / Audit**: Evaluates predictions against annotated benchmark ground-truth and outputs HTML/Markdown reports.

---

## 3. Repository Structure

```text
pii-redaction-tool/
├── requirements.txt                # Pip package requirements (spacy, python-docx, pytest)
├── README.md                       # Main landing documentation
├── src/                            # Code files
│   ├── main.py                     # CLI wrapper
│   ├── pipeline.py                 # Core workflow pipeline
│   ├── docx_reader.py              # Word document text parser
│   ├── docx_redactor.py            # Word document XML run-splitter and redactor
│   ├── normalizer.py               # Text normalization and mapping
│   ├── models.py                   # Class objects (PIIEntity, ResolutionDecision)
│   ├── resolver.py                 # Deduplication and resolution logic
│   ├── context/
│   │   └── rules.py                # Context evidence matching rules
│   └── detectors/
│       ├── base.py                 # Detector interface base
│       ├── address.py              # ADDRESS regular expression detector
│       ├── credit_card.py          # CREDIT_CARD regex with Luhn checksum validation
│       ├── dob.py                  # DOB regex detector
│       ├── email.py                # EMAIL regex detector
│       ├── ip_address.py           # IP_ADDRESS regex detector
│       ├── ner.py                  # PERSON/ORGANIZATION spaCy NER detector
│       ├── phone.py                # PHONE regex detector
│       └── ssn.py                  # SSN regex detector
├── tests/                          # 182 unit/regression test cases
├── scripts/                        # Evaluation run scripts
│   ├── evaluate.py
│   └── generate_evaluation_report.py
├── evaluation/                     # Metric data and audit reports
│   ├── ground_truth.json
│   ├── final_evaluation_report.md
│   ├── real_document_audit.md
│   └── real_document_audit_v24.md
└── notes/                          # Commit guides
```

---

## 4. How to Install
1. Initialize a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install library dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Fetch the spaCy English model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

---

## 5. How to Run
Run the CLI application by specifying the input path and output destination:
```bash
python -m src.main \
  --input "input/Red Herring Prospectus.docx" \
  --output "output/final_redacted.docx"
```

---

## 6. How to Test
Verify all unit and integration test fixtures:
```bash
pytest
```
*Current result*: **182 passed**.

---

## 7. How Evaluation Works
The evaluator programmatically runs candidate detection on labeled examples in `evaluation/ground_truth.json` and evaluates prediction spans using **Exact Span + Entity Type Matching** (exact boundary matching).
* **TP (True Positive)**: Exact span boundary and PII entity type match ground truth.
* **FP (False Positive)**: Pipeline predicted a PII span not labeled in ground truth.
* **FN (False Negative)**: Pipeline missed a PII span labeled in ground truth.
* **TN (True Negative)**: Pipeline correctly rejected non-PII candidate entities explicitly annotated as test controls in ground truth.

---

## 8. Final Benchmark Results (Controlled Evaluation)

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

## 9. Real-Document Smoke Test
* **Processed Segments**: `4288`
* **Candidates Detected**: `3711`
* **Candidates Accepted**: `2144`
* **Candidates Rejected**: `1567`
* **Organization Redacted (v23)**: `2704`
* **Organization Redacted (v24)**: `1271` (represented a **53% reduction in accepted ORGANIZATION candidates** due to domain-aware context filters).
* *Note*: The prospectus smoke-test is a qualitative validation; no formal precision/recall metrics are claimed because it lacks exhaustive ground truth.

---

## 10. Limitations
* **Synthetic Evaluation**: Controlled benchmark uses synthetically constructed templates.
* **No Prospectus Ground Truth**: No complete list of PII exists for the target prospectus document.
* **Image/Drawing Blocks**: Scanned screenshots or drawings inside Word XML cannot be parsed.

---

## 11. Tradeoffs
PII redaction represents a classic tradeoff between **recall** (avoiding privacy leaks) and **precision** (maintaining document readability). Missing a phone number or SSN is a security violation, but over-redacting common words makes the text unreadable. Decoder confidence levels, context rules, and resolver thresholds are calibrated to prioritize recall for highly sensitive fields while cleaning up precision on organizations.

---

## 12. Development Journey

```text
Baseline (Commit 18)
  ↓
Address improvement (Commit 20)
  ↓
Organization improvement (Commit 21)
  ↓
Phone improvement (Commit 22)
  ↓
Final benchmark (Commit 23)
  ↓
Real-document audit (Commit 23 Audit)
  ↓
Domain-aware organization improvement (Commit 24)
  ↓
Final submission (Commit 25)
```

---

## 13. What I Learned

* **Regex-based detection**: Highly effective for structured fields, but requires strict validation (like Luhn checksums for credit cards) to prevent matching arbitrary numbers.
* **NER (Named Entity Recognition)**: Flexible for dynamic entities (like names), but highly susceptible to domain shift (e.g. tagging capitalized defined terms as organizations).
* **Context-aware detection**: Crucial for disambiguating entities (e.g. recognizing that a number near `"Ticket ID"` is not a phone number).
* **False Positives / Precision**: Detections that are incorrect, reducing document usability. Suppressed using negative context keywords.
* **False Negatives / Recall**: Missing valid PII, which constitutes a security leak. Improved by optimizing boundary alignments and model parameters.
* **Exact Span Matching**: Demanding evaluation scheme where off-by-one errors count as failures, forcing clean span normalization.
* **DOCX Processing**: Manipulating Word documents requires navigating complex XML runs without disrupting structural mappings or fonts.
* **Evaluation-driven Development (EDD)**: Developing in iterative cycles by writing tests and evaluations before implementing code fixes.
* **Domain Shift**: Degradation of model performance (like spaCy NER) when moving from general news corpuses to specialized legal documents.

---

## 14. Interview Questions

### 1. Why did you combine regex and NER?
"Regex provides high recall and precision for structured patterns like emails or credit cards. NER is necessary for dynamic, unstructured text like names or organizations. Combining them gives us the best of both worlds."

### 2. Why is recall important in PII detection?
"Recall measures missed PII. In a privacy pipeline, a single false negative means leaking sensitive data like an SSN or phone number, which violates compliance regulations."

### 3. What was your biggest false-positive problem?
"Over-redacting common nouns, headings, and locations (like `Bidders`, `Bids`, `Maharashtra`) as organizations because they were capitalized in the legal prospectus."

### 4. How did you solve organization over-redaction?
"We registered these common nouns and locations as negative context keywords for organizations, restricted negative validation to the candidate text itself, and bypassed the penalties if the entity contained strong corporate suffixes like `Limited`."

### 5. How did you evaluate the system?
"We ran quantitative evaluations on a 62-example manually annotated dataset with exact span and type matching, and qualitative smoke tests on the prospectus to verify pipeline stability and formatting."

### 6. Why don't you claim 100% real-world accuracy?
"Our 100% score is on the controlled benchmark. Real-world documents are highly variable, and since the prospectus does not have exhaustive ground truth annotations, claiming formal precision/recall is mathematically impossible."

### 7. How does the resolver work?
"It gathers candidate spans, matches context, computes a score ($\text{Score} = \text{Confidence} + \text{Bonus} - \text{Penalty}$), and deduplicates overlapping boundaries by choosing the candidate with the highest resolved score."

### 8. How did you preserve DOCX structure?
"We used `python-docx` to read elements as paragraphs and table cells, and manipulated raw text runs at the XML level rather than editing raw file binaries."

### 9. What would you improve with more time?
"I would train a domain-specific legal NER model, add OCR support to detect text inside screenshots, and implement a web-based human-in-the-loop review interface for borderline candidates."

---

## 15. Quick Revision

### 5 Key Terms
1. **Luhn Algorithm**: Modulo 10 formula used to validate primary account numbers.
2. **Micro F1-Score**: Micro-averaged F1 metric aggregating TPs, FPs, and FNs across all classes.
3. **Exact Matching**: Enforcing identical span start, end, and class type boundaries.
4. **Defined Terms**: Capitalized words in legal files representing roles.
5. **Run-Splitting**: Decomposing docx text blocks into XML nodes to apply replacements.

### 3 Critical Takeaways
1. A 100% score on a controlled benchmark does not guarantee general perfection.
2.Decoupled architecture makes it easy to calibrate rules without breaking parser layers.
3. Deciding between recall and precision depends on compliance and privacy risk bounds.
