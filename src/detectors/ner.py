import spacy
from typing import List
from src.detectors.base import BaseDetector
from src.models import PIIEntity, PIIType

class NERDetector(BaseDetector):
    """PII Detector using spaCy Named Entity Recognition (NER).

    Loads the 'en_core_web_sm' model once during initialization.
    Processes PERSON and ORG entities, mapping them to PIIType.PERSON
    and PIIType.ORGANIZATION respectively.
    """

    def __init__(self) -> None:
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError(
                "spaCy model 'en_core_web_sm' not found. "
                "Please run: python -m spacy download en_core_web_sm"
            )

        # Mapping spaCy entity labels to PIIType enums
        self.label_mapping = {
            "PERSON": PIIType.PERSON,
            "ORG": PIIType.ORGANIZATION
        }

        # Detector-level confidence for NER.
        # Since standard spaCy pipelines do not provide individual entity confidence scores,
        # we assign a reasonable default confidence of 0.85 and document this limitation.
        self.confidence_level = 0.85

    def detect(self, text: str) -> List[PIIEntity]:
        """Scans the text using spaCy NER and helper regexes for ORGANIZATION and ADDRESS.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of detected PIIEntity objects.
        """
        import re
        entities: List[PIIEntity] = []
        if not text:
            return entities

        # 1. spaCy NER candidates
        doc = self.nlp(text)
        # Added credit card brands and standard technical protocol terms to filtered list
        filtered_terms = {
            "SSN", "IP", "LLC", "SERVER IP", "DNS", "VISA", 
            "MASTERCARD", "AMEX", "RUPAY", "DISCOVER", "JCB"
        }

        for ent in doc.ents:
            if ent.label_ in self.label_mapping:
                ent_text = ent.text.strip()
                # Skip common false positive abbreviations/terms
                if ent_text.upper() in filtered_terms:
                    continue
                # Skip date-like strings (e.g. "01/02/1995")
                if re.match(r"^\d+[\/\-\.]\d+[\/\-\.]\d+$", ent_text):
                    continue
                # Skip purely numeric strings
                if ent_text.isdigit():
                    continue

                start_char = ent.start_char
                end_char = ent.end_char

                # Span alignment check:
                # If matched text ends in common abbreviations like "Inc", "Corp", "Ltd", "Co" but is followed by a period:
                abbreviations = {"INC", "CORP", "LTD", "CO", "LLC"}
                if any(ent_text.upper().endswith(abbr) for abbr in abbreviations):
                    if end_char < len(text) and text[end_char] == ".":
                        end_char += 1
                        ent_text += "."

                entities.append(PIIEntity(
                    text=ent_text,
                    entity_type=self.label_mapping[ent.label_],
                    start=start_char,
                    end=end_char,
                    confidence=self.confidence_level,
                    source="ner"
                ))

        # 2. General organization suffix regex candidate scan
        # Matches capitalized words followed by LLC, Inc., Corp., Ltd., Co., or Limited.
        # Boundary check at the end uses negative lookahead instead of \b to avoid failure on trailing periods.
        org_pattern = re.compile(
            r"\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:LLC|Inc\.|Corp\.|Ltd\.|Limited|Co\.)(?![a-zA-Z0-9])"
        )
        for match in org_pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(0),
                entity_type=PIIType.ORGANIZATION,
                start=match.start(),
                end=match.end(),
                confidence=0.90,  # strong rule-based confidence
                source="regex_org"
            ))

        return entities
