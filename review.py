"""Forgotten-curve algorithm and blind-box review logic."""

import random
from database import get_due_problems

REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30]


def draw_blindbox(n: int = 5):
    """Draw n random problems from the due pool."""
    due = get_due_problems()
    if not due:
        return []
    n = min(n, len(due))
    return random.sample(due, n)


def compute_next_stage(current_stage: int, self_rating: int) -> int:
    if self_rating == 1:
        return max(0, current_stage - 1)
    elif self_rating == 3:
        return min(5, current_stage + 1)
    return current_stage


def stage_to_status(stage: int) -> str:
    if stage >= 5:
        return "已吃透"
    elif stage >= 2:
        return "模糊"
    return "未掌握"
