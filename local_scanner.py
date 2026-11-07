"""
GeM BidWatch — Domestic Indian Scanner & Sync Agent
Runs on any Windows/Mac/Linux computer in India (home/office Wi-Fi, Jio, Airtel).
Because GeM portal firewall blocks non-Indian IPs, this domestic scanner:
1. Polls GeM directly with zero firewall restrictions.
2. Immediately triggers local loud sound & alarm popup when matching tender appears.
3. Automatically syncs all discovered tenders & alerts to the Cloud Web Dashboard (Render).
"""

import sys
import os
import time
import json
import urllib.request
import ssl
from datetime import datetime

# Safe UTF-8 console output for Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend directory relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "backend"))

from app.gem.session import GemSession
from app.gem.fetcher import GemFetcher
from app.gem.normalizer import normalize_bid

CLOUD_SYNC_URL = "https://realtime-gem-monitoring.onrender.com/bids/batch-sync"
POLL_INTERVAL_SECONDS = 300  # 5 minutes

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def play_local_alarm():
    """Play loud local siren sound on Windows."""
    try:
        import winsound
        for _ in range(5):
            winsound.Beep(1200, 300)
            winsound.Beep(800, 300)
    except Exception:
        print("\a" * 5)  # Terminal bell fallback


def sync_bids_to_cloud(bids_list: list):
    """Uploads normalized bids to the Render cloud backend."""
    if not bids_list:
        return
    try:
        payload = json.dumps([b.model_dump(mode="json") for b in bids_list]).encode("utf-8")
        req = urllib.request.Request(
            CLOUD_SYNC_URL,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "GeM-India-Agent/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  ☁️ Cloud Sync: {data.get('bids_inserted', 0)} new bids saved, {data.get('alerts_created', 0)} new alerts created.")
    except Exception as e:
        print(f"  ⚠️ Cloud sync notice: {e} (Local monitoring unaffected)")


import re

def run_scanner_cycle(session: GemSession, fetcher: GemFetcher):
    print("\n" + "="*65)
    print(f"🔍 GeM Scan Cycle Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*65)

    cities = ["BANGALORE", "Bangalore Urban", "BENGALURU URBAN", "Bengaluru"]
    keywords = ["toner", "cartridge", "printer", "ink"]
    target_re = re.compile(r'\b(printer|toner|c(?:a|ar)tridge|ink(?:jet|s)?|mfp)\b', re.IGNORECASE)

    all_normalized_bids = []
    seen_ids = set()
    matched_tenders = []

    # 1. Location-based search (Karnataka / Bangalore)
    for city in cities:
        try:
            raw_bids = fetcher.fetch_all_pages(state="KARNATAKA", city=city, max_pages=3)
            print(f"  [{city}]: Found {len(raw_bids)} recent tender(s)")
            for raw in raw_bids:
                bid = normalize_bid(raw)
                if not bid or bid.gem_bid_id in seen_ids:
                    continue
                # Only keep genuine printer/cartridge/toner/ink tenders!
                if target_re.search(bid.category_name or ""):
                    seen_ids.add(bid.gem_bid_id)
                    all_normalized_bids.append(bid)
                    matched_tenders.append((bid, ["target match"]))
        except Exception as e:
            print(f"  ⚠️ Error polling city {city}: {e}")

    # 2. Targeted Keyword Catalog Polling (Toner, Cartridge, Printer, Ink)
    print("\n🔍 Polling GeM Real-Time Catalog for Target Keywords...")
    for kw in keywords:
        try:
            kw_raw_bids, num_found = fetcher.fetch_bids_by_keyword(keyword=kw, page=1)
            print(f"  [{kw.upper()}]: Found {num_found} active tender(s) on GeM")
            for raw in kw_raw_bids[:10]:
                bid = normalize_bid(raw)
                if not bid or bid.gem_bid_id in seen_ids:
                    continue
                if target_re.search(bid.category_name or ""):
                    seen_ids.add(bid.gem_bid_id)
                    all_normalized_bids.append(bid)
                    matched_tenders.append((bid, [kw]))
        except Exception as e:
            print(f"  ⚠️ Error polling keyword {kw}: {e}")

    print(f"\n📊 Total Tenders Extracted: {len(all_normalized_bids)}")
    print(f"🚨 Matching Target Tenders: {len(matched_tenders)}")

    if matched_tenders:
        print("\n" + "!"*65)
        print("🚨🚨 EMERGENCY GeM BID MATCH DETECTED! 🚨🚨")
        print("!"*65)
        for bid, kws in matched_tenders:
            print(f"  TENDER NO: {bid.bid_number}")
            print(f"  CATEGORY:  {bid.category_name}")
            print(f"  LOCATION:  {bid.consignee_city}, {bid.consignee_state}")
            print(f"  MATCHED:   {', '.join(kws)}")
            print(f"  PDF LINK:  {bid.bid_url}")
            print("-" * 65)
        play_local_alarm()

    # Sync to Cloud
    print("\n☁️ Syncing with Cloud Dashboard...")
    sync_bids_to_cloud(all_normalized_bids)


def main():
    print("="*65)
    print("  🚨 GeM BidWatch — Domestic Indian 24/7 Scanner Agent 🚨")
    print("  Target: Bangalore / Karnataka — Toner, Cartridge, Printer")
    print("="*65)
    session = GemSession()
    fetcher = GemFetcher(session)

    while True:
        try:
            run_scanner_cycle(session, fetcher)
        except Exception as e:
            print(f"❌ Error in scan cycle: {e}")

        print(f"\n⏳ Next scan in {POLL_INTERVAL_SECONDS // 60} minutes... (Press Ctrl+C to stop)")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
