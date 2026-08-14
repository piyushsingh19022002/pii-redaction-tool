import os
import logging
from typing import List, Tuple, Dict, Any, Optional
from src.models import TextSegment, PIIEntity, ResolutionResult
from src.pseudonymizer import Pseudonymizer
from src.docx_reader import extract_segments
from src.context.rules import evaluate_context
from src.resolver import resolve_candidate, resolve_overlaps
from src.docx_redactor import redact_docx

logger = logging.getLogger(__name__)

class PipelineResult:
    """Stores metadata and summary metrics for a pipeline run."""
    def __init__(
        self,
        input_path: str,
        output_path: str,
        segments_processed: int,
        candidates_detected: int,
        candidates_accepted: int,
        candidates_rejected: int,
        counts_by_type: Dict[str, int]
    ) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.segments_processed = segments_processed
        self.candidates_detected = candidates_detected
        self.candidates_accepted = candidates_accepted
        self.candidates_rejected = candidates_rejected
        self.counts_by_type = counts_by_type

class PIIRedactionPipeline:
    """Orchestrates the end-to-end PII detection and redaction process."""

    def __init__(self, detectors: Optional[List[Any]] = None) -> None:
        """Initializes the pipeline with a registry of detectors.

        Args:
            detectors: Optional list of injected detectors. If None, default detectors are used.
        """
        if detectors is None:
            # Lazy import to avoid loading spaCy/NER model unless pipeline is run
            from src.detectors.email import EmailDetector
            from src.detectors.phone import PhoneDetector
            from src.detectors.ip_address import IPDetector
            from src.detectors.ssn import SSNDetector
            from src.detectors.credit_card import CreditCardDetector
            from src.detectors.dob import DOBDetector
            from src.detectors.ner import NERDetector
            from src.detectors.address import AddressDetector

            self.detectors = [
                EmailDetector(),
                PhoneDetector(),
                IPDetector(),
                SSNDetector(),
                CreditCardDetector(),
                DOBDetector(),
                NERDetector(),
                AddressDetector()
            ]
        else:
            self.detectors = detectors

    def run(self, input_path: str, output_path: str) -> PipelineResult:
        """Executes the pipeline: extracts text, detects PII, resolves overlaps, pseudonymizes, and saves the redacted document.

        Args:
            input_path: Path to the original DOCX document.
            output_path: Path where the redacted DOCX should be saved.

        Returns:
            A PipelineResult object containing execution metrics.
        """
        logger.info("Starting pipeline execution.")

        # Validate input file existence
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

        # 1. Extract text segments
        segments = extract_segments(input_path)
        logger.info("Extracted %d segments from document.", len(segments))

        # Shared pseudonymizer to maintain consistency across the entire document
        pseudonymizer = Pseudonymizer()

        all_candidates_count = 0
        all_accepted_count = 0
        all_rejected_count = 0

        counts_by_type = {
            "PERSON": 0,
            "EMAIL": 0,
            "PHONE": 0,
            "ORGANIZATION": 0,
            "ADDRESS": 0,
            "SSN": 0,
            "CREDIT_CARD": 0,
            "DOB": 0,
            "IP_ADDRESS": 0
        }

        redaction_replacements = []

        # Process segment-by-segment
        for seg in segments:
            # Skip empty segments
            if not seg.normalized_text:
                continue

            # Run detectors
            segment_candidates: List[PIIEntity] = []
            for detector in self.detectors:
                try:
                    matches = detector.detect(seg.normalized_text)
                    segment_candidates.extend(matches)
                except Exception as e:
                    logger.error(
                        "Detector %s failed on segment: %s",
                        detector.__class__.__name__,
                        str(e)
                    )
                    raise e

            all_candidates_count += len(segment_candidates)

            # Evaluate context and resolve individually
            resolved_results = []
            for cand in segment_candidates:
                evidence = evaluate_context(
                    text=seg.normalized_text,
                    candidate_start=cand.start,
                    candidate_end=cand.end,
                    candidate_type=cand.entity_type
                )
                res = resolve_candidate(cand, evidence)
                resolved_results.append(res)

            # Resolve overlaps at the segment level
            accepted_results = resolve_overlaps(resolved_results)
            all_accepted_count += len(accepted_results)
            all_rejected_count += (len(segment_candidates) - len(accepted_results))

            # Fetch or generate pseudonyms and build replacements list
            for res in accepted_results:
                cand = res.entity
                replacement = pseudonymizer.pseudonymize(cand)

                # Update counts
                type_name = cand.entity_type.name
                if type_name in counts_by_type:
                    counts_by_type[type_name] += 1
                else:
                    counts_by_type[type_name] = counts_by_type.get(type_name, 0) + 1

                redaction_replacements.append((seg, cand, replacement))

        # 2. Write replacements to the output file using the redactor
        logger.info("Applying %d accepted replacements to document.", len(redaction_replacements))
        try:
            redact_docx(
                input_path=input_path,
                output_path=output_path,
                replacements=redaction_replacements
            )
        except Exception as e:
            logger.error("DOCX redaction failed: %s", str(e))
            raise e

        logger.info("Pipeline execution completed successfully.")
        return PipelineResult(
            input_path=input_path,
            output_path=output_path,
            segments_processed=len(segments),
            candidates_detected=all_candidates_count,
            candidates_accepted=all_accepted_count,
            candidates_rejected=all_rejected_count,
            counts_by_type=counts_by_type
        )
