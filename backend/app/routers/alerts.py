"""
Alerts Router — Alert history + manual notification trigger
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List

from app.database import get_db
from app.models import Alert, Bid
from app.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertOut])
def list_alerts(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Alert).options(joinedload(Alert.bid)).order_by(desc(Alert.created_at))
    if unread_only:
        q = q.filter(Alert.notification_sent == False)
    return q.offset(skip).limit(limit).all()


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).options(joinedload(Alert.bid)).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return a


@router.post("/{alert_id}/retry-notify")
def retry_notification(alert_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger FCM notification for an alert."""
    from app.notifications.fcm_sender import send_alert_notifications
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    background_tasks.add_task(send_alert_notifications, alert_id)
    return {"message": "Notification retry queued"}
