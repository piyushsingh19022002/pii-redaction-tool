# PII Redaction Pipeline: Real-Document Smoke-Test Quality Audit (v24)

This report presents a comparative quality audit of the redactions applied to the `input/Red Herring Prospectus.docx` file between the baseline run (v23) and the domain-optimized run (v24).

---

## 1. Document & Pipeline Summary Statistics Comparison

The table below contrasts the pipeline execution statistics before and after the domain-aware organization precision improvements:

| Metric | Before (v23 Run) | After (v24 Run) | Change |
| :--- | :---: | :---: | :---: |
| **Segments Processed** | 4288 | 4288 | 0 |
| **Candidates Detected** | 3711 | 3711 | 0 |
| **Candidates Accepted** | 3577 | 2144 | **-1433 (-40.1%)** |
| **Candidates Rejected** | 134 | 1567 | **+1433** |
| **ORGANIZATION Redacted** | **2704** | **1271** | **-1433 (-53.0%)** |
| **PERSON Redacted** | 752 | 752 | 0 |
| **EMAIL Redacted** | 70 | 70 | 0 |
| **PHONE Redacted** | 48 | 48 | 0 |
| **ADDRESS Redacted** | 3 | 3 | 0 |

The accepted ORGANIZATION count dropped by **1433**, resulting in a **53% reduction in accepted ORGANIZATION candidates** while preserving all other PII categories exactly.

---

## 2. Distinction: Benchmark vs. Real Document

> [!IMPORTANT]
> * **Controlled Benchmark**: Evaluated using 62 manually annotated synthetic examples, achieving a verified **100.00% Precision, Recall, and F1-Score**.
> * **Real Document (Prospectus)**: Conducted as a **smoke test only**. No exhaustive ground truth annotations exist for this document; therefore, **no precision/recall/F1 claims are made** for the prospectus redactions.

---

## 3. Representative ORGANIZATION Detections (v24 Audit)

We performed a qualitative audit of 20 representative ORGANIZATION detections in the v24 output, classifying their validity:

1. `BSE` → **VALID ORGANIZATION** (Bombay Stock Exchange).
2. `KSH INTERNATIONAL LIMITED` → **VALID ORGANIZATION** (Issuer company).
3. `BSE Limited` → **VALID ORGANIZATION** (Stock exchange corporate name).
4. `ICICI Securities Limited` → **VALID ORGANIZATION** (Book running lead manager).
5. `HDFC Bank Limited` → **VALID ORGANIZATION** (Book running lead manager).
6. `DHAULAGIRI FAMILY TRUST` → **VALID ORGANIZATION** (Shareholding entity).
7. `MAKALU FAMILY TRUST` → **VALID ORGANIZATION** (Shareholding entity).
8. `BROAD FAMILY TRUST` → **VALID ORGANIZATION** (Shareholding entity).
9. `ANNAPURNA FAMILY TRUST` → **VALID ORGANIZATION** (Shareholding entity).
10. `KANCHENJUNGA FAMILY TRUST` → **VALID ORGANIZATION** (Shareholding entity).
11. `Kirtane & Pandit LLP` → **VALID ORGANIZATION** (Issuer's legal/accounting auditor).
12. `Company` → **POSSIBLE FALSE POSITIVE** (Capitalized defined noun for the issuer; common noun rather than a sensitive organization entity).
13. `ISSUER` → **CLEAR FALSE POSITIVE** (Defined legal role placeholder).
14. `Syndicate` → **POSSIBLE FALSE POSITIVE** (Defined role placeholder).
15. `Offer` → **CLEAR FALSE POSITIVE** (Transaction description).
16. `the CARE Report` → **POSSIBLE FALSE POSITIVE** (Industry report name).
17. `Rakhi Girija Shetty` → **CLEAR FALSE POSITIVE** (Legitimate person name misclassified by spaCy as ORG).
18. `Life Insurance Companies and Pension Funds` → **CLEAR FALSE POSITIVE** (Generic investor class description).
19. `Allotment` → **CLEAR FALSE POSITIVE** (Generic financial term).
20. `Supa Facility` → **CLEAR FALSE POSITIVE / GPE** (Manufacturing site location).

### Audit Proportional Assessment
* **Before (v23)**: Approximately **85%** of checked organization detections were obvious false positives (common nouns, state names, headings).
* **After (v24)**: In the qualitative sample, the majority of reviewed organization detections were legitimate organizations or trusts.

---

## 4. Inspection of Previous False-Positive Categories

We audited the output file to determine if the 17 major false-positive categories from the previous v23 run are still being redacted:

* `Bids` → **RESOLVED** (Successfully suppressed; count is 0).
* `Bidders` → **RESOLVED** (Successfully suppressed; count is 0).
* `Anchor Investors` → **RESOLVED** (Successfully suppressed; count is 0).
* `Bid/Offer Closing Day` → **RESOLVED** (Successfully suppressed; count is 0).
* `Maharashtra` → **RESOLVED** (Successfully suppressed; count is 0).
* `Pune` → **RESOLVED** (Successfully suppressed; count is 0).
* `Village Birdewadi` → **RESOLVED** (Successfully suppressed; count is 0).
* `RED HERRING PROSPECTUS` → **RESOLVED** (Successfully suppressed; count is 0).
* `DEFINITIONS` → **RESOLVED** (Successfully suppressed; count is 0).
* `CURRENCY` → **RESOLVED** (Successfully suppressed; count is 0).
* `OFFER` → **RESOLVED** (Successfully suppressed; count is 0).
* `RISKS` → **RESOLVED** (Successfully suppressed; count is 0).
* `ASBA` → **RESOLVED** (Successfully suppressed; count is 0).
* `Promoter Group` → **RESOLVED** (Successfully suppressed; count is 0).
* `Key Managerial Personnel` → **RESOLVED** (Successfully suppressed; count is 0).
* `Designated Intermediaries` → **RESOLVED** (Successfully suppressed; count is 0).
* `Equity Share` → **RESOLVED** (Successfully suppressed; count is 0).

---

## 5. Verification of Legitimate Organization Detection

We verified that the baseline legitimate organizations are still successfully captured and redacted by the pipeline:

* `KSH International Limited` → **DETECTED & REDACTED**
* `Bhandary Metal Extrusion Private Limited` → **DETECTED & REDACTED**
* `Georgia Transformer Corporation` → **DETECTED & REDACTED**
* `Ahlstrom Sweden AB` → **DETECTED & REDACTED**
* `Cindus Corporation` → **DETECTED & REDACTED**
* `Elantas Beck India Limited` → **DETECTED & REDACTED**
* `Registrar of Companies Maharashtra` → **DETECTED & REDACTED** (Successfully matched despite containing the geographic term `Maharashtra`).

---

## 6. Output File Readability & Structural Validation

* **Paragraph Count Preservation**: Both original and redacted files contain exactly `1006` paragraphs.
* **Table Count Preservation**: Both original and redacted files contain exactly `76` tables.
* **Original File Integrity**: Verified that `input/Red Herring Prospectus.docx` remains completely unmodified.
* **Layout Integrity**: The output file `output/final_redacted_v24.docx` opens without error and preserves the prospectus formatting.
