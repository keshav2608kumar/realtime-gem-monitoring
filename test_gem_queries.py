import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.gem.session import GemSession
from app.gem.fetcher import GemFetcher

session = GemSession()
session.refresh()
print(f"Session CSRF obtained: {bool(session._csrf_token)}")

fetcher = GemFetcher(session)

keywords = [
    "Toner Cartridges",
    "Scanner",
    "Multifunction Printer",
    "Computer Printer",
    "Desktop Computer",
    "Laptop",
    "toner",
    "printer"
]

for kw in keywords:
    try:
        bids, total = fetcher.fetch_bids_by_keyword(kw, page=1)
        print(f"Keyword '{kw}': total={total}, page 1 len={len(bids)}")
    except Exception as e:
        print(f"Keyword '{kw}': error {e}")
