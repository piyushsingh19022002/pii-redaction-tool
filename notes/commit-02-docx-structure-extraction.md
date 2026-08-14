# Commit 2 Learning Notes: DOCX Structure Extraction

This document explains the concepts and design decisions implemented in Commit 2 (`feat: add docx structure extraction`).

---

## 1. What DOCX Is Internally
A `.docx` file is not a single plain text file. Internally, it is a zipped archive of XML (eXtensible Markup Language) documents and media assets.
* **Simple Example:** If you rename a `document.docx` to `document.zip` and extract it, you will see a folder structure containing files like `word/document.xml`. This XML file uses nested tags (like `<w:p>` for paragraphs and `<w:tbl>` for tables) to define formatting and store content.
* **How it will be used later:** Knowing that a DOCX is structured XML helps us understand why we cannot easily find-and-replace text directly on raw binary files; we must traverse the document's XML hierarchy.

---

## 2. What `python-docx` Is
`python-docx` is a Python library that reads and writes Microsoft Word (.docx) files by parsing the underlying XML structure and presenting it as convenient Python objects.
* **Simple Example:** Instead of manually writing code to parse XML tags like `<w:p>`, you can write `doc.paragraphs` to retrieve clean text objects.
* **How it will be used later:** We will continue to use `python-docx` to load documents, find specific nodes, replace PII with pseudonyms, and write out a new `.docx` file.

---

## 3. What `Document()` Does
In `python-docx`, the `Document(file_path)` function loads a DOCX file from a path and parses its XML structure into an in-memory `Document` object.
* **Simple Example:**
  ```python
  import docx
  doc = docx.Document("input/document.docx")
  # doc is now an active Document object representing the file
  ```
* **How it will be used later:** Whenever we need to read an input document or construct a new output document, we will initialize it using this class.

---

## 4. What Paragraphs Are
In a Word document, a paragraph is a block of text that ends with a carriage return (i.e. whenever you press "Enter"). Paragraphs can contain styled text, bold/italic runs, and lists.
* **Simple Example:** A single line of text or a full block of a text block is represented as a paragraph object in `doc.paragraphs`.
* **How it will be used later:** We will scan each paragraph segment to detect PII candidates (e.g., matching a name or phone number).

---

## 5. What Tables, Rows, and Cells Are
Tables in a DOCX are structured grids consisting of:
* **Table (`Table`)**: The parent container.
* **Row (`Row`)**: Horizontal lines of cells within the table.
* **Cell (`Cell`)**: Individual grid blocks containing text.
* **Simple Example:** In a 2x2 table:
  ```text
  [ Row 0, Cell 0 ] [ Row 0, Cell 1 ]
  [ Row 1, Cell 0 ] [ Row 1, Cell 1 ]
  ```
* **How it will be used later:** We will search cells individually for PII, resolving any matches inside tabular data.

---

## 6. Why We Need to Extract Both Paragraphs and Tables
In Word documents, paragraphs and tables are stored separately in the XML hierarchy. The `doc.paragraphs` list **only** contains top-level paragraphs. Paragraphs inside table cells are nested inside `table.rows[i].cells[j].paragraphs` and are not included in the main list.
* **Simple Example:** If a document has a heading paragraph followed by a table, extracting only `doc.paragraphs` would completely miss the text inside the table.
* **How it will be used later:** Extracting both ensures that we scan the entire visible text content of the document for PII.

---

## 7. What a Dataclass Is
Introduced in Python 3.7, a `@dataclass` is a decorator that automatically generates boilerplate code (like `__init__`, `__repr__`, and `__eq__`) for classes designed primarily to hold data.
* **Simple Example:**
  ```python
  from dataclasses import dataclass

  @dataclass
  class User:
      username: str
      email: str
  ```
* **How it will be used later:** Using `TextSegment` as a dataclass allows us to easily create, modify, print, and compare extracted text units without writing tedious constructor methods.

---

## 8. What `TextSegment` Represents
`TextSegment` is our reusable data model that packages a single logical block of extracted text alongside metadata about where it came from.
* **Simple Example:** Rather than passing around raw strings, we pass a `TextSegment` that contains the string `"REGISTERED OFFICE"` alongside information that it was found in Table 0, Row 0, Cell 0.
* **How it will be used later:** The detection engine will process lists of `TextSegment` objects, appending PII findings to their respective segments.

---

