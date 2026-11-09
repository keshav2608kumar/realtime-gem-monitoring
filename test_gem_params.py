import sys
import os
import json
sys.path.insert(0, os.path.abspath("backend"))

from app.gem.session import GemSession

session = GemSession()
session.refresh()

# Let's inspect search-bids with different payload combinations
# 1. searchType = "con" with city and keyword or category
print("--- Test 1: search-bids with state, city and keyword ---")
payload = {
    "searchType": "con",
    "state_name_con": "KARNATAKA",
    "city_name_con": "BANGALORE",
    "page": 1,
}
data = session.post("https://bidplus.gem.gov.in/search-bids", payload)
resp = data.get("response", {}).get("response", {})
print("numFound without keyword:", resp.get("numFound"))

# Let's see if search-bids accepts searchBid or keyword
payload_kw = {
    "searchType": "con",
    "state_name_con": "KARNATAKA",
    "city_name_con": "BANGALORE",
    "searchBid": "printer",
    "page": 1,
}
data_kw = session.post("https://bidplus.gem.gov.in/search-bids", payload_kw)
resp_kw = data_kw.get("response", {}).get("response", {})
print("numFound with searchBid='printer':", resp_kw.get("numFound"))

# Let's see all-bids-data with filter for state or city
print("\n--- Test 2: all-bids-data with state filter ---")
payload_all = {
    "page": 1,
    "param": {"searchBid": "printer", "searchType": "fullText"},
    "filter": {
        "bidStatusType": "ongoing_bids",
        "byType": "all",
        "sort": "Bid-End-Date-Oldest",
        "state": "KARNATAKA"
    }
}
data_all = session.post("https://bidplus.gem.gov.in/all-bids-data", payload_all)
resp_all = data_all.get("response", {}).get("response", {})
print("numFound in all-bids-data for 'printer' with state='KARNATAKA':", resp_all.get("numFound"))
docs = resp_all.get("docs", [])
if docs:
    print("Sample doc keys:", list(docs[0].keys())[:10])
    print("Sample b_category_name:", docs[0].get("b_category_name"))
