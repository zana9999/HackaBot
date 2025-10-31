from fastapi import FastAPI
from app.routes import hackathons
from app.database import SessionLocal, engine, Base
from app.scheduler.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Hackabot MVP")
app.include_router(hackathons.router)


@app.get("/")
def root():
    return {"message": "HackaBot Running"}

@app.on_event("startup")
def startup_event():
    start_scheduler()
