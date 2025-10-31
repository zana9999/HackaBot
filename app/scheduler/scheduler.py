from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal, engine, Base
from app.services.scraper import scrape_mlh_events, scrape_devpost_events

def run_scraper_job():
    db = SessionLocal()
    try:
        scrape_mlh_events(db)
        scrape_devpost_events(db)
        db.commit() 
        print("Scraper job completed")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scraper_job, 'interval', seconds=86400)
    scheduler.start()
    print("Scheduler started")