## 9. Why `segment_type` is Useful
`segment_type` is a string field (e.g. `"paragraph"` or `"table-cell"`) that tells downstream code how to handle the segment, since paragraphs and tables have different XML paths.
* **Simple Example:** If `segment_type == "paragraph"`, the system knows to look for `paragraph_index`. If it's `"table-cell"`, it knows to check `table_index`, `row_index`, and `cell_index`.
* **How it will be used later:** The reconstruction engine will read this type to decide whether to update a top-level paragraph or write back into a table cell.

---

## 10. Why `paragraph_index` is Stored
It records the absolute position of the paragraph in `doc.paragraphs`.
* **Simple Example:** If a segment has `paragraph_index: 5`, it came from `doc.paragraphs[5]`.
* **How it will be used later:** During reconstruction, when we need to write a pseudonymized text, we will update the text of `doc.paragraphs[paragraph_index]`.

---

## 11. Why `table_index`, `row_index`, and `cell_index` are Stored
These indexes store the 3D grid coordinates of table-based text.
* **Simple Example:** `table_index: 0`, `row_index: 1`, `cell_index: 1` points to `doc.tables[0].rows[1].cells[1]`.
* **How it will be used later:** When replacing PII inside a table, we use these coordinates to pinpoint and update the text in that specific cell.

---

## 12. Why We Are Preserving Location Information
Because we need to recreate the original document structure with identical styling and layouts, we cannot simply extract all text, modify it, and write a new plain text file. We must overwrite the PII *in-place* inside the original document. Location metadata is the "map" that lets us navigate back to the correct spot.
* **Simple Example:** If we redact the name "John Doe" in the text, we need to know exactly which paragraph or table cell it was in, so we can swap it out without affecting the surrounding headers, fonts, and borders.
* **How it will be used later:** The reconstruction pipeline relies entirely on these indexes to replace sensitive text in the active document object before saving it.

---

## 13. Why We Are Not Doing Normalization Yet
Normalization (e.g., lowercasing, removing punctuation, or replacing accents) makes it easier for machine learning or regex models to detect PII. However, doing it during extraction would destroy the original text format.
* **Simple Example:** If we normalize `"John Doe"` to `"john doe"` during extraction, the reconstructed document would lose its capitalization.
* **How it will be used later:** We will perform normalization on copies of the text in the candidate generation phase, keeping the original segment text clean for final output rendering.

---

## 14. Why We Are Not Doing PII Detection Yet
We are using an incremental development model. Adding extraction, detection, pseudonymization, and reconstruction all at once creates too much complexity and makes debugging very difficult.
* **Simple Example:** Separating extraction from detection allows us to build unit tests confirming that our document reader works perfectly on tables before we write any regular expressions.
* **How it will be used later:** In subsequent commits, we will build candidate generators that run directly on top of the structured segments outputted by this step.

---

## 15. How This Commit Connects to Future DOCX Reconstruction
The extraction and reconstruction phases are two sides of the same coin:
1. **Extraction (This Commit):** `Document` → `TextSegment` (preserving locations).
2. **Detection & Redaction (Future):** `TextSegment` → `Redacted TextSegment` (content swapped).
3. **Reconstruction (Future):** `Redacted TextSegment` + Original `Document` (using preserved locations) → Finished Redacted DOCX.

---

## Structural Pipeline Example

Here is a visual map showing how content flows from a document into our `TextSegment` models:

```
[Document]
  ├── Paragraph 0: "RED HERRING PROSPECTUS"
  │     └── TextSegment(text="RED HERRING PROSPECTUS", segment_type="paragraph", paragraph_index=0)
  │
  └── Table 0
        └── Row 0
              └── Cell 0: "REGISTERED OFFICE"
                    └── TextSegment(text="REGISTERED OFFICE", segment_type="table-cell", table_index=0, row_index=0, cell_index=0)
```

---

## Interview Explanation

**Question:** *"How does your system extract information from a DOCX document while preserving enough structure for later redaction?"*

**Answer:**
> "To extract text from a DOCX file while retaining its formatting structure, I wrote a parser using the python-docx library. Since paragraphs and tables exist in different XML subtrees, the parser traverses them independently. For each non-empty text element, it creates a TextSegment dataclass. Along with the text, this dataclass stores structural coordinates: the paragraph index for standard text, or the table, row, and cell indices for tabular text. This location metadata serves as a coordinate map, letting us perform in-place text replacement in later stages without corrupting the document's original styling or layout."
