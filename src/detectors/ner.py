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
        """Scans the text using spaCy NER, maps PERSON/ORG entities, and returns PIIEntity objects.

        Args:
            text: The normalized text segment to search.

        Returns:
            A list of detected PIIEntity objects.
        """
        entities: List[PIIEntity] = []
        if not text:
            return entities

        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in self.label_mapping:
                entities.append(PIIEntity(
                    text=ent.text,  # Keep the exact original text span unmodified
                    entity_type=self.label_mapping[ent.label_],
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=self.confidence_level,
                    source="ner"
                ))

        return entities
