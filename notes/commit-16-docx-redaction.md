# Commit 16 Learning Notes: DOCX Redaction and Reconstruction

This document details the design patterns, document parsing structures, and verification of Commit 16 (`feat: add docx redaction and reconstruction`).

---

## 1. Commit Overview

### Why DOCX Redaction is Different from Plain-Text Replacement
A Word Document (DOCX) is not a plain-text file. It is a zipped package of XML files. Replacing text directly in the XML string ruins formatting, corrupts style definitions, and can break document structure. Redaction must happen at the element object level (such as paragraphs, tables, and runs) to keep the file valid.

### DOCX Paragraphs
The basic text block containing characters, styles, and alignments. It is represented by `docx.text.paragraph.Paragraph` in python-docx.

### DOCX Runs
A paragraph is divided into one or more runs (`docx.text.run.Run`). A run is a contiguous span of text sharing the same formatting (e.g. bold, italic, font style). A single word or string can be split across multiple runs.

### DOCX Tables
A collection of rows and columns. Cells inside tables contain paragraphs, which in turn contain runs.

### Why Preserving Structure Matters
Corporate prospectuses contain complex tables, alignments, headers, and footers. If a redaction tool strips this styling, the document becomes unreadable. We must edit text in-place inside the existing runs to preserve the layout.

---

## 2. Files Involved

### File Responsibility Table

| File | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **`src/docx_reader.py`** | Traverses DOCX elements to extract paragraphs and cells. | Original DOCX file | List of `TextSegment` objects |
| **`src/models.py`** | Defines `TextSegment` and `PIIEntity` models. | (None for this commit) | Data schema definitions |
| **`src/docx_redactor.py`** | Maps offsets and performs run-level updates. | Original file, output path, and replacements | Redacted DOCX file |
| **`tests/test_docx_redactor.py`** | Asserts correct paragraph/cell replacements and splits. | Dummy DOCX files | Test pass/fail results |

### Consumer Pipeline Flow
The **Candidate Resolver** (Commit 14) resolves overlapping candidate entities. The **Pseudonymizer** (Commit 15) generates synthetic pseudonyms for each accepted entity. Finally, `redact_docx` receives these accepted entities, maps their offsets, and updates the runs.

---

## 3. Required Commit-Specific Flow Diagram

Here is the data flow for DOCX redaction:

```text
Original DOCX
     │
     ▼
python-docx Document
     │
     ├── Paragraphs (doc.paragraphs)
     │      ↓
     │    Runs (paragraph.runs)
     │
     └── Tables (doc.tables)
            ↓
          Cells (row.cells)
            ↓
        Paragraphs (cell.paragraphs)
            ↓
          Runs (paragraph.runs)
     │
     ▼
Combined Text ───────────(raw_text = "".join(run.text))
     │
     ▼
Accepted PII Spans ──────(mapped using find_raw_offsets())
     │
     ▼
Right-to-Left Replacement(mapped_replacements.sort(reverse=True))
     │
     ▼
Updated Runs ────────────(redact_paragraph() updates runs)
     │
     ▼
Output DOCX ─────────────(doc.save(output_path))
```

Also showing the module dependencies:

```text
src/docx_reader.py (TextSegment indices)
      │
      ▼
src/docx_redactor.py
      │
      ▼ (Tests paragraph/cell replacements & run-splitting)
tests/test_docx_redactor.py
```

---

## 4. Step-by-Step Example (Cross-Run Case Split Check)

Suppose a paragraph has its text split across three runs:

* **Run 1**: `"Contact john@"` (formatting: normal)
* **Run 2**: `"example"` (formatting: bold)
* **Run 3**: `".com today."` (formatting: normal)

The visible text is `"Contact john@example.com today."`.
The detector finds `"john@example.com"` (start=8, end=24) which is replaced with `"john.doe@example.com"`.

### Redaction Execution Steps

```text
1. Combined text range:
   - Run 1: [0, 13)
   - Run 2: [13, 20)
   - Run 3: [20, 31)

2. Determine affected runs for PII span [8, 24):
   - Run 1 overlaps [8, 24) (run_start 0 < 24 and 8 < run_end 13 -> True)
   - Run 2 overlaps [8, 24) (run_start 13 < 24 and 8 < run_end 20 -> True)
   - Run 3 overlaps [8, 24) (run_start 20 < 24 and 8 < run_end 31 -> True)
   - Affected runs = [Run 1, Run 2, Run 3]

3. Apply replacement to the first affected run (Run 1):
   - rel_start = max(0, 8 - 0) = 8
   - rel_end = max(0, 24 - 0) = 24 -> clamped to 13
   - Run 1 text becomes: run_text[:8] + "john.doe@example.com" + run_text[13:]
   - Run 1.text = "Contact john.doe@example.com"

4. Remove PII text from subsequent runs (Run 2 and Run 3):
   - Run 2: rel_start = 0, rel_end = 7. Text becomes: run_text[:0] + "" + run_text[7:] = ""
   - Run 3: rel_start = 0, rel_end = 4. Text becomes: run_text[:0] + "" + run_text[4:] = " today."

5. Final reconstructed visible text:
   - Run 1.text + Run 2.text + Run 3.text
   - = "Contact john.doe@example.com" + "" + " today."
   - = "Contact john.doe@example.com today."
```

---

## 5. Why Right-to-Left

Replacing text changes the string length. If we process replacements from left-to-right, modifying an earlier span will shift all subsequent character indices, invalidating their offsets.

### Left-to-Right Problem
* Text: `"John Doe email john@example.com"`
* Replace `"John Doe"` with `"Jane Smith"` (length changes from 8 to 10).
* The offset for `"john@example.com"` shifts by `+2` characters, causing subsequent replacements to target the wrong index.

