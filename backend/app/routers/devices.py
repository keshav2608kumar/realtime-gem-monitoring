"""
Devices Router — Register/manage Android FCM device tokens
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.database import get_db
from app.models import Device
from app.schemas import DeviceRegister, DeviceOut

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def register_device(data: DeviceRegister, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.fcm_token == data.fcm_token).first()
    if existing:
        existing.is_active = True
        existing.last_seen_at = datetime.now(timezone.utc)
        if data.device_name:
            existing.device_name = data.device_name
        db.commit()
        db.refresh(existing)
        return existing

    device = Device(fcm_token=data.fcm_token, device_name=data.device_name, is_active=True)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/", response_model=List[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).filter(Device.is_active == True).all()


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device(device_id: int, db: Session = Depends(get_db)):
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    d.is_active = False
    db.commit()
