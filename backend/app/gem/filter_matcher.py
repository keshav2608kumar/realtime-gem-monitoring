"""
GeM BidWatch — FilterMatcher
Checks if a normalized bid matches a monitoring profile.
All matching is case-insensitive.
"""
import logging
from typing import List, Optional
from app.schemas import BidCreate, ProfileOut

logger = logging.getLogger(__name__)


class MatchResult:
    def __init__(self, matched: bool, matched_keywords: List[str] = None):
        self.matched = matched
        self.matched_keywords = matched_keywords or []

    def __bool__(self):
        return self.matched


def match_bid_to_profile(bid: BidCreate, profile: ProfileOut) -> MatchResult:
    """
    Returns MatchResult indicating whether bid matches profile filters.

    Matching rules:
    1. Keyword match: at least one keyword in category_name (if keywords defined)
    2. Ministry filter: if set, ministry_name must be in list (optional)
    3. Value range: skip (GeM search doesn't return bid value in listing)
    """
    matched_keywords = []

    # --- Keyword Filter ---
    if profile.keywords:
        category_text = (bid.category_name or "").lower()
        for kw in profile.keywords:
            if kw.lower() in category_text:
                matched_keywords.append(kw)

        if not matched_keywords:
            return MatchResult(False)

    # --- Ministry Filter (optional) ---
    if profile.ministry_filter:
        ministry_lower = (bid.ministry_name or "").lower()
        allowed = [m.lower() for m in profile.ministry_filter]
        if not any(m in ministry_lower for m in allowed):
            return MatchResult(False)

    return MatchResult(True, matched_keywords)


def keywords_summary(matched_keywords: List[str]) -> str:
    return ", ".join(matched_keywords) if matched_keywords else ""
