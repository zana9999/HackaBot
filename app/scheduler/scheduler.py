from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
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
    # Run the job every 24 hours
    scheduler.add_job(run_scraper_job, 'interval', seconds=86400)
    scheduler.start()
    print("Scheduler started and will run every 24 hours")

if __name__ == "__main__":
    run_scraper_job()  # run immediately when the script starts
    start_scheduler()

    # Keep the script running so the scheduler doesn't exit
    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped")
