from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from database import SessionLocal
from app.models.item import TrackedItem
from app.services.scraper import check_all_items

router = APIRouter(prefix="/items", tags=["items"])


class ItemCreate(BaseModel):
    url: str
    notify_email: str = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/check-changes")
def check_changes(db: Session = Depends(get_db)):
    changes = check_all_items(db)
    return {"changed_items": changes}


@router.post("/", response_model=dict)
def add_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = TrackedItem(
        url=item.url,
        notify_email=item.notify_email
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message": "Item Added", "id": db_item.id}


@router.get("/", response_model=List[dict])
def list_items(db: Session = Depends(get_db)):
    items = db.query(TrackedItem).all()
    return [
        {
            "id": i.id,
            "url": i.url,
            "last_value": i.last_value,
            "notify_email": i.notify_email
        } for i in items
    ]


@router.delete("/{item_id}", response_model=dict)
def remove_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TrackedItem).filter(TrackedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}
