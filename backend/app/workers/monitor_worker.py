"""
GeM BidWatch — Monitor Worker
Core polling loop: fetches bids → normalizes locations → deduplicates → matches → triggers alerts.
"""
import logging
import time
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Bid, Profile, Alert, MonitorHealth
from app.schemas import BidCreate, ProfileOut
from app.gem import GemSession, GemFetcher, normalize_bid, match_bid_to_profile, MatchResult
from app.gem.filter_matcher import keywords_summary
from app.services.location_normalizer import normalize_location
from app.services.datetime_service import UTC_TZ

logger = logging.getLogger(__name__)

# Single shared session (auto-refreshes on 403)
_gem_session = GemSession()


def _get_or_create_bid(db: Session, bid_data: BidCreate) -> tuple:
    """
    Insert or update bid. Returns (db_bid, is_new).
    Uses gem_bid_id or bid_number as deduplication keys.
    """
    existing = db.query(Bid).filter(
        (Bid.gem_bid_id == bid_data.gem_bid_id) | (Bid.bid_number == bid_data.bid_number)
    ).first()

    if existing:
        # Update with newly observed fields without destroying historical data
        if bid_data.end_date:
            existing.end_date = bid_data.end_date
        if bid_data.start_date:
            existing.start_date = bid_data.start_date
        if bid_data.bid_status:
            existing.bid_status = bid_data.bid_status
        if bid_data.category_name:
            existing.category_name = bid_data.category_name
        if bid_data.dept_name:
            existing.dept_name = bid_data.dept_name
        if bid_data.consignee_city and bid_data.location_verification_status in ("VERIFIED", "NORMALIZED"):
            existing.consignee_city = bid_data.consignee_city
            existing.consignee_state = bid_data.consignee_state
            existing.consignee_district = bid_data.consignee_district
            existing.location_verification_status = bid_data.location_verification_status
        return existing, False

    new_bid = Bid(**bid_data.model_dump())
    db.add(new_bid)
    db.flush()  # get ID without committing
    return new_bid, True


def _alert_exists(db: Session, profile_id: int, bid_id: int) -> bool:
    return db.query(Alert).filter(
        Alert.profile_id == profile_id,
        Alert.bid_id == bid_id
    ).first() is not None


def _create_alert(db: Session, profile_id: int, bid_id: int, match: MatchResult) -> Alert:
    alert = Alert(
        profile_id=profile_id,
        bid_id=bid_id,
        matched_keywords=keywords_summary(match.matched_keywords),
        match_reason=match.match_reason,
        status="NEW",
        acknowledged=False,
        notification_sent=False,
    )
    db.add(alert)
    db.flush()
    return alert


def run_profile_poll(profile: Profile) -> dict:
    """
    Poll GeM for one profile. Returns stats dict.
    """
    db: Session = SessionLocal()
    start_time = time.time()

    stats = {
        "profile_id": profile.id,
        "profile_name": profile.name,
        "bids_fetched": 0,
        "bids_new": 0,
        "bids_matched": 0,
        "success": False,
        "error_message": None,
    }
    _pending_alert_ids = []

    try:
        fetcher = GemFetcher(_gem_session)
        cities = profile.cities or [""]  # empty string = whole state

        all_raw_bids = []
        for city in cities:
            logger.info(f"[{profile.name}] Polling {profile.state}/{city or 'ALL'}")
            raw_bids = fetcher.fetch_all_pages(state=profile.state, city=city, max_pages=5)
            all_raw_bids.extend(raw_bids)

        stats["bids_fetched"] = len(all_raw_bids)

        profile_schema = ProfileOut(
            id=profile.id,
            name=profile.name,
            is_active=profile.is_active,
            state=profile.state,
            cities=profile.cities,
            keywords=profile.keywords,
            min_value=profile.min_value,
            max_value=profile.max_value,
            ministry_filter=profile.ministry_filter,
            poll_interval_seconds=profile.poll_interval_seconds,
            created_at=profile.created_at or datetime.now(timezone.utc),
        )

        seen_in_run = set()

        for raw in all_raw_bids:
            bid_data = normalize_bid(raw)
            if not bid_data:
                continue

            # Skip duplicates within same polling run
            if bid_data.gem_bid_id in seen_in_run:
                continue
            seen_in_run.add(bid_data.gem_bid_id)

            # Dedup + store
            db_bid, is_new = _get_or_create_bid(db, bid_data)
            if is_new:
                stats["bids_new"] += 1

            # Match against profile
            match = match_bid_to_profile(bid_data, profile_schema)
            if match.matched:
                if not _alert_exists(db, profile.id, db_bid.id):
                    alert = _create_alert(db, profile.id, db_bid.id, match)
                    stats["bids_matched"] += 1
                    logger.info(
                        f"[{profile.name}] 🔔 NEW MATCH: {bid_data.bid_number} | "
                        f"Cat: {bid_data.category_name} | Keywords: {match.matched_keywords}"
                    )
                    _pending_alert_ids.append(alert.id)

        db.commit()
        stats["success"] = True
        logger.info(
            f"[{profile.name}] ✅ Poll done. "
            f"Fetched={stats['bids_fetched']} New={stats['bids_new']} Matched={stats['bids_matched']}"
        )

        # Dispatch FCM for newly created alerts
        if _pending_alert_ids:
            from app.notifications.fcm_sender import send_alert_notifications
            for aid in _pending_alert_ids:
                try:
                    send_alert_notifications(aid)
                except Exception as fcm_err:
                    logger.error(f"FCM dispatch failed for alert {aid}: {fcm_err}")

    except Exception as e:
        db.rollback()
        stats["error_message"] = str(e)
        logger.error(f"[{profile.name}] ❌ Poll failed: {e}", exc_info=True)
    finally:
        # Save health record
        duration = int(time.time() - start_time)
        health = MonitorHealth(
            profile_id=stats["profile_id"],
            profile_name=stats["profile_name"],
            bids_fetched=stats["bids_fetched"],
            bids_new=stats["bids_new"],
            bids_matched=stats["bids_matched"],
            success=stats["success"],
            error_message=stats["error_message"],
            duration_seconds=duration,
        )
        try:
            db.add(health)
            db.commit()
        except Exception:
            db.rollback()
        db.close()

    return stats


def poll_all_active_profiles():
    """
    Called by APScheduler. Polls all active profiles.
    """
    db = SessionLocal()
    try:
        profiles = db.query(Profile).filter(Profile.is_active == True).all()
        logger.info(f"Starting poll cycle for {len(profiles)} active profile(s)...")
    finally:
        db.close()

    for profile in profiles:
        try:
            run_profile_poll(profile)
        except Exception as e:
            logger.error(f"Unexpected error polling profile {profile.id}: {e}", exc_info=True)
