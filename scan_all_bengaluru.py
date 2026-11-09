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

cities = ["BANGALORE", "BANGALORE RURAL", "BANGALORE URBAN", "BENGALURU", "BENGALURU URBAN"]
all_matches = []
seen_bid_numbers = set()

print("Starting deep scan of all GeM tenders in Bengaluru region...")

for city in cities:
    page = 1
    total_in_city = 0
    matches_in_city = 0
    while True:
        try:
            raw_bids, num_found = fetcher.fetch_bids_by_location("KARNATAKA", city, page=page)
            if not raw_bids:
                break
            total_in_city += len(raw_bids)
            for raw in raw_bids:
                bid = normalize_bid(raw)
                if not bid or bid.bid_number in seen_bid_numbers:
                    continue
                
                cat_key, cat_name, cat_status = match_category(bid.category_name, bid.cat_id)
                if cat_key:
                    loc_st, _, _, _, _ = resolve_effective_bid_delivery_location(bid)
                    seen_bid_numbers.add(bid.bid_number)
                    matches_in_city += 1
                    all_matches.append({
                        "bid_number": bid.bid_number,
                        "category_key": cat_key,
                        "category_name": bid.category_name,
                        "city": city,
                        "loc_st": loc_st,
                        "end_date": str(bid.end_date),
                    })
            
            if total_in_city >= num_found:
                break
            page += 1
            time.sleep(0.1)  # small delay
        except Exception as e:
            print(f"Error on {city} page {page}: {e}")
            break
    print(f"Finished {city}: total tenders scanned={total_in_city}/{num_found}, target category matches={matches_in_city}")

print(f"\n==========================================")
print(f"TOTAL MATCHING TENDERS DISCOVERED: {len(all_matches)}")
print(f"==========================================")
for m in all_matches[:20]:
    print(f"- {m['bid_number']} | {m['category_key']} | {m['city']} | {m['loc_st']} | {m['end_date']}")
