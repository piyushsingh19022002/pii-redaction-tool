# Commit 24: Prospectus Domain Precision Improvements

This guide details the error analysis, logic adjustments, and verification for **Commit 24** (`feat: improve organization precision for prospectus domain`).

---

## 1. Why 100% Benchmark Metrics Were Not Enough

While the pipeline achieved `100.00%` on our controlled evaluation benchmark, the benchmark dataset consists of short, clean, synthetically constructed templates. A real-world document like a Red Herring Prospectus is much longer (`4288` segments) and contains complex legal, financial, and formatting structures that are not fully captured by short templates. 

The controlled benchmark had only 6 examples of `ORGANIZATION`, which all had explicit corporate suffix indicators (e.g. `LLC`, `Ltd.`, `Corporation`, `Inc.`). Because the benchmark did not contain any capitalized defined terms, generic roles, or geographical state names in raw prose, it could not expose the systematic over-redaction (False Positive) tendencies of the underlying spaCy NER model when applied to the legal/financial domain.

---

## 2. What the Real-Document Smoke Test Revealed

On the first prospectus smoke test, the pipeline redacted **2704** items as `ORGANIZATION`, representing **75.6%** of all accepted entities. An audit of these matches revealed that the vast majority were false positives:
* **Legal/Financial Defined Terms**: `Bids`, `Bidders`, `Anchor Investors`, `Promoter Group`, `Key Managerial Personnel`.
* **Geographical Entities**: `Maharashtra`, `Pune`, `Village Birdewadi`.
* **Section Headings / Titles**: `RED HERRING PROSPECTUS`, `DEFINITIONS`, `OFFER`, `RISKS`, `CURRENCY`.
* **Financial Acronyms**: `ASBA`.
* **Generic Nouns/Instruments**: `Equity Share`, `the Board and Shareholders`.

---

## 3. Why NER Over-Predicts Organizations in Legal/Financial Documents

