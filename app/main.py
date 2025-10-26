from fastapi import FastAPI
from app.routes import items
from database import Base, engine
from app.scheduler.scheduler import start_scheduler


app = FastAPI(title="Dynamic Scraper MVP")
app.include_router(items.router)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Dynamic Scraper API Running"}

@app.on_event("startup")
def startup_event():
    start_scheduler()
