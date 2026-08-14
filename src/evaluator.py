from typing import List, Dict, Any, Tuple

def calculate_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    """Calculates precision, recall, accuracy, and F1-score safely.

    Handles zero denominators by returning 0.0.

    Args:
        tp: True Positives count.
        fp: False Positives count.
        fn: False Negatives count.
        tn: True Negatives count.

    Returns:
        A dictionary containing the computed metrics.
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return {
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "f1": f1
    }

class Evaluator:
    """Calculates accuracy, precision, recall, and F1-score for PII detection."""

    @staticmethod
    def evaluate(
        examples: List[Dict[str, Any]],
        predictions_by_example_id: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """Evaluates predictions against manual ground truth annotations.

        Args:
            examples: A list of ground truth example dictionaries.
            predictions_by_example_id: A dictionary mapping example ID to a list of predicted PIIEntity objects.

        Returns:
            A structured dictionary containing per-type and overall metrics.
        """
        # Supported PII types
        pii_types = [
            "PERSON", "EMAIL", "PHONE", "ORGANIZATION",
            "ADDRESS", "SSN", "CREDIT_CARD", "DOB", "IP_ADDRESS"
        ]

        # Initialize counts
        counts = {
            t: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for t in pii_types
        }

        for example in examples:
            ex_id = example["id"]
            preds = predictions_by_example_id.get(ex_id, [])

            # 1. Extract ground truth annotations
            gt_positives = example.get("entities", [])
            gt_negatives = example.get("non_pii", [])

            # Deduplicate by converting to sets of (start, end, type)
            unique_gt_pos = {(ent["start"], ent["end"], ent["type"]) for ent in gt_positives}
            unique_gt_neg = {(ent["start"], ent["end"], ent["type"]) for ent in gt_negatives}
            unique_preds = {(p.start, p.end, p.entity_type.name) for p in preds}

            # 2. Update counts for each PII type
            for t in pii_types:
                t_gt_pos = {item for item in unique_gt_pos if item[2] == t}
                t_gt_neg = {item for item in unique_gt_neg if item[2] == t}
                t_preds = {item for item in unique_preds if item[2] == t}

                # Calculations
                tp_set = t_preds.intersection(t_gt_pos)
                fp_set = t_preds.difference(t_gt_pos)
                fn_set = t_gt_pos.difference(t_preds)
                tn_set = t_gt_neg.difference(t_preds)

                counts[t]["tp"] += len(tp_set)
                counts[t]["fp"] += len(fp_set)
                counts[t]["fn"] += len(fn_set)
                counts[t]["tn"] += len(tn_set)

        # 3. Calculate per-type metrics
        results: Dict[str, Any] = {}
        for t in pii_types:
            c = counts[t]
            metrics = calculate_metrics(c["tp"], c["fp"], c["fn"], c["tn"])
            results[t] = {
                "tp": c["tp"],
                "fp": c["fp"],
                "fn": c["fn"],
                "tn": c["tn"],
                **metrics
            }

        # 4. Calculate overall micro-averaged metrics
        overall_tp = sum(counts[t]["tp"] for t in pii_types)
        overall_fp = sum(counts[t]["fp"] for t in pii_types)
        overall_fn = sum(counts[t]["fn"] for t in pii_types)
        overall_tn = sum(counts[t]["tn"] for t in pii_types)

        overall_metrics = calculate_metrics(overall_tp, overall_fp, overall_fn, overall_tn)
        results["OVERALL"] = {
            "tp": overall_tp,
            "fp": overall_fp,
            "fn": overall_fn,
            "tn": overall_tn,
            **overall_metrics
        }

        return results