General-purpose Named Entity Recognition (NER) models (like spaCy's `en_core_web_sm`) are trained on news text, articles, and general internet corpuses. In news text, capitalized words (like `"Tata"` or `"Google"`) represent organizations. 

However, in legal and financial documents, capitalization is heavily used for **defined terms** (like `"Equity Shares"`, `"Bidders"`, `"Offer Price"`). Since they are capitalized, the pre-trained spaCy model incorrectly classifies these capitalized noun phrases as proper organizations (`ORG`), leading to severe over-redaction.

---

## 4. General-Purpose NER vs. Domain-Specific Context

* **General-purpose NER**: Classifies capitalized entities based on syntactic patterns and linguistic structures found in general news text.
* **Domain-specific context**: Uses specialized rules to evaluate the candidate in its local business/legal context (e.g. looking for indicators like `"Limited"`, or checking if the name matches a blacklist of financial instruments).

---

## 5. How Positive and Negative Context Work

1. **Positive Context**: Searches for words like `"company"`, `"corporation"`, or `"incorporated"` surrounding a candidate to confirm it is an organization (adding a `+0.15` bonus).
2. **Negative Context**: Searches for words like `"equity share"`, `"bids"`, or `"maharashtra"` inside a candidate. If matched, the candidate receives a `-0.30` penalty, bringing its score below the threshold of `0.70` and rejecting it.

---

## 6. How Geographic Entities Differ from Organizations

Geographic names (like `"Maharashtra"` or `"Pune"`) represent locations (GPE/LOC), not corporate entities. However, geographic names often appear inside organization names (e.g. `"Registrar of Companies Maharashtra"` or `"Ahlstrom Sweden AB"`). 

To handle this, the pipeline penalizes generic geographic terms (like `"Maharashtra"`) unless the candidate also contains a strong organizational suffix (like `"Limited"`, `"Ltd"`, `"AB"`) or starts with `"Registrar of"`.

---

## 7. How Defined Terms Create False Positives

Defined terms (such as `Bidders` or `Promoter Group`) are capitalized in prospectuses. Because of this, spaCy identifies them as proper nouns and labels them `ORG`. By treating these defined roles as negative keywords, the pipeline can filter them out while retaining actual companies.

---

## 8. How the Resolver Combines Evidence

The candidate resolver ([src/resolver.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/src/resolver.py)) calculates a final score:
$$\text{Score} = \text{Detector Confidence} + \text{Context Bonus} - \text{Context Penalty}$$
If $\text{Score} \ge 0.70$, the candidate is accepted. For example:
* A generic term with confidence `0.85` matches negative context: $\text{Score} = 0.85 - 0.30 = 0.55 < 0.70$ (Rejected).
* A valid company matches positive context: $\text{Score} = 0.85 + 0.15 = 1.00 \ge 0.70$ (Accepted).

---

## 9. Implementation Flow

```text
DOCX (input/Red Herring Prospectus.docx)
  ↓ [src/docx_reader.py]
Segments (paragraphs and table cells text)
  ↓ [src/detectors/ner.py]
NER / Regex Candidates (confidence = 0.85/0.90)
  ↓ [src/context/rules.py]
Context Evidence (evaluate_context)
  ↓
Positive + Negative Evidence (evaluate candidate-only for negative org keywords)
  ↓ [src/resolver.py]
Resolver (calculate_score and clamp to [0.0, 1.0])
  ↓
Accept / Reject (threshold = 0.70)
  ↓ [src/docx_redactor.py]
Redaction (redact_docx)
  ↓
Real-document Audit (output/final_redacted_v24.docx)
```

---

## 10. Quantitative vs. Qualitative Testing

* **Controlled Quantitative Evaluation**: Uses the 62 manually annotated templates. Calculates formal Precision, Recall, and F1 metrics.
* **Real-Document Qualitative Smoke Test**: Pipeline run against the full 4288-segment prospectus. Formally verifies the pipeline does not crash, layout is preserved, and redaction proportions are reasonable. No formal precision/recall is claimed because the prospectus has no exhaustive ground truth.

### Organization Redaction Statistics

* **BEFORE (Commit 23)**: Organization accepted = **2704**
* **AFTER (Commit 24)**: Organization accepted = **1271** (**-1433 / -53.0%**)

---

## 11. Interview Questions

### "Why did the benchmark show 100% while the real document had over-redaction?"
"The benchmark contains short, synthetic templates that did not represent the domain-specific capitalization rules of legal documents (like defined terms and headings). This masked spaCy's over-redaction tendencies."

### "How did you handle domain shift?"
"We registered legal, financial, and geographical terms (like `Bidders`, `Equity Shares`, and `Maharashtra`) as negative context keywords for the ORGANIZATION type, penalizing generic matches while preserving valid companies."

### "Why didn't you simply disable NER?"
"Disabling NER would destroy our recall for valid organizations that do not end in standard suffix abbreviations (e.g. `Google` in some contexts). Instead, we used negative context to prune the NER predictions."

### "How did negative context improve precision?"
"It penalizes candidates matching generic terms by `-0.30`, dropping their final resolution score to `0.55`, which falls below the resolver's acceptance threshold of `0.70`."

### "How did you protect recall while improving precision?"
"We exempted candidates containing strong corporate indicators (like `Ltd.`, `AB`, `LLC`) from the negative context rules. This ensures names like `Ahlstrom Sweden AB` remain redacted even if they contain geographic terms."

---

## 12. Quick Revision

### 5 Key Concepts
1. **Domain Shift**: Performance degradation when models are applied to new document types.
2. **Defined Terms**: Capitalized common nouns in legal contexts that confuse general-purpose NER models.
3. **Candidate-Only Negative Checking**: Limiting negative context checks to the candidate text itself.
4. **Strong Indicator Exemption**: Bypassing negative context if the name contains corporate suffixes.
5. **Score Clamping**: Restricting the resolver score range to $[0.0, 1.0]$.

### 3 Interview Questions
1. *Why is accuracy a poor metric for evaluating PII redaction pipelines?*
2. *How does candidate-only negative checking prevent penalizing valid companies when nearby words match negative terms?*
3. *What is the role of word boundaries in compiling negative context patterns?*

### 3 Practical Examples
1. **Defined Term Filter**: Reject `"Bidders"` but accept `"Bhandary Metal Extrusion Private Limited"`.
2. **Geographical Exemption**: Reject `"Maharashtra"` but accept `"Registrar of Companies Maharashtra"`.
3. **Acronym Filter**: Reject `"ASBA"` but accept `"KSH International Limited"`.
