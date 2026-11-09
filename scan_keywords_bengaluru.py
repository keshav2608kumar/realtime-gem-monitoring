import sys
import os
import time
sys.path.insert(0, os.path.abspath("backend"))

from app.gem.session import GemSession
from app.gem.fetcher import GemFetcher
from app.gem.normalizer import normalize_bid
from app.services.category_service import match_category, TARGET_CATEGORIES
from app.services.location_normalizer import (
    resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_RURAL,
    STATUS_VERIFIED_BENGALURU_CITY,
)

session = GemSession()
session.refresh()
fetcher = GemFetcher(session)

# Target search queries for the 7 categories
category_queries = [
    "Toner Cartridges",
    "Scanner",
    "Multifunction Printer",
    "Computer Printer",
    "Desktop Computer",
    "Laptop",
]

keyword_matches = []
seen_bids = set()

for kw in category_queries:
    page = 1
    total_fetched = 0
    matched_for_kw = 0
    while True:
        try:
            raw_bids, num_found = fetcher.fetch_bids_by_keyword(kw, page=page)
            if not raw_bids:
                break
            total_fetched += len(raw_bids)
            for raw in raw_bids:
                bid = normalize_bid(raw)
                if not bid or bid.bid_number in seen_bids:
                    continue
                loc_st, _, _, _, _ = resolve_effective_bid_delivery_location(bid)
                if loc_st in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_RURAL, STATUS_VERIFIED_BENGALURU_CITY):
                    cat_key, cat_name, _ = match_category(bid.category_name, bid.cat_id)
                    seen_bids.add(bid.bid_number)
                    matched_for_kw += 1
                    keyword_matches.append({
                        "bid_number": bid.bid_number,
                        "category_key": cat_key or bid.category_name,
                        "kw": kw,
                        "loc_st": loc_st,
                    })
            if total_fetched >= num_found or page >= 30:  # scan up to 30 pages (300 bids per category)
                break
            page += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Error on {kw} page {page}: {e}")
            break
    print(f"Keyword '{kw}': scanned {total_fetched}/{num_found} bids, Bengaluru matches = {matched_for_kw}")

print(f"\nTotal Bengaluru matches from category keyword searches: {len(keyword_matches)}")
