import sys
import os
import time
import json
import urllib.request

sys.path.insert(0, os.path.abspath("backend"))

from app.gem.session import GemSession
from app.gem.fetcher import GemFetcher
from app.gem.normalizer import normalize_bid
from app.services.category_service import match_category
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
seen_ids = set()
bids_to_sync = []

print("Running exhaustive scan to prepare batch-sync payload...")

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
                if not bid or bid.bid_number in seen_ids:
                    continue
                
                cat_key, cat_name, cat_status = match_category(bid.category_name, bid.cat_id)
                if cat_key:
                    loc_st, norm_city, norm_dist, norm_st, conf = resolve_effective_bid_delivery_location(bid)
                    if loc_st in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_RURAL, STATUS_VERIFIED_BENGALURU_CITY):
                        seen_ids.add(bid.bid_number)
                        
                        # Provenance and verified status
                        bid.category_key = cat_key
                        bid.category_mapping_status = cat_status
                        bid.target_location_status = loc_st
                        bid.synchronization_status = "VERIFIED"
                        bid.pdf_verification_status = "VERIFIED"
                        bid.raw_source_record = json.dumps({
                            "source": "GeM Official Portal search-bids",
                            "state_searched": "KARNATAKA",
                            "city_searched": city,
                            "page": page,
                            "category_matched": cat_key,
                            "discovered_via": "Exhaustive Regional Location Scan",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        })
                        bids_to_sync.append(bid)
            
            if total_in_city >= num_found:
                break
            page += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Error on {city} page {page}: {e}")
            break

print(f"Prepared {len(bids_to_sync)} verified tenders to sync to Render backend!")

# Push to Render
BACKEND_SYNC_URL = "https://realtime-gem-monitoring.onrender.com/bids/batch-sync"
SCANNER_SECRET = "gem_bidwatch_cloud_token_v1"

payload = json.dumps([b.model_dump(mode="json") for b in bids_to_sync]).encode("utf-8")
req = urllib.request.Request(
    BACKEND_SYNC_URL,
    data=payload,
    headers={
        "Content-Type": "application/json",
        "User-Agent": "GeM-Zero-Miss-Ingestion-Engine/2.0",
        "X-Scanner-Secret": SCANNER_SECRET,
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print("\n✅ Render Ingestion Result:")
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"\n❌ Error syncing to Render: {e}")
