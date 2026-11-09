"""
GeM BidWatch — Standalone Poll & Alert Runner
Can be executed as a one-shot task by any cloud cron (GitHub Actions, Linux cron, cron-job.org)
or continuously by the background worker.
"""
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, SessionLocal
from app.models import Profile, Bid, Alert
from app.workers.monitor_worker import run_profile_poll

def main():
    print("=== GeM BidWatch: Cloud Poll Run Starting ===")
    init_db()
    db = SessionLocal()

    # Ensure default Bangalore Toner & Printer profile exists
    profile = db.query(Profile).filter(Profile.name == "Bangalore - Toner & Printer").first()
    if not profile:
        profile = Profile(
            name="Bangalore - Toner & Printer",
            state="KARNATAKA",
            cities=["BANGALORE", "Bangalore Urban", "BENGALURU URBAN", "Bengaluru", "Bangalore Rural", "BENGALURU RURAL"],
            keywords=["toner", "cartridge", "printer", "ink"],
            is_active=True,
            poll_interval_seconds=300
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        print(f"Created default profile: {profile.name}")

    active_profiles = db.query(Profile).filter(Profile.is_active == True).all()
    print(f"Active profiles to check: {len(active_profiles)}")
    db.close()

    total_matches = 0
    for p in active_profiles:
        print(f"\n--- Checking Profile: {p.name} ({p.state}) ---")
        stats = run_profile_poll(p)
        print(f"Result: Fetched={stats['bids_fetched']} | New={stats['bids_new']} | Matched={stats['bids_matched']} | Success={stats['success']}")
        total_matches += stats['bids_matched']

    print(f"\n=== Completed. Total New Alerts: {total_matches} ===")

if __name__ == "__main__":
    main()
