from typing import List, Optional
from src.models import PIIEntity, ContextEvidence, ResolutionResult

def resolve_candidate(
    candidate: PIIEntity,
    evidence: Optional[ContextEvidence],
    acceptance_threshold: float = 0.70,
    context_bonus: float = 0.15,
    context_penalty: float = 0.30
) -> ResolutionResult:
    """Calculates the resolution score and acceptance decision for a single candidate.

    Scoring is calculated as:
        score = detector_confidence + context_bonus (if positive) - context_penalty (if negative)
    clamped to the range [0.0, 1.0].

    Args:
        candidate: The original candidate PIIEntity.
        evidence: Optional ContextEvidence gathered around the candidate.
        acceptance_threshold: Score threshold above which a candidate is accepted.
        context_bonus: Score bonus added for positive context.
        context_penalty: Score penalty subtracted for negative context.

    Returns:
        A ResolutionResult containing the entity, final score, decision, and rationale.
    """
    score = candidate.confidence

    if not evidence:
        is_accepted = score >= acceptance_threshold
        if is_accepted:
            reason = f"Accepted based on detector confidence {score:.2f} (no context evaluated)."
        else:
            reason = f"Rejected: score {score:.2f} below threshold {acceptance_threshold:.2f}."
        return ResolutionResult(
            entity=candidate,
            is_accepted=is_accepted,
            score=score,
            reason=reason
        )

    # Calculate score adjustments based on context evidence
    if evidence.has_positive and evidence.has_negative:
        score = score + context_bonus - context_penalty
        reason = (
            f"Conflicting context: positive keyword '{evidence.matched_keyword}' "
            f"found, but negative keyword decreased final score."
        )
    elif evidence.has_positive:
        score = score + context_bonus
        reason = f"Accepted with positive context bonus for keyword '{evidence.matched_keyword}'."
    elif evidence.has_negative:
        score = score - context_penalty
        reason = f"Rejected/reduced due to negative context keyword '{evidence.matched_keyword}'."
    else:
        reason = f"No context matches; using baseline detector confidence {score:.2f}."

    # Clamp and round the score to [0.0, 1.0]
    score = round(max(0.0, min(1.0, score)), 4)

    is_accepted = score >= acceptance_threshold

    # If the score fell below threshold, override the reason to reflect rejection
    if not is_accepted and "Rejected" not in reason:
        reason = f"Rejected: score {score:.2f} fell below threshold {acceptance_threshold:.2f}. " + reason

    return ResolutionResult(
        entity=candidate,
        is_accepted=is_accepted,
        score=score,
        reason=reason
    )

def resolve_candidates(
    candidates: List[PIIEntity],
    text: str,
    acceptance_threshold: float = 0.70,
    context_bonus: float = 0.15,
    context_penalty: float = 0.30,
    window_size: int = 30
) -> List[ResolutionResult]:
    """Evaluates context and resolves all candidates individually.

    Args:
        candidates: List of candidate PIIEntity objects.
        text: The text segment.
        acceptance_threshold: Score threshold for acceptance.
        context_bonus: Bonus for positive context.
        context_penalty: Penalty for negative context.
        window_size: Surrounding context window size.

    Returns:
        A list of ResolutionResult objects for all candidates.
    """
    from src.context.rules import evaluate_context

    results = []
    for cand in candidates:
        evidence = evaluate_context(
            text=text,
            candidate_start=cand.start,
            candidate_end=cand.end,
            candidate_type=cand.entity_type,
            window_size=window_size
        )
        res = resolve_candidate(
            candidate=cand,
            evidence=evidence,
            acceptance_threshold=acceptance_threshold,
            context_bonus=context_bonus,
            context_penalty=context_penalty
        )
        results.append(res)
    return results

def resolve_overlaps(results: List[ResolutionResult]) -> List[ResolutionResult]:
    """Resolves overlapping candidates deterministically, prioritizing higher scores and spans.

    Overlap condition:
    Candidate A and B overlap if:
        A.start < B.end AND B.start < A.end
    using half-open intervals [start, end).

    Tie-breaking logic:
    1. Stronger resolution score.
    2. Longer span length (end - start).
    3. Alphabetically by entity_type name (stable deterministic tie-breaker).
    4. Earlier start offset (stable deterministic tie-breaker).

    Args:
        results: List of ResolutionResult objects.

    Returns:
        A list of non-overlapping accepted ResolutionResult objects.
    """
    # Filter to accepted candidates only
    accepted = [r for r in results if r.is_accepted]
    if not accepted:
        return []

    # Sort accepted results by priority:
    # 1. Score descending
    # 2. Span length descending
    # 3. Entity type name ascending
    # 4. Start index ascending
    def sort_key(res: ResolutionResult) -> tuple:
        span_len = res.entity.end - res.entity.start
        return (-res.score, -span_len, res.entity.entity_type.name, res.entity.start)

    sorted_accepted = sorted(accepted, key=sort_key)

    non_overlapping: List[ResolutionResult] = []

    for res in sorted_accepted:
        cand = res.entity
        # Check if cand overlaps with any already accepted candidate
        overlap_found = False
        for active in non_overlapping:
            act_cand = active.entity
            # Half-open interval overlap check
            if cand.start < act_cand.end and act_cand.start < cand.end:
                overlap_found = True
                break

        if not overlap_found:
            non_overlapping.append(res)

    # Sort the final output by start offset ascending for clean presentation
    non_overlapping.sort(key=lambda r: r.entity.start)
    return non_overlapping
