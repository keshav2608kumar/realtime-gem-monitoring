"""
GeM BidWatch — Automatic Startup Seeder
Guarantees clean startup without empty state or false defaults.
All baseline bids are explicitly marked as data_source_classification='IMPORTED'
with verified administrative locations.
"""
import os
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Profile, Bid, Alert
from app.gem.filter_matcher import match_bid_to_profile, keywords_summary
from app.schemas import ProfileOut, BidCreate
from app.services.location_normalizer import normalize_location
from app.services.datetime_service import parse_datetime
from app.services.bid_status_service import calculate_bid_status
from app.services.category_service import match_category

logger = logging.getLogger(__name__)


def seed_initial_data(db: Session):
    """Seed Profile 1 and verified baseline bids/alerts."""
    try:
        # 1. Ensure Profile 1 exists
        profile = db.query(Profile).filter(Profile.name == "Bangalore - Toner & Printer").first()
        if not profile:
            profile = Profile(
                name="Bangalore - Toner & Printer",
                state="KARNATAKA",
                cities=["BANGALORE", "Bangalore Urban", "BENGALURU URBAN", "Bengaluru"],
                keywords=["toner", "cartridge", "printer", "ink"],
                is_active=True,
                poll_interval_seconds=300
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            logger.info("Auto-seeded Profile 1: Bangalore - Toner & Printer")

        # 2. Load and upsert baseline bids
        json_path = os.path.join(os.path.dirname(__file__), "baseline_bids.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                baseline_bids = json.load(f)

            for b in baseline_bids:
                start_dt = parse_datetime(b.get("start_date"))
                end_dt = parse_datetime(b.get("end_date"))
                raw_stat = b.get("status", 1)
                bid_status = calculate_bid_status(end_dt, raw_stat)

                loc = normalize_location(
                    raw_text=b.get("dept_name"),
                    city_hint=b.get("consignee_city"),
                    state_hint=b.get("consignee_state"),
                )

                # Resolve category key & status
                cat_key = b.get("category_key")
                cat_status = b.get("category_mapping_status")
                if not cat_key:
                    cat_key, _, cat_status = match_category(b.get("category_name"), b.get("cat_id"))

                existing = db.query(Bid).filter(
                    (Bid.bid_number == b["bid_number"]) | (Bid.gem_bid_id == b["gem_bid_id"])
                ).first()

                if existing:
                    existing.gem_bid_id = b["gem_bid_id"]
                    existing.bid_number = b["bid_number"]
                    existing.category_name = b.get("category_name")
                    existing.category_key = cat_key
                    existing.category_mapping_status = cat_status or "UNKNOWN"
                    existing.dept_name = b.get("dept_name")
                    existing.ministry_name = b.get("ministry_name")
                    existing.quantity = b.get("quantity")
                    existing.start_date = start_dt
                    existing.end_date = end_dt
                    existing.bid_status = bid_status
                    existing.consignee_city = loc.city
                    existing.consignee_state = loc.state
                    existing.consignee_district = loc.district
                    existing.location_verification_status = loc.confidence
                    existing.data_source_classification = "IMPORTED"
                    existing.bid_url = b.get("bid_url")
                    if b.get("pdf_delivery_address"):
                        existing.pdf_delivery_address = b.get("pdf_delivery_address")
                        existing.pdf_delivery_city = b.get("pdf_delivery_city")
                        existing.pdf_delivery_district = b.get("pdf_delivery_district")
                        existing.pdf_delivery_state = b.get("pdf_delivery_state")
                        existing.pdf_delivery_pincode = b.get("pdf_delivery_pincode")
                        existing.pdf_delivery_consignee = b.get("pdf_delivery_consignee")
                        existing.pdf_delivery_org = b.get("pdf_delivery_org")
                        existing.pdf_page_number = b.get("pdf_page_number")
                        existing.pdf_extraction_method = b.get("pdf_extraction_method", "PDF_TEXT")
                        existing.pdf_confidence_score = b.get("pdf_confidence_score")
                        existing.pdf_verification_status = b.get("pdf_verification_status", "UNKNOWN")
                else:
                    new_bid = Bid(
                        gem_bid_id=b["gem_bid_id"],
                        bid_number=b["bid_number"],
                        bid_number_parent=b.get("bid_number_parent"),
                        category_name=b.get("category_name"),
                        category_key=cat_key,
                        category_mapping_status=cat_status or "UNKNOWN",
                        quantity=b.get("quantity"),
                        bid_type=b.get("bid_type", 1),
                        status=raw_stat,
                        is_high_value=bool(b.get("is_high_value", False)),
                        ministry_name=b.get("ministry_name"),
                        dept_name=b.get("dept_name"),
                        start_date=start_dt,
                        end_date=end_dt,
                        bid_status=bid_status,
                        consignee_state=loc.state,
                        consignee_city=loc.city,
                        consignee_district=loc.district,
                        raw_location_text=loc.raw_text,
                        location_verification_status=loc.confidence,
                        data_source_classification="IMPORTED",
                        bid_url=b.get("bid_url"),
                        cat_id=b.get("cat_id"),
                        pdf_delivery_address=b.get("pdf_delivery_address"),
                        pdf_delivery_city=b.get("pdf_delivery_city"),
                        pdf_delivery_district=b.get("pdf_delivery_district"),
                        pdf_delivery_state=b.get("pdf_delivery_state"),
                        pdf_delivery_pincode=b.get("pdf_delivery_pincode"),
                        pdf_delivery_consignee=b.get("pdf_delivery_consignee"),
                        pdf_delivery_org=b.get("pdf_delivery_org"),
                        pdf_page_number=b.get("pdf_page_number"),
                        pdf_extraction_method=b.get("pdf_extraction_method", "PDF_TEXT"),
                        pdf_confidence_score=b.get("pdf_confidence_score"),
                        pdf_verification_status=b.get("pdf_verification_status", "UNKNOWN"),
                    )
                    db.add(new_bid)

            db.commit()
            logger.info(f"Verified {len(baseline_bids)} baseline tenders in database")

        # 3. Create alerts for matching bids
        active_profiles = db.query(Profile).filter(Profile.is_active == True).all()
        all_bids = db.query(Bid).all()
        created_alerts = 0
        for prof in active_profiles:
            p_out = ProfileOut(
                id=prof.id,
                name=prof.name,
                is_active=prof.is_active,
                state=prof.state,
                cities=prof.cities,
                keywords=prof.keywords,
                poll_interval_seconds=prof.poll_interval_seconds,
                created_at=prof.created_at or datetime.now(timezone.utc),
            )
            for b in all_bids:
                b_create = BidCreate(
                    gem_bid_id=b.gem_bid_id,
                    bid_number=b.bid_number,
                    category_name=b.category_name,
                    consignee_state=b.consignee_state,
                    consignee_city=b.consignee_city,
                    dept_name=b.dept_name,
                    ministry_name=b.ministry_name,
                )
                match = match_bid_to_profile(b_create, p_out)
                if match.matched:
                    already = db.query(Alert).filter(Alert.profile_id == prof.id, Alert.bid_id == b.id).first()
                    if not already:
                        alert = Alert(
                            profile_id=prof.id,
                            bid_id=b.id,
                            matched_keywords=keywords_summary(match.matched_keywords),
                            match_reason=match.match_reason,
                            status="NEW",
                            acknowledged=False,
                            notification_sent=False,
                        )
                        db.add(alert)
                        created_alerts += 1
        db.commit()
        if created_alerts > 0:
            logger.info(f"Created {created_alerts} new alerts for matching bids")
    except Exception as e:
        logger.error(f"Error during auto-seeding: {e}", exc_info=True)
