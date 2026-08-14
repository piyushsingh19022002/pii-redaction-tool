import pytest
from src.models import PIIEntity, PIIType
from src.evaluator import Evaluator

def test_perfect_predictions():
    """Verifies evaluation when predicted entities perfectly match ground truth."""
    examples = [
        {
            "id": "ex1",
            "text": "Email john@example.com is private.",
            "entities": [
                {"text": "john@example.com", "type": "EMAIL", "start": 6, "end": 22}
            ],
            "non_pii": []
        }
    ]

    preds = {
        "ex1": [PIIEntity("john@example.com", PIIType.EMAIL, 6, 22, 0.90, "regex")]
    }

    report = Evaluator.evaluate(examples, preds)

    # EMAIL specific checks
    email_rep = report["EMAIL"]
    assert email_rep["tp"] == 1
    assert email_rep["fp"] == 0
    assert email_rep["fn"] == 0
    assert email_rep["tn"] == 0
    assert email_rep["precision"] == 1.0
    assert email_rep["recall"] == 1.0
    assert email_rep["accuracy"] == 1.0
    assert email_rep["f1"] == 1.0

def test_one_false_positive():
    """Verifies metric degradation when there is a false positive prediction."""
    examples = [
        {
            "id": "ex1",
            "text": "Hello world.",
            "entities": [],
            "non_pii": []
        }
    ]

    preds = {
        "ex1": [PIIEntity("Hello", PIIType.PERSON, 0, 5, 0.90, "ner")]
    }

    report = Evaluator.evaluate(examples, preds)
    person_rep = report["PERSON"]

    assert person_rep["tp"] == 0
    assert person_rep["fp"] == 1
    assert person_rep["fn"] == 0
    assert person_rep["tn"] == 0
    assert person_rep["precision"] == 0.0
    assert person_rep["recall"] == 0.0
    assert person_rep["accuracy"] == 0.0
    assert person_rep["f1"] == 0.0

def test_one_false_negative():
    """Verifies recall degradation when there is an undetected entity."""
    examples = [
        {
            "id": "ex1",
            "text": "Email is john@example.com.",
            "entities": [
                {"text": "john@example.com", "type": "EMAIL", "start": 9, "end": 25}
            ],
            "non_pii": []
        }
    ]

    # No predictions
    preds = {"ex1": []}

    report = Evaluator.evaluate(examples, preds)
    email_rep = report["EMAIL"]

    assert email_rep["tp"] == 0
    assert email_rep["fp"] == 0
    assert email_rep["fn"] == 1
    assert email_rep["precision"] == 0.0
    assert email_rep["recall"] == 0.0
    assert email_rep["accuracy"] == 0.0
    assert email_rep["f1"] == 0.0

def test_wrong_entity_type_not_tp():
    """Verifies that matching span but incorrect type results in 1 FP and 1 FN, not a TP."""
    examples = [
        {
            "id": "ex1",
            "text": "Match john@example.com text.",
            "entities": [
                {"text": "john@example.com", "type": "EMAIL", "start": 6, "end": 22}
            ],
            "non_pii": []
        }
    ]

    # Predicted as PERSON instead of EMAIL
    preds = {
        "ex1": [PIIEntity("john@example.com", PIIType.PERSON, 6, 22, 0.90, "ner")]
    }

    report = Evaluator.evaluate(examples, preds)

    # EMAIL checks (1 FN)
    assert report["EMAIL"]["tp"] == 0
    assert report["EMAIL"]["fn"] == 1
    assert report["EMAIL"]["fp"] == 0

    # PERSON checks (1 FP)
    assert report["PERSON"]["tp"] == 0
    assert report["PERSON"]["fp"] == 1
    assert report["PERSON"]["fn"] == 0

def test_duplicate_prediction_handling():
    """Verifies duplicate predicted entities are treated as a single prediction."""
    examples = [
        {
            "id": "ex1",
            "text": "My phone +91 9876543210 is here.",
            "entities": [
                {"text": "+91 9876543210", "type": "PHONE", "start": 9, "end": 23}
            ],
            "non_pii": []
        }
    ]

    # Two identical predictions (same span and type)
    preds = {
        "ex1": [
            PIIEntity("+91 9876543210", PIIType.PHONE, 9, 23, 0.90, "regex"),
            PIIEntity("+91 9876543210", PIIType.PHONE, 9, 23, 0.95, "regex")
        ]
    }

    report = Evaluator.evaluate(examples, preds)
    phone_rep = report["PHONE"]

    # Only counts as 1 TP, not 2
    assert phone_rep["tp"] == 1
    assert phone_rep["fp"] == 0
    assert phone_rep["fn"] == 0

def test_accuracy_calculation_with_annotated_tn():
    """Verifies that accuracy metrics correctly evaluate explicitly annotated negative spans."""
    examples = [
        {
            "id": "ex1",
            "text": "Order 1234-5678-9012.",
            "entities": [],
            "non_pii": [
                {"text": "1234-5678-9012", "type": "CREDIT_CARD", "start": 6, "end": 20}
            ]
        }
    ]

    # CASE A: Successful rejection of non-PII -> counts as True Negative
    preds_tn = {"ex1": []}
    report_tn = Evaluator.evaluate(examples, preds_tn)
    cc_tn = report_tn["CREDIT_CARD"]
    assert cc_tn["tp"] == 0
    assert cc_tn["fp"] == 0
    assert cc_tn["fn"] == 0
    assert cc_tn["tn"] == 1
    assert cc_tn["accuracy"] == 1.0

    # CASE B: False positive prediction -> counts as FP and NOT TN
    preds_fp = {
        "ex1": [PIIEntity("1234-5678-9012", PIIType.CREDIT_CARD, 6, 20, 0.90, "regex")]
    }
    report_fp = Evaluator.evaluate(examples, preds_fp)
    cc_fp = report_fp["CREDIT_CARD"]
    assert cc_fp["tp"] == 0
    assert cc_fp["fp"] == 1
    assert cc_fp["fn"] == 0
    assert cc_fp["tn"] == 0
    assert cc_fp["accuracy"] == 0.0

def test_f1_score_calculation():
    """Verifies mathematical F1-score equation calculations."""
    # If tp=1, fp=1, fn=1:
    # precision = 1 / 2 = 0.5
    # recall = 1 / 2 = 0.5
    # f1 = 2 * (0.5 * 0.5) / (0.5 + 0.5) = 0.5
    examples = [
        {
            "id": "ex1",
            "text": "Email1: a@b.com, Email2: c@d.com.",
            "entities": [
                {"text": "a@b.com", "type": "EMAIL", "start": 8, "end": 15},
                {"text": "c@d.com", "type": "EMAIL", "start": 25, "end": 32}
            ],
            "non_pii": []
        }
    ]

    # Predict one correct email, and one false positive email
    preds = {
        "ex1": [
            PIIEntity("a@b.com", PIIType.EMAIL, 8, 15, 0.90, "regex"),
            PIIEntity("c@d.com", PIIType.EMAIL, 0, 5, 0.90, "regex") # wrong span -> FP
        ]
    }

    report = Evaluator.evaluate(examples, preds)
    email_rep = report["EMAIL"]

    assert email_rep["tp"] == 1
    assert email_rep["fp"] == 1
    assert email_rep["fn"] == 1
    assert email_rep["precision"] == 0.5
    assert email_rep["recall"] == 0.5
    assert email_rep["f1"] == 0.5
