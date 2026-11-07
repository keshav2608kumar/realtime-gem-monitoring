"""
GeM BidWatch — SQLAlchemy Database Setup with Safe Auto-Migration
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.settings import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    """
    Safely inspect and add missing columns to SQLite/Postgres tables.
    Guarantees no data loss when upgrading database schema.
    """
    with engine.connect() as conn:
        # Check bids table columns
        try:
            result = conn.execute(text("PRAGMA table_info(bids)"))
            existing_bid_cols = {row[1] for row in result.fetchall()}
            if existing_bid_cols:
                bid_cols_to_add = [
                    ("buyer_state", "VARCHAR(100)"),
                    ("buyer_district", "VARCHAR(100)"),
                    ("buyer_city", "VARCHAR(100)"),
                    ("consignee_district", "VARCHAR(100)"),
                    ("delivery_state", "VARCHAR(100)"),
                    ("delivery_district", "VARCHAR(100)"),
                    ("delivery_city", "VARCHAR(100)"),
                    ("delivery_address", "TEXT"),
                    ("raw_location_text", "TEXT"),
                    ("location_verification_status", "VARCHAR(50)"),
                    ("data_source_classification", "VARCHAR(50)"),
                    ("raw_source_record", "TEXT"),
                    ("source_retrieval_time", "TIMESTAMP"),
                    ("data_ingestion_time", "TIMESTAMP"),
                    ("bid_status", "VARCHAR(50)"),
                    ("estimated_value", "FLOAT"),
                    ("category_key", "VARCHAR(100)"),
                    ("category_mapping_status", "VARCHAR(50)"),
                    ("pdf_delivery_address", "TEXT"),
                    ("pdf_delivery_city", "VARCHAR(100)"),
                    ("pdf_delivery_district", "VARCHAR(100)"),
                    ("pdf_delivery_state", "VARCHAR(100)"),
                    ("pdf_delivery_pincode", "VARCHAR(20)"),
                    ("pdf_delivery_consignee", "VARCHAR(200)"),
                    ("pdf_delivery_org", "VARCHAR(255)"),
                    ("pdf_page_number", "INTEGER"),
                    ("pdf_extraction_method", "VARCHAR(50)"),
                    ("pdf_confidence_score", "FLOAT"),
                    ("pdf_verification_status", "VARCHAR(50)"),
                    ("pdf_processed_at", "TIMESTAMP"),
                    ("pdf_doc_hash", "VARCHAR(64)"),
                    ("target_location_status", "VARCHAR(50)"),
                    ("original_end_date", "TIMESTAMP"),
                    ("revised_end_date", "TIMESTAMP"),
                    ("corrigendum_status", "VARCHAR(50)"),
                    ("corrigendum_doc_url", "VARCHAR(500)"),
                    ("corrigendum_details", "TEXT"),
                    ("date_source", "VARCHAR(50)"),
                ]
                for col_name, col_type in bid_cols_to_add:
                    if col_name not in existing_bid_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE bids ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                            logger.info(f"Added column {col_name} to bids table")
                        except Exception as ce:
                            logger.debug(f"Column {col_name} addition notice: {ce}")
        except Exception as e:
            logger.warning(f"Notice during bids table migration check: {e}")

        # Check alerts table columns
        try:
            result = conn.execute(text("PRAGMA table_info(alerts)"))
            existing_alert_cols = {row[1] for row in result.fetchall()}
            if existing_alert_cols:
                alert_cols_to_add = [
                    ("match_reason", "TEXT"),
                    ("status", "VARCHAR(50)"),
                    ("acknowledged", "BOOLEAN"),
                    ("acknowledged_at", "TIMESTAMP"),
                ]
                for col_name, col_type in alert_cols_to_add:
                    if col_name not in existing_alert_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE alerts ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                            logger.info(f"Added column {col_name} to alerts table")
                        except Exception as ce:
                            logger.debug(f"Column {col_name} addition notice: {ce}")
        except Exception as e:
            logger.warning(f"Notice during alerts table migration check: {e}")

        # Check profiles table columns
        try:
            result = conn.execute(text("PRAGMA table_info(profiles)"))
            existing_prof_cols = {row[1] for row in result.fetchall()}
            if existing_prof_cols and "categories" not in existing_prof_cols:
                conn.execute(text("ALTER TABLE profiles ADD COLUMN categories JSON"))
                conn.commit()
                logger.info("Added column categories to profiles table")
        except Exception as pe:
            logger.debug(f"Notice during profiles table migration check: {pe}")

        # Backfill target_location_status on bids if missing or UNKNOWN
        try:
            from app.services.location_normalizer import resolve_effective_bid_delivery_location
            bids_to_loc_backfill = conn.execute(
                text("""
                    SELECT id, pdf_delivery_address, pdf_delivery_city, pdf_delivery_district,
                           pdf_delivery_state, pdf_delivery_pincode, delivery_address, delivery_city,
                           delivery_district, delivery_state, consignee_city, consignee_district,
                           consignee_state, raw_location_text, dept_name
                    FROM bids WHERE target_location_status IS NULL OR target_location_status = 'UNKNOWN'
                """)
            ).fetchall()
            for b_row in bids_to_loc_backfill:
                b_dict = {
                    "pdf_delivery_address": b_row[1],
                    "pdf_delivery_city": b_row[2],
                    "pdf_delivery_district": b_row[3],
                    "pdf_delivery_state": b_row[4],
                    "pdf_delivery_pincode": b_row[5],
                    "delivery_address": b_row[6],
                    "delivery_city": b_row[7],
                    "delivery_district": b_row[8],
                    "delivery_state": b_row[9],
                    "consignee_city": b_row[10],
                    "consignee_district": b_row[11],
                    "consignee_state": b_row[12],
                    "raw_location_text": b_row[13],
                    "dept_name": b_row[14],
                }
                st, conf, c, d, s = resolve_effective_bid_delivery_location(b_dict)
                conn.execute(
                    text("UPDATE bids SET target_location_status = :tstatus WHERE id = :bid_id"),
                    {"tstatus": st, "bid_id": b_row[0]}
                )
            conn.commit()
        except Exception as lbe:
            logger.debug(f"Notice during target_location_status backfill: {lbe}")
        try:
            from app.services.category_service import match_category
            bids_to_backfill = conn.execute(
                text("SELECT id, category_name, cat_id FROM bids WHERE category_key IS NULL AND category_name IS NOT NULL")
            ).fetchall()
            for b_row in bids_to_backfill:
                b_id, cat_name, cat_id = b_row[0], b_row[1], b_row[2]
                ckey, cname, cstatus = match_category(cat_name, cat_id)
                if ckey:
                    conn.execute(
                        text("UPDATE bids SET category_key = :ckey, category_mapping_status = :cstatus WHERE id = :bid_id"),
                        {"ckey": ckey, "cstatus": cstatus, "bid_id": b_id}
                    )
            conn.commit()
        except Exception as bfe:
            logger.debug(f"Notice during category backfill: {bfe}")


def init_db():
    """Create all tables and run migrations. Call at app startup."""
    from app.models import bid, profile, alert, device, health  # noqa: F401
    Base.metadata.create_all(bind=engine)
    migrate_db()
