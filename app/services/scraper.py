import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.hackathons import Hackathons
from app.database import SessionLocal, engine, Base
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from datetime import date, datetime

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None

def clean_text(text):
    return text.strip() if text else ""

def save_hackathon(session, name, link, start_date=None, end_date=None,
                   platform="", city="", state="", online=False, tags=None):
    if not link:
        return
    exists = session.query(Hackathons).filter_by(link=link).first()
    if exists:
        return
    hackathon = Hackathons(
        name=name,
        link=link,
        start_date=start_date,
        end_date=end_date,
        platform=platform,
        city=city,
        state=state,
        online=online,
        tags=",".join(tags) if tags else None
    )
    session.add(hackathon)


def clean_text(text):
    return text.strip().replace("\n", " ").replace("\t", " ") if text else ""


def parse_devpost_date(date_str):
    """Parse Devpost submission period string into start_date and end_date"""
    try:
        if "-" in date_str:
            start_str, end_str = date_str.split("-")
            # If year missing in start_str, assume same year as end_str
            end_date = datetime.strptime(end_str.strip(), "%b %d, %Y").date()
            try:
                start_date = datetime.strptime(start_str.strip(), "%b %d").replace(year=end_date.year).date()
            except:
                start_date = end_date
        else:
            start_date = end_date = datetime.strptime(date_str.strip(), "%b %d, %Y").date()
        return start_date, end_date
    except:
        return None, None



def scrape_mlh_events(session):
    MLH_URL = "https://mlh.io/seasons/2026/events"

    print("[DEBUG] Launching Chrome...")
    options = Options()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    print("[DEBUG] Loading MLH page...")
    driver.get(MLH_URL)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".event"))
        )
        print("[DEBUG] Event elements detected on page.")
    except Exception:
        print("[DEBUG] Timeout waiting for events to load.")

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()

    today = date.today()

    # Only select events starting today or later
    events = []
    for e in soup.find_all("div", class_="event"):
        start_tag = e.select_one("meta[itemprop='startDate']")
        end_tag = e.select_one("meta[itemprop='endDate']")
        if not start_tag or not end_tag:
            continue
        start = parse_date(start_tag["content"]).date()
        end = parse_date(end_tag["content"]).date()
        
        # Only include ongoing or future events
        if end < today:
            continue
    
        events.append(e)


    print(f"[DEBUG] MLH found {len(events)} future events")

    for e in events:
        name_tag = e.select_one(".event-name")
        name = name_tag.get_text(strip=True) if name_tag else "N/A"

        link_tag = e.select_one("a.event-link")
        link = link_tag["href"] if link_tag else "N/A"

        start_date_tag = e.select_one("meta[itemprop='startDate']")
        start_date = parse_date(start_date_tag["content"]) if start_date_tag else None

        end_date_tag = e.select_one("meta[itemprop='endDate']")
        end_date = parse_date(end_date_tag["content"]) if end_date_tag else None

        city_tag = e.select_one(".event-location [itemprop='city']")
        state_tag = e.select_one(".event-location [itemprop='state']")
        city = city_tag.get_text(strip=True) if city_tag else "N/A"
        state = state_tag.get_text(strip=True) if state_tag else "N/A"

        online_text = clean_text(
            e.select_one(".event-hybrid-notes span").text
            if e.select_one(".event-hybrid-notes span")
            else ""
        )
        online = "digital" in online_text.lower() or "online" in online_text.lower()

        tags = []
        ribbon = e.select_one(".ribbon")
        if ribbon:
            tags.append(clean_text(ribbon.text))

        save_hackathon(session, name, link, start_date, end_date, "MLH", city, state, online, tags)

        # ✅ print inside the loop
        print(
            f"{name} | {city}, {state} | {start_date} - {end_date} | "
            f"Online: {online} | Tags: {tags} | Link: {link}"
        )

    session.commit()
    print("✅ MLH future events added!")

def scrape_devpost_events(session):
    DEV_URL = "https://devpost.com/hackathons"
    today = date.today()
    page = 1
    total_added = 0

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    while True:
        url = f"{DEV_URL}?page={page}"
        print(f"[DEBUG] Loading Devpost page {page}...")
        driver.get(url)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".hackathon-tile"))
            )
        except Exception:
            print("[DEBUG] No more hackathons found or timeout reached.")
            break

        # Scroll to bottom to load lazy-loaded hackathons
        SCROLL_PAUSE_TIME = 2
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        hackathons = soup.select(".hackathon-tile")
        if not hackathons:
            print("[DEBUG] No hackathons found on this page.")
            break

        future_count = 0
        for h in hackathons:
            name_tag = h.select_one("h3")
            name = clean_text(name_tag.text) if name_tag else "N/A"

            link_tag = h.select_one("a.tile-anchor")
            link = link_tag["href"] if link_tag else None

            date_tag = h.select_one(".submission-period")
            start_date, end_date = parse_devpost_date(date_tag.text) if date_tag else (None, None)

            if not start_date or end_date < today:
                continue

            city = state = ""
            online = True  # Devpost hackathons are typically online or unspecified
            tags = [clean_text(t.text) for t in h.select(".theme-label")]

            save_hackathon(session, name, link, start_date, end_date, platform="Devpost",
                           city=city, state=state, online=online, tags=tags)
            print(f"{name} | {start_date} - {end_date} | Tags: {tags} | Link: {link}")
            future_count += 1
            total_added += 1

        print(f"[DEBUG] Page {page} done. Future hackathons found: {future_count}")
        page += 1

    driver.quit()
    session.commit()
    print(f"✅ Devpost events added! Total future events: {total_added}")

    

if __name__ == "__main__":
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        scrape_mlh_events(session)
        scrape_devpost_events(session)
        session.commit()  
        print("All hackathons added to the database!")
    finally:
        session.close()

