# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
from app.services.scraper import check_all_items

def run_scraper_job():
    db: Session = SessionLocal()
    try:
        changed = check_all_items(db)
        if changed:
            print(f"Changes detected: {changed}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run every 30 seconds
    scheduler.add_job(run_scraper_job, 'interval', seconds=10)
    scheduler.start()
    print("Scheduler started")
