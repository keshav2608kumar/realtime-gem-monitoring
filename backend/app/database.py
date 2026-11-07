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


def init_db():
    """Create all tables and run migrations. Call at app startup."""
    from app.models import bid, profile, alert, device, health  # noqa: F401
    Base.metadata.create_all(bind=engine)
    migrate_db()
