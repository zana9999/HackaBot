from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database import SessionLocal, engine, Base


class Hackathons(Base):
    __tablename__ = "hackathons"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    link = Column(String, unique=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    platform = Column(String)
    tags = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    online = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.utcnow)