### Right-to-Left Solution
* Text: `"John Doe email john@example.com"`
* Replace `"john@example.com"` (at offset 15) first.
* This changes the text on the right, but leaves the indices of `"John Doe"` (at offset 0) completely untouched and valid.

---

## 6. Table Handling

Tables in DOCX contain a nested structure:

$$\text{document.tables} \rightarrow \text{rows} \rightarrow \text{cells} \rightarrow \text{paragraphs} \rightarrow \text{runs}$$

Corporate prospectuses use tables to list board members, financial stats, and corporate details. Because cell content contains sensitive names and contact info, table cell redaction cannot be ignored. We map cell-level coordinates and apply paragraph redaction to each paragraph inside the cell.

---

## 7. Formatting

* **Preserved Formatting**: Runs that do not contain PII are untouched. The first affected run retains its styling (such as font, bold, color, and size), which is applied to the replacement text.
* **Limitations**: When PII crosses run boundaries, subsequent runs are cleared. If those subsequent runs had different styling (e.g. the second half of a name was bolded), that style is cleared. This is an acceptable trade-off for security.

---

## 8. Testing

We created **[tests/test_docx_redactor.py](file:///Users/piyushsengar/Desktop/pii-redaction-tool/tests/test_docx_redactor.py)** to verify:
* **Paragraph & Cell Redaction**: Asserts correct replacements inside paragraphs and table cells.
* **Boundary Conditions**: Tests matches at the start and end of paragraphs, and text surrounded by punctuation.
* **Cross-Run splits**: Verifies that PII split across runs is replaced correctly using the mandatory split test.
* **Formatting Preservation**: Verifies that bold formatting remains intact in unaffected runs.
* **Reopen Checks**: Re-opens redacted documents with python-docx to verify the file was saved correctly.

---

## 9. Connection Between Commits

Our project pipeline builds incrementally:

* **Commit 14 (Candidate Resolver)**: Resolves overlapping candidate spans.
* **Commit 15 (Pseudonymizer)**: Generates deterministic pseudonyms for accepted candidates.
* **Commit 16 (DOCX Redactor)**: Applies replacements in-place inside docx paragraphs and table cells, saving the file.
* **Commit 17 (End-to-End Pipeline)**: Will coordinate the complete pipeline from input DOCX to redacted output.

---

## 10. Common Beginner Mistakes

* **Editing Only `paragraph.text`**: Modifying the paragraph text directly, which deletes all runs and strips the document's styling.
* **Ignoring Tables**: Failing to traverse `doc.tables`, leaving sensitive cell text unredacted.
* **Assuming One PII = One Run**: Assuming that a candidate is always contained inside a single run, which fails on split runs.
* **Left-to-Right Processing**: Applying replacements from left-to-right, which invalidates subsequent offsets.
* **Overwriting the Original File**: Silently overwriting the input document. The tool should save to a separate output path.
* **Re-opening and Saving for Every Replacement**: Opening and saving the file for each entity, causing massive performance issues. The document should be opened once, edited in-place, and saved.
* **Running Detectors inside the Redactor**: Coupling detection and redaction logic, which leads to duplicate detections.

---

## 11. Interview Explanation

**Question:** *"How did you redact PII from a DOCX?"*

**Answer:**
> "I used python-docx to load the document. To preserve formatting, we cannot overwrite paragraph.text directly. Instead, we locate the character offsets of the PII in the visible text, identify the affected runs, and modify the run text in-place."

**Question:** *"How did you handle PII split across Word runs?"*

**Answer:**
> "I mapped the run character boundaries relative to the paragraph text. For runs that overlap with the PII span, the first affected run gets the replacement text inserted, while all subsequent affected runs have their portion of the PII text removed. Preceding and succeeding characters in the runs are preserved."

**Question:** *"Why did you process replacements right-to-left?"*

**Answer:**
> "Replacing text changes its length. If we process left-to-right, modifying an earlier span shifts all subsequent character indices, invalidating the offsets of later entities. Processing right-to-left ensures that preceding indices remain valid."

**Question:** *"How did you preserve tables?"*

**Answer:**
> "I traversed tables row-by-row and cell-by-cell. Since cells contain paragraphs, we map cell-level character offsets to their corresponding paragraphs, and reuse the paragraph redaction helper to update the cell runs in-place."

**Question:** *"What DOCX features are not currently supported?"*

**Answer:**
> "We do not support editing text inside headers, footers, hyperlinks, and images. These features are documented as out of scope for this commit."

---

## 12. Quick Revision

### 5 Key Concepts
1. Redactions must be applied to **runs** rather than paragraph text to preserve styles.
2. A single PII string can be **split across runs**.
3. Replacements are processed **right-to-left** to keep preceding offsets valid.
4. Run boundaries are **rebuilt dynamically** after each replacement.
5. Table cell text is resolved to **individual paragraphs** inside the cell.

### 3 Interview Questions
1. *Why does overwriting paragraph.text directly strip document formatting?*
2. *How does right-to-left processing keep character offsets valid?*
3. *What is the run-level strategy for handling PII split across runs?*

### 3 Practical Examples

#### Example 1: Single Run Redaction
* **Run Text**: `"Meet John Doe."`
* **PII**: `"John Doe"` (PERSON)
* **Output Run Text**: `"Meet Jane Smith."`

#### Example 2: Cross-Run Redaction
* **Runs**: `["john@", "example", ".com"]`
* **PII**: `"john@example.com"`
* **Output Runs**: `["user1@example.com", "", ""]` (runs are cleared in-place).

#### Example 3: Table Cell Redaction
* **Cell Paragraph**: `"DOB: 01/02/1995"`
* **PII**: `"01/02/1995"` (DOB)
* **Output Cell Paragraph**: `"DOB: 15/06/1990"`
