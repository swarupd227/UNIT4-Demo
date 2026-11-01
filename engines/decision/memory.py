"""What mapping memory would propose first for the next item with the same pattern.

Plain code over past decisions: an outcome people rejected more often than approved is not offered.
"""

from collections import Counter
from collections.abc import Iterable

BASE_CONFIDENCE = 70
CONFIDENCE_PER_APPROVAL = 5
MAX_CONFIDENCE = 95


def next_proposal(history: Iterable[tuple[str, str]]) -> tuple[str | None, int | None]:
    """Takes (outcome, review_status) pairs and returns the first proposal and its confidence."""
    net: Counter[str] = Counter()
    for outcome, review_status in history:
        if review_status == "approved":
            net[outcome] += 1
        elif review_status == "rejected":
            net[outcome] -= 1
    supported = sorted(
        ((count, outcome) for outcome, count in net.items() if count > 0),
        key=lambda entry: (-entry[0], entry[1]),
    )
    if not supported:
        return None, None
    count, outcome = supported[0]
    return outcome, min(BASE_CONFIDENCE + CONFIDENCE_PER_APPROVAL * count, MAX_CONFIDENCE)
