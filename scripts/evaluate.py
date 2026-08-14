import os
import json
import logging
from typing import List
from src.pipeline import PIIRedactionPipeline
from src.context.rules import evaluate_context
from src.resolver import resolve_candidate, resolve_overlaps
from src.evaluator import Evaluator
from src.models import PIIEntity

# Turn off verbose logging during evaluation runs unless needed
logging.basicConfig(level=logging.WARNING)

def get_predictions(text: str, pipeline: PIIRedactionPipeline) -> List[PIIEntity]:
    """Simulates the pipeline extraction/resolution stages for a single raw string.

    Args:
        text: The raw text string.
        pipeline: Instantiated PIIRedactionPipeline.

    Returns:
        A list of accepted PIIEntity objects.
    """
    candidates = []
    for detector in pipeline.detectors:
        try:
            candidates.extend(detector.detect(text))
        except Exception as e:
            # Silently log errors to keep evaluate output clean
            logging.error("Detector %s failed: %s", detector.__class__.__name__, str(e))

    resolved_results = []
    for cand in candidates:
        evidence = evaluate_context(
            text=text,
            candidate_start=cand.start,
            candidate_end=cand.end,
            candidate_type=cand.entity_type
        )
        res = resolve_candidate(cand, evidence)
        resolved_results.append(res)

    accepted = resolve_overlaps(resolved_results)
    return [res.entity for res in accepted]

def main() -> None:
    # 1. Load ground truth dataset
    gt_path = os.path.join("evaluation", "ground_truth.json")
    if not os.path.exists(gt_path):
        print(f"Error: Ground truth file '{gt_path}' not found.")
        return

    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    examples = data.get("examples", [])
    print(f"Loaded {len(examples)} evaluation examples from ground truth.")

    # 2. Get predictions using existing pipeline/detectors
    pipeline = PIIRedactionPipeline()
    predictions_by_example_id = {}

    for ex in examples:
        text = ex["text"]
        preds = get_predictions(text, pipeline)
        predictions_by_example_id[ex["id"]] = preds

    # 3. Evaluate predictions
    report = Evaluator.evaluate(examples, predictions_by_example_id)

    # 4. Print metrics summary report
    print("\n======================================================================")
    print("PII DETECTION EVALUATION REPORT")
    print("======================================================================")
    print(f"Total Examples: {len(examples)}")
    print(f"Evaluation Matching Mode: EXACT SPAN & TYPE MATCHING\n")

    print(f"{'PII TYPE':<15} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'TN':<4} | {'PRECISION':<9} | {'RECALL':<9} | {'ACCURACY':<9} | {'F1-SCORE':<9}")
    print("-" * 92)

    pii_types = [
        "PERSON", "EMAIL", "PHONE", "ORGANIZATION", "ADDRESS",
        "SSN", "CREDIT_CARD", "DOB", "IP_ADDRESS"
    ]

    for t in pii_types:
        r = report[t]
        print(f"{t:<15} | {r['tp']:<4} | {r['fp']:<4} | {r['fn']:<4} | {r['tn']:<4} | {r['precision']:<9.4f} | {r['recall']:<9.4f} | {r['accuracy']:<9.4f} | {r['f1']:<9.4f}")

    print("-" * 92)
    overall = report["OVERALL"]
    print(f"{'OVERALL (MICRO)':<15} | {overall['tp']:<4} | {overall['fp']:<4} | {overall['fn']:<4} | {overall['tn']:<4} | {overall['precision']:<9.4f} | {overall['recall']:<9.4f} | {overall['accuracy']:<9.4f} | {overall['f1']:<9.4f}")
    print("======================================================================\n")

if __name__ == "__main__":
    main()
