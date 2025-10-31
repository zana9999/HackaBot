from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.hackathons import Hackathons
from app.services.scraper import scrape_devpost_events, scrape_mlh_events

router = APIRouter(prefix="/hackathons", tags=["hackathons"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/check-new")
def check_new_hackathons(db: Session = Depends(get_db)):
    scrape_mlh_events(db)
    scrape_devpost_events(db)
    db.commit() 
    return {"message": "Hackathons updated"}

@router.get("/", response_model=List[dict])
def list_hackathons(db: Session = Depends(get_db)):
    hackathons = db.query(Hackathons).all()
    return [
        {
            "id": h.id,
            "name": h.name,
            "link": h.link,
            "start_date": h.start_date,
            "end_date": h.end_date,
            "platform": h.platform,
            "city": h.city,
            "state": h.state,
            "online": h.online,
            "tags": h.tags
        }
        for h in hackathons
    ]

