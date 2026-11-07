"""
Profiles Router — CRUD for monitoring profiles
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Profile
from app.schemas import ProfileCreate, ProfileUpdate, ProfileOut

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.post("/", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(data: ProfileCreate, db: Session = Depends(get_db)):
    profile = Profile(**data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/", response_model=List[ProfileOut])
def list_profiles(active_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Profile)
    if active_only:
        q = q.filter(Profile.is_active == True)
    return q.all()


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).filter(Profile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    return p


@router.patch("/{profile_id}", response_model=ProfileOut)
@router.put("/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: int, data: ProfileUpdate, db: Session = Depends(get_db)):
    p = db.query(Profile).filter(Profile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(Profile).filter(Profile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(p)
    db.commit()
