from sqlalchemy import Column, Integer, String, DateTime, Text
from database import Base
from datetime import datetime

class TrackedItem(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    rarity = Column(String)
    last_value = Column(Text)
    notify_email = Column(String, nullable=True)
    last_checked = Column(DateTime, default=datetime.utcnow)
