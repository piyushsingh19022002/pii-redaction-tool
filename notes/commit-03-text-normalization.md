# Commit 3 Learning Notes: Document Text Normalization

This document details the concepts and architectural choices implemented in Commit 3 (`feat: add document text normalization`).

---

## 1. What Text Normalization Means
Text normalization is the process of translating raw, unstandardized text into a consistent, standard format. It cleans up variations in spelling, encoding, and spacing without altering the core semantic meaning of the words.
* **Simple Example:** Converting `"John\xa0Smith"` (where `\xa0` is a non-breaking space) to `"John Smith"` (with a standard space).

---

## 2. Why Normalization is Necessary in a DOCX PII Detection System
In Word documents, text can contain invisible characters, varying encoding formats, and irregular spacing. If a user types three spaces between their first and last name, or if Word inserts formatting codes, a regex or Named Entity Recognition (NER) model looking for PII might fail to match it.
* **Simple Example:** A regex looking for `[A-Z][a-z]+ [A-Z][a-z]+` (like `"John Smith"`) will fail on `"John   Smith"` because of the multiple spaces. Normalizing it to a single space ensures the match succeeds.

---

## 3. Why Extracted Word Text Can Contain Formatting or Unicode Artifacts
Word documents are complex XML files designed for visual layout. To handle line wraps, hyphenation, or custom fonts, Word may inject hidden characters like soft hyphens (`\xad`), zero-width spaces (`\u200b`), or non-breaking spaces (`\xa0`). When we extract raw text, these layout artifacts remain in the strings.
* **Simple Example:** Word might save the city name `"Maharashtra"` as `"Maha\xadrashtra"` to allow hyphenation at the end of a line. While it looks normal on-screen, a python script sees the `\xad` character inside the string.

---

## 4. What Unicode Normalization Means
Unicode allows different binary sequences to represent visually identical characters. For example, accented letters can be represented as a single character (e.g. `é`) or as a base character plus a combining accent mark (e.g. `e` + `´`). Unicode Normalization (specifically `NFKC`) decomposes compatibility variants and recomposes them into standard, uniform character representations.
* **Simple Example:** NFKC normalizes full-width Roman characters like `"Ｈｅｌｌｏ"` to standard characters: `"Hello"`.

---

## 5. What Control Characters Are
Control characters are non-printing characters used to instruct software on how to format or render text. In Unicode, these belong to the category "Other" (starting with `'C'`). Examples include null bytes (`\x00`), formatting marks, zero-width spaces (`\u200b`), and soft hyphens (`\xad`).
* **Simple Example:** `\x00` is a null byte control character that has no visual representation and can cause text parsers to terminate early.

---

## 6. What Whitespace Normalization Means
Whitespace normalization is the process of standardizing the spacing between characters. It involves stripping leading/trailing whitespace margins and collapsing multiple consecutive whitespace characters (like spaces and tabs) into a single standard space (`\x20`).
* **Simple Example:** Transforming `"  hello   world  "` into `"hello world"`.

---

## 7. Why Tabs and Repeated Spaces May Need Normalization
In documents, tabs and repeated spaces are often used for alignment or columns. If left un-normalized, they interfere with search and matching models that expect words to be separated by a single space.
* **Simple Example:** A phone number typed as `"555   1234"` will not match a standard phone number regex if the extra spacing is not collapsed.

---

## 8. Why We Must Be Careful with Newlines
We cannot blindly replace all line breaks (`\n` or `\r`) with spaces at the document level. Doing so would merge different lines of text together, which could destroy structural context and make it harder to identify layouts.
* **Simple Example:** Merging a header and a paragraph might concatenate `"CONFIDENTIAL"` and `"This document..."` into `"CONFIDENTIAL This document..."`.

---

## 9. Why Addresses Make Newline Handling Important
Physical and mailing addresses are typically structured across multiple lines. PII detectors and parser rules rely on the line boundaries (like `\n`) to recognize that a block of text is an address.
* **Simple Example:**
  ```text
  123 Main Street
  Suite 100
  New York, NY 10001
  ```
  If we replace newlines with spaces, the address becomes `"123 Main Street Suite 100 New York, NY 10001"`. While still readable, the line-by-line boundaries are lost, which makes regex or NER parsing of addresses more difficult.

---

## 10. Why Normalization Must Happen Before PII Detection
PII detectors (regex, NER) require clean, predictable text. By placing normalization before detection, we strip away all random noise (like double spaces, formatting artifacts, or unusual Unicode forms) so the detectors only have to handle standard text.
* **Simple Example:** By normalizing `"Maha\xadrashtra"` to `"Maharashtra"`, we ensure our future location detector only needs to look for `"Maharashtra"`.

---

## 11. Why Normalization Should Not Modify the Original DOCX
The source document must remain untouched because we want to preserve its original layout, styles, and exact spacing. Overwriting the original text during extraction would corrupt the formatting of the document.
* **Simple Example:** If a document has double spacing for visual design, we want to keep that design in the final output. The raw text must be preserved so we can do a precise swap during reconstruction.

---

## 12. Why the Normalizer Should Be Independent of PII Detection
The normalizer's only job is to clean up characters and spacing; it should not know anything about PII categories (like Names, Emails, or Phone Numbers). Keeping them decoupled makes the normalizer reusable and easy to test.
* **Simple Example:** We can test the normalizer against control characters without needing to load machine learning models or regex patterns.

---

## 13. How This Commit Connects to Regex and NER in Future Commits
In the upcoming commits, the PII detectors will run their matching rules against `TextSegment.normalized_text`. Once they find a match (e.g. finding a name in the normalized string), they will record the character index. Because the coordinates point back to `TextSegment`, we can map the redacted output back to the original layout.

---

## Key Differences: Raw vs. Normalized vs. Redacted

| Text Type | Purpose | Example |
| :--- | :--- | :--- |
| **Raw Document Text** | Preserves original layout and XML formatting details; used for final file output writing. | `"John   Doe\xa0\xa0lives\xad\xadin Mumbai"` |
| **Normalized Detection Text** | Standardized, clean text used by Regex and NER models to find PII. | `"John Doe lives in Mumbai"` |
| **Final Redacted Document** | The output document with PII replaced by pseudonyms, keeping original styles. | `"John_Doe_1 lives in Mumbai_1"` |

---

## Interview Explanation

**Question:** *"Why did you add a text normalization layer before PII detection?"*

**Answer:**
> "I added a text normalization layer because raw text extracted from DOCX documents is often noisy, containing layout artifacts like soft hyphens, zero-width spaces, and irregular spacing. If left un-normalized, these formatting characters can break regular expressions and machine-learning models, leading to missed PII. The normalization layer standardizes Unicode representation and collapses repeated spaces while preserving line breaks for structures like multi-line addresses. By keeping the raw text and normalized text side-by-side in our TextSegment models, we ensure that detection runs on clean text, while preserving the raw formatting needed for accurate document reconstruction later."
