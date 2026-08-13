import re
from typing import Dict, List
from src.models import ContextEvidence, PIIType

# Positive contextual keywords for standard PII types
_POSITIVE_KEYWORDS = {
    PIIType.DOB: ["date of birth", "dob", "birth date", "birthdate", "born on", "born"],
    PIIType.EMAIL: ["email address", "email", "e-mail"],
    PIIType.PHONE: ["contact number", "phone number", "phone", "telephone", "mobile"],
    PIIType.ADDRESS: ["registered office", "residential address", "mailing address", "address"],
    PIIType.ORGANIZATION: ["company", "corporation", "incorporated", "organization", "organisation"],
}

# Negative contextual keywords for ambiguous numeric/date patterns
_NEGATIVE_KEYWORDS = {
    PIIType.DOB: [
        "date of issue", "issue date", "date of incorporation", "incorporation date",
        "date of agreement", "agreement date", "date of report", "report date",
        "date of transaction", "transaction date"
    ],
    # Phone, SSN, and generic numeric types share phone/number-negative contexts
    PIIType.PHONE: [
        "order number", "ticket number", "reference number", "registration number",
        "application number", "account number"
    ],
    PIIType.SSN: [
        "order number", "ticket number", "reference number", "registration number",
        "application number", "account number"
    ],
}

# Pre-compile positive regex patterns using word boundaries
_POSITIVE_REGEX: Dict[PIIType, re.Pattern] = {}
for pii_type, kws in _POSITIVE_KEYWORDS.items():
    # Longer phrases are placed first in the alternate match group to avoid early partial matches
    sorted_kws = sorted(kws, key=len, reverse=True)
    _POSITIVE_REGEX[pii_type] = re.compile(
        r"\b(" + "|".join(re.escape(kw) for kw in sorted_kws) + r")\b",
        re.IGNORECASE
    )

# Pre-compile negative regex patterns using word boundaries
_NEGATIVE_REGEX: Dict[PIIType, re.Pattern] = {}
for pii_type, kws in _NEGATIVE_KEYWORDS.items():
    sorted_kws = sorted(kws, key=len, reverse=True)
    _NEGATIVE_REGEX[pii_type] = re.compile(
        r"\b(" + "|".join(re.escape(kw) for kw in sorted_kws) + r")\b",
        re.IGNORECASE
    )

def evaluate_context(
    text: str,
    candidate_start: int,
    candidate_end: int,
    candidate_type: PIIType,
    window_size: int = 30
) -> ContextEvidence:
    """Evaluates local context windows around a candidate for positive or negative keywords.

    Args:
        text: The normalized text segment containing the candidate.
        candidate_start: Start index of the candidate.
        candidate_end: End index of the candidate.
        candidate_type: The PIIType category of the candidate.
        window_size: Length of context characters to inspect before and after the candidate.

    Returns:
        A ContextEvidence object summarizing the matching findings.
    """
    if not text:
        return ContextEvidence(has_positive=False, has_negative=False)

    # Extract surrounding windows
    context_before = text[max(0, candidate_start - window_size):candidate_start]
    candidate_text = text[candidate_start:candidate_end]
    context_after = text[candidate_end:min(len(text), candidate_end + window_size)]

    has_positive = False
    has_negative = False
    matched_keyword = None
    matched_rule = None
    distance = None

    # 1. Evaluate positive context
    pos_regex = _POSITIVE_REGEX.get(candidate_type)
    if pos_regex:
        # Check context before the candidate (higher priority usually)
        before_match = pos_regex.search(context_before)
        if before_match:
            has_positive = True
            matched_keyword = before_match.group(0)
            matched_rule = f"{candidate_type.name}_positive"
            # Distance from match start to candidate start
            distance = candidate_start - (max(0, candidate_start - window_size) + before_match.start())
        else:
            # Check inside the candidate text itself
            candidate_match = pos_regex.search(candidate_text)
            if candidate_match:
                has_positive = True
                matched_keyword = candidate_match.group(0)
                matched_rule = f"{candidate_type.name}_positive"
                distance = 0
            else:
                # Check context after the candidate
                after_match = pos_regex.search(context_after)
                if after_match:
                    has_positive = True
                    matched_keyword = after_match.group(0)
                    matched_rule = f"{candidate_type.name}_positive"
                    # Distance from candidate end to match start
                    distance = after_match.start()

    # 2. Evaluate negative context
    neg_regex = _NEGATIVE_REGEX.get(candidate_type)
    if neg_regex:
        # Check context before the candidate
        before_match = neg_regex.search(context_before)
        if before_match:
            has_negative = True
            matched_keyword = before_match.group(0)
            matched_rule = f"{candidate_type.name}_negative"
            distance = candidate_start - (max(0, candidate_start - window_size) + before_match.start())
        else:
            # Check inside the candidate text itself
            candidate_match = neg_regex.search(candidate_text)
            if candidate_match:
                has_negative = True
                matched_keyword = candidate_match.group(0)
                matched_rule = f"{candidate_type.name}_negative"
                distance = 0
            else:
                # Check context after the candidate
                after_match = neg_regex.search(context_after)
                if after_match:
                    has_negative = True
                    matched_keyword = after_match.group(0)
                    matched_rule = f"{candidate_type.name}_negative"
                    distance = after_match.start()

    return ContextEvidence(
        has_positive=has_positive,
        has_negative=has_negative,
        matched_keyword=matched_keyword,
        matched_rule=matched_rule,
        distance=distance
    )
