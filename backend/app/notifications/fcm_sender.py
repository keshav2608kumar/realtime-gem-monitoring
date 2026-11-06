"""
GeM BidWatch — FCM Notification Sender
Sends alarm-style push notifications to registered Android devices via Firebase.
Falls back to logging when Firebase is not configured (dev mode).
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def _get_firebase_app():
    """Initialize Firebase Admin SDK if not already done."""
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        if not firebase_admin._apps:
            from app.settings import settings
            if not settings.FIREBASE_SERVICE_ACCOUNT_PATH:
                logger.warning("FIREBASE_SERVICE_ACCOUNT_PATH not set. FCM disabled.")
                return None
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)

        return firebase_admin.get_app()
    except ImportError:
        logger.warning("firebase-admin not installed. FCM disabled.")
        return None
    except Exception as e:
        logger.error(f"Firebase init error: {e}")
        return None


def send_bid_alert(fcm_token: str, bid_number: str, category: str,
                   city: str, end_date: Optional[str], bid_url: str,
                   matched_keywords: str) -> bool:
    """
    Send a single FCM notification to one device.
    Uses high-priority data message for alarm-style behavior on Android.
    Returns True on success.
    """
    try:
        import firebase_admin
        from firebase_admin import messaging

        app = _get_firebase_app()
        if not app:
            # Dev mode: just log
            logger.info(
                f"[FCM-DEV] Would send alert to token={fcm_token[:20]}...\n"
                f"  Bid: {bid_number}\n"
                f"  Category: {category}\n"
                f"  City: {city}\n"
                f"  End Date: {end_date}\n"
                f"  Keywords: {matched_keywords}"
            )
            return True

        # Build message — data payload triggers background handler on Android
        message = messaging.Message(
            token=fcm_token,
            # Data payload: always delivered, even when app is killed
            data={
                "type": "NEW_BID_ALERT",
                "bid_number": str(bid_number),
                "category": str(category)[:200],
                "city": str(city),
                "end_date": str(end_date or ""),
                "bid_url": str(bid_url),
                "matched_keywords": str(matched_keywords),
                "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
            },
            # Notification for foreground display
            notification=messaging.Notification(
                title=f"🚨 GeM Bid Match: {city}",
                body=f"{bid_number}\n{category[:80]}",
            ),
            android=messaging.AndroidConfig(
                priority="high",
                ttl=3600,  # 1 hour TTL
                notification=messaging.AndroidNotification(
                    channel_id="gem_bid_alerts",
                    priority="max",
                    sound="alarm",
                    visibility="public",
                    sticky=True,
                    vibrate_timings_millis=[0, 500, 200, 500, 200, 500],
                    notification_priority=messaging.AndroidNotificationPriority.MAX,
                ),
            ),
        )

        response = messaging.send(message)
        logger.info(f"FCM sent successfully: {response}")
        return True

    except Exception as e:
        logger.error(f"FCM send failed for token {fcm_token[:20]}...: {e}")
        return False


def send_alert_notifications(alert_id: int) -> None:
    """
    Send FCM notifications for a given alert_id to ALL active devices.
    Updates alert.notification_sent status.
    Called as background task.
    """
    from app.database import SessionLocal
    from app.models import Alert, Bid, Device

    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.error(f"Alert {alert_id} not found")
            return

        bid = db.query(Bid).filter(Bid.id == alert.bid_id).first()
        if not bid:
            logger.error(f"Bid for alert {alert_id} not found")
            return

        devices = db.query(Device).filter(Device.is_active == True).all()
        if not devices:
            logger.warning("No active devices registered. Cannot send FCM.")
            return

        end_date_str = bid.end_date.strftime("%d-%b-%Y %H:%M UTC") if bid.end_date else "N/A"
        success_count = 0

        for device in devices:
            ok = send_bid_alert(
                fcm_token=device.fcm_token,
                bid_number=bid.bid_number,
                category=bid.category_name or "",
                city=bid.consignee_city or bid.consignee_state or "",
                end_date=end_date_str,
                bid_url=bid.bid_url or "",
                matched_keywords=alert.matched_keywords or "",
            )
            if ok:
                success_count += 1

        # Mark as sent if at least one succeeded
        if success_count > 0:
            alert.notification_sent = True
            alert.notification_sent_at = datetime.now(timezone.utc)
        else:
            alert.retry_count += 1
            alert.notification_error = "All FCM sends failed"

        db.commit()
        logger.info(f"Alert {alert_id}: sent to {success_count}/{len(devices)} devices")

    except Exception as e:
        db.rollback()
        logger.error(f"send_alert_notifications error: {e}", exc_info=True)
    finally:
        db.close()


def dispatch_pending_alerts() -> None:
    """
    Called by scheduler. Sends FCM for all unsent alerts.
    """
    from app.database import SessionLocal
    from app.models import Alert

    db = SessionLocal()
    try:
        pending = db.query(Alert).filter(
            Alert.notification_sent == False,
            Alert.retry_count < 3,
        ).all()
        logger.info(f"Dispatching {len(pending)} pending alerts...")
    finally:
        db.close()

    for alert in pending:
        try:
            send_alert_notifications(alert.id)
        except Exception as e:
            logger.error(f"Dispatch failed for alert {alert.id}: {e}")
