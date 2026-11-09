import sys
import os
import json
sys.path.insert(0, os.path.abspath("backend"))

from app.gem.session import GemSession
from app.gem.fetcher import GemFetcher
from app.gem.normalizer import normalize_bid
from app.services.category_service import match_category
from app.services.location_normalizer import resolve_effective_bid_delivery_location

session = GemSession()
session.refresh()
fetcher = GemFetcher(session)

cities = ["BANGALORE", "BANGALORE RURAL", "BANGALORE URBAN", "BENGALURU", "BENGALURU URBAN"]
all_matches = []
seen_bid_numbers = set()

for city in cities:
    page = 1
    total_in_city = 0
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
                    all_matches.append({
                        "bid_number": bid.bid_number,
                        "category_key": cat_key,
                        "category_name": bid.category_name,
                        "city_searched": city,
                        "buyer_city": bid.buyer_city,
                        "consignee_city": bid.consignee_city,
                        "delivery_city": bid.delivery_city,
                        "location_status": loc_st,
                        "start_date": str(bid.start_date),
                        "end_date": str(bid.end_date),
                        "status": bid.status,
                    })
            
            if total_in_city >= num_found:
                break
            page += 1
        except Exception as e:
            break

print(f"Total verified matches: {len(all_matches)}")
with open("discovered_real_bids.json", "w", encoding="utf-8") as f:
    json.dump(all_matches, f, indent=2)
print("Saved to discovered_real_bids.json")
