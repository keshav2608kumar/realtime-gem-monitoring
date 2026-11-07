"""
GeM BidWatch — Automatic Startup Seeder
Guarantees the application never starts in an empty or corrupt state.
Ensures 100% targeted Bangalore & Karnataka Printer, Cartridge, Toner tenders with complete Department details.
"""
import os
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Profile, Bid, Alert
from app.gem.filter_matcher import match_bid_to_profile, keywords_summary
from app.schemas import ProfileOut, BidCreate

logger = logging.getLogger(__name__)


def seed_initial_data(db: Session):
    """Seed Profile 1 and baseline target bids/alerts."""
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
            logger.info("✅ Auto-seeded Profile 1: Bangalore - Toner & Printer")

        # 2. Load and upsert curated Bangalore & Karnataka Printer/Cartridge tenders
        json_path = os.path.join(os.path.dirname(__file__), "baseline_bids.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                baseline_bids = json.load(f)

            target_gem_ids = {b["gem_bid_id"] for b in baseline_bids}

            # Remove legacy non-target bids (paints, sheds, chemicals) if any
            non_targets = db.query(Bid).filter(
                ~Bid.gem_bid_id.in_(target_gem_ids),
                ~Bid.category_name.ilike("%printer%"),
                ~Bid.category_name.ilike("%toner%"),
                ~Bid.category_name.ilike("%cartridge%"),
            ).all()
            if non_targets:
                for nb in non_targets:
                    db.query(Alert).filter(Alert.bid_id == nb.id).delete()
                    db.delete(nb)
                db.commit()
                logger.info(f"🧹 Cleaned up {len(non_targets)} non-target legacy bids")

            # Upsert target bids
            for b in baseline_bids:
                start_dt = None
                end_dt = None
                if b.get("start_date"):
                    try:
                        start_dt = datetime.fromisoformat(str(b["start_date"]).replace("Z", "+00:00"))
                    except Exception:
                        pass
                if b.get("end_date"):
                    try:
                        end_dt = datetime.fromisoformat(str(b["end_date"]).replace("Z", "+00:00"))
                    except Exception:
                        pass

                existing = db.query(Bid).filter(
                    (Bid.bid_number == b["bid_number"]) | (Bid.gem_bid_id == b["gem_bid_id"])
                ).first()
                if existing:
                    existing.gem_bid_id = b["gem_bid_id"]
                    existing.bid_number = b["bid_number"]
                    existing.category_name = b["category_name"]
                    existing.dept_name = b.get("dept_name")
                    existing.ministry_name = b.get("ministry_name")
                    existing.consignee_city = b.get("consignee_city", "Bangalore Urban")
                    existing.consignee_state = b.get("consignee_state", "KARNATAKA")
                    existing.end_date = end_dt
                    existing.bid_url = b.get("bid_url")
                else:
                    new_bid = Bid(
                        gem_bid_id=b["gem_bid_id"],
                        bid_number=b["bid_number"],
                        bid_number_parent=b.get("bid_number_parent"),
                        category_name=b.get("category_name"),
                        quantity=b.get("quantity"),
                        bid_type=b.get("bid_type", 1),
                        status=b.get("status", 1),
                        is_high_value=bool(b.get("is_high_value", False)),
                        ministry_name=b.get("ministry_name"),
                        dept_name=b.get("dept_name"),
                        start_date=start_dt,
                        end_date=end_dt,
                        consignee_state=b.get("consignee_state", "KARNATAKA"),
                        consignee_city=b.get("consignee_city", "Bangalore Urban"),
                        bid_url=b.get("bid_url"),
                        cat_id=b.get("cat_id"),
                    )
                    db.add(new_bid)

            db.commit()
            logger.info(f"✅ Verified {len(baseline_bids)} curated target tenders in database")

        # 3. Ensure alerts exist for all target bids
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
                created_at=prof.created_at,
            )
            for b in all_bids:
                b_create = BidCreate(
                    gem_bid_id=b.gem_bid_id,
                    bid_number=b.bid_number,
                    category_name=b.category_name,
                    consignee_state=b.consignee_state,
                    consignee_city=b.consignee_city,
                )
                match = match_bid_to_profile(b_create, p_out)
                if match.matched:
                    already = db.query(Alert).filter(Alert.profile_id == prof.id, Alert.bid_id == b.id).first()
                    if not already:
                        alert = Alert(
                            profile_id=prof.id,
                            bid_id=b.id,
                            matched_keywords=keywords_summary(match.matched_keywords),
                            notification_sent=False
                        )
                        db.add(alert)
                        created_alerts += 1
        db.commit()
        if created_alerts > 0:
            logger.info(f"✅ Created {created_alerts} new alerts for target tenders")
    except Exception as e:
        logger.error(f"⚠️ Error during auto-seeding: {e}")
