"""
GeM BidWatch — FilterMatcher
Checks if a normalized bid matches a monitoring profile.
Uses strict administrative state & city normalization, preventing empty string bugs
and cross-city false matches.
"""
import logging
import re
from typing import List, Optional
from app.schemas import BidCreate, ProfileOut
from app.services.location_normalizer import (
    resolve_state, clean_text, CITY_DISTRICT_TO_STATE,
    resolve_effective_bid_delivery_location, STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_CITY, STATUS_OUTSIDE_TARGET, STATUS_PARTIALLY_VERIFIED
)
from app.services.category_service import match_category

logger = logging.getLogger(__name__)


class MatchResult:
    def __init__(self, matched: bool, matched_keywords: List[str] = None, match_reason: str = ""):
        self.matched = matched
        self.matched_keywords = matched_keywords or []
        self.match_reason = match_reason

    def __bool__(self):
        return self.matched


def match_bid_to_profile(bid: BidCreate, profile: ProfileOut) -> MatchResult:
    """
    Returns MatchResult indicating whether bid satisfies profile criteria.

    Strict Matching Rules:
    1. Priority Delivery Location:
       Strictly prioritizes PDF delivery -> Structured delivery -> Consignee delivery.
       Never assumes buyer office is delivery location.
       For Bengaluru Urban profiles, bid must have STATUS_VERIFIED_BENGALURU_URBAN.
    2. State filter: If profile.state is set, bid delivery/consignee state must match canonical state.
    3. City filter: If profile.cities is set, bid delivery/consignee city must match at least one profile city.
    4. Target Category Filter: If profile.categories is set, canonical category_key must match.
    5. Keyword match: Category name must contain at least one configured keyword with word boundaries.
    6. Ministry filter: If configured, ministry_name must match allowed ministries.
    """
    # ─── 0. Priority Delivery Location Resolution ───────────────────────────────
    eff_status, eff_conf, eff_city, eff_dist, eff_state = resolve_effective_bid_delivery_location(bid)

    # ─── 1. State Filter ────────────────────────────────────────────────────────
    if profile.state:
        prof_state_clean = clean_text(profile.state)
        canonical_prof_state = resolve_state(prof_state_clean) or prof_state_clean.upper()

        bid_state_raw = eff_state or bid.consignee_state or (bid.buyer_state if not eff_city else None)
        bid_state_clean = clean_text(bid_state_raw)
        if not bid_state_clean:
            return MatchResult(False, [], "Bid state missing; rejected by state filter")

        canonical_bid_state = resolve_state(bid_state_clean) or bid_state_clean.upper()

        if canonical_prof_state != canonical_bid_state:
            return MatchResult(
                False, [],
                f"State mismatch: Profile requires '{canonical_prof_state}', bid is '{canonical_bid_state}'"
            )

    # ─── 2. City & Bengaluru Urban Filter ───────────────────────────────────────
    # Detect if profile specifically monitors Bengaluru / Bangalore
    prof_targets_bengaluru = False
    if profile.cities and len(profile.cities) > 0:
        for c in profile.cities:
            if re.search(r"\b(?:bengaluru|bangalore)\b", (c or "").lower()):
                prof_targets_bengaluru = True
                break

    if prof_targets_bengaluru:
        if eff_status not in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_CITY):
            return MatchResult(
                False, [],
                f"Location rejected: Delivery status is '{eff_status}' (Requires VERIFIED_BENGALURU_URBAN or VERIFIED_BENGALURU_CITY)"
            )
    if profile.cities and len(profile.cities) > 0:
        bid_city_raw = eff_city or bid.consignee_city or (bid.buyer_city if not eff_state else None)
        bid_city_clean = clean_text(bid_city_raw).lower()
        if not bid_city_clean:
            return MatchResult(False, [], "Bid city missing; rejected by city filter")

        # Canonical city lookup if available
        canonical_bid_city = bid_city_clean
        canonical_bid_dist = eff_dist.lower() if eff_dist else None
        if bid_city_clean in CITY_DISTRICT_TO_STATE:
            canonical_bid_city = CITY_DISTRICT_TO_STATE[bid_city_clean][0].lower()
            canonical_bid_dist = canonical_bid_dist or CITY_DISTRICT_TO_STATE[bid_city_clean][1].lower()

        city_matched = False
        for c in profile.cities:
            c_clean = clean_text(c).lower()
            if not c_clean:
                continue

            # Special case for Bengaluru Urban & City verified match
            if (
                re.search(r"\b(?:bengaluru|bangalore)\b", c_clean)
                and eff_status in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_CITY)
            ):
                city_matched = True
                break

            canonical_c = c_clean
            canonical_c_dist = None
            if c_clean in CITY_DISTRICT_TO_STATE:
                canonical_c = CITY_DISTRICT_TO_STATE[c_clean][0].lower()
                canonical_c_dist = CITY_DISTRICT_TO_STATE[c_clean][1].lower()

            if (
                canonical_c == canonical_bid_city
                or c_clean == bid_city_clean
                or (canonical_c_dist and canonical_c_dist == canonical_bid_dist)
                or bool(re.search(r"\b" + re.escape(c_clean) + r"\b", bid_city_clean))
                or bool(re.search(r"\b" + re.escape(bid_city_clean) + r"\b", c_clean))
            ):
                city_matched = True
                break

        if not city_matched:
            return MatchResult(
                False, [],
                f"City mismatch: Bid city '{bid_city_clean}' not in profile cities"
            )

    # ─── 3. Target Category Filter ──────────────────────────────────────────────
    if profile.categories and len(profile.categories) > 0:
        bid_cat_key = getattr(bid, "category_key", None)
        if not bid_cat_key and bid.category_name:
            bid_cat_key, _, _ = match_category(bid.category_name, bid.cat_id)

        allowed_cats = set()
        for pc in profile.categories:
            if not pc:
                continue
            pc_clean = pc.strip().upper()
            allowed_cats.add(pc_clean)
            res_id, _, _ = match_category(pc)
            if res_id:
                allowed_cats.add(res_id)

        if not bid_cat_key or bid_cat_key not in allowed_cats:
            return MatchResult(
                False, [],
                f"Category mismatch: Bid category '{bid_cat_key}' not in profile categories"
            )

    # ─── 4. Keyword Filter ──────────────────────────────────────────────────────
    matched_keywords = []
    if profile.keywords:
        category_text = bid.category_name or ""
        for kw in profile.keywords:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue

            if kw_clean in ("cartridge", "catridge"):
                pattern = re.compile(r'\bc(?:a|ar)tridge\b', re.IGNORECASE)
            elif kw_clean == "ink":
                pattern = re.compile(r'\bink(?:jet|s)?\b', re.IGNORECASE)
            elif kw_clean == "printer":
                pattern = re.compile(r'\bprinters?\b|\bmfp\b', re.IGNORECASE)
            else:
                pattern = re.compile(r'\b' + re.escape(kw_clean) + r'\b', re.IGNORECASE)

            if pattern.search(category_text):
                matched_keywords.append(kw_clean)

        if not matched_keywords:
            return MatchResult(False, [], "No category keywords matched")

    # ─── 4. Ministry Filter (optional) ──────────────────────────────────────────
    if profile.ministry_filter:
        ministry_lower = (bid.ministry_name or "").lower()
        allowed = [m.lower().strip() for m in profile.ministry_filter if m.strip()]
        if allowed and not any(m in ministry_lower for m in allowed):
            return MatchResult(False, [], "Ministry filter did not match")

    reason_parts = []
    if profile.categories:
        reason_parts.append(f"category: {bid_cat_key}")
    if matched_keywords:
        reason_parts.append(f"keywords: {', '.join(matched_keywords)}")
    reason_desc = " & ".join(reason_parts) if reason_parts else "all criteria"
    reason = f"Matched profile '{profile.name}' on {reason_desc}"
    return MatchResult(True, matched_keywords, reason)


def keywords_summary(matched_keywords: List[str]) -> str:
    return ", ".join(matched_keywords) if matched_keywords else ""
