"""
GeM BidWatch — FilterMatcher
Checks if a normalized bid matches a monitoring profile.
All matching is case-insensitive.
"""
import logging
import re
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
    1. State filter: consignee_state must match profile.state (if defined)
    2. City filter: consignee_city must match at least one profile.cities (if defined)
    3. Keyword match: at least one keyword in category_name with word-boundary
       awareness to prevent false positives (e.g. 'ink' matching 'Drinking water').
    4. Ministry filter: if set, ministry_name must be in list (optional)
    """
    # --- Location Filter: State ---
    if profile.state:
        bid_state = (bid.consignee_state or "").strip().lower()
        prof_state = profile.state.strip().lower()
        if prof_state and prof_state != bid_state and prof_state not in bid_state:
            return MatchResult(False)

    # --- Location Filter: Cities ---
    if profile.cities:
        bid_city = (bid.consignee_city or "").strip().lower()
        city_matched = False
        for c in profile.cities:
            c_clean = c.strip().lower()
            if c_clean and (c_clean == bid_city or c_clean in bid_city or bid_city in c_clean):
                city_matched = True
                break
        if not city_matched:
            return MatchResult(False)

    matched_keywords = []

    # --- Keyword Filter ---
    if profile.keywords:
        category_text = bid.category_name or ""
        for kw in profile.keywords:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue

            # Use word boundary at beginning to avoid false positives like 'drinking' for 'ink'
            pattern = re.compile(r'\b' + re.escape(kw_clean), re.IGNORECASE)
            if pattern.search(category_text):
                matched_keywords.append(kw_clean)

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
