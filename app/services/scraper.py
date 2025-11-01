import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.hackathons import Hackathons
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from app.services.discordnotifs import send_DiscordMessage
from app.services.filter import passes_filters
import json
from app.database import SessionLocal
from dateutil import parser as date_parser



def parse_date(date_str):
    """Parse MLH ISO date string YYYY-MM-DD"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None

def clean_text(text):
    return text.strip().replace("\n", " ").replace("\t", " ") if text else ""


from dateutil import parser as date_parser
import re

from dateutil import parser as date_parser
import re

def parse_devpost_date(date_str):
    """Parse Devpost submission period string into start_date and end_date"""
    print(f"[DATE DEBUG] Attempting to parse: '{date_str}'")
    
    try:
        date_str = date_str.strip()
        date_str = date_str.replace("–", "-").replace("—", "-").replace("−", "-")
        
        print(f"[DATE DEBUG] Normalized: '{date_str}'")
        
        year_match = re.search(r'\b(20\d{2})\b', date_str)
        if not year_match:
            print(f"[DATE DEBUG] No year found")
            return None, None
        year = int(year_match.group(1))
        
        if "-" in date_str:
            parts = date_str.split("-", 1)   
            if len(parts) != 2:
                print(f"[DATE DEBUG] Invalid range format")
                return None, None
                
            start_str = parts[0].strip()
            end_str = parts[1].strip()
            
            print(f"[DATE DEBUG] Range parts: '{start_str}' and '{end_str}'")
            
            if re.match(r'^\d{1,2},\s*\d{4}$', end_str):
                month_match = re.match(r'^([A-Za-z]+)\s+(\d{1,2})$', start_str)
                if month_match:
                    month_str = month_match.group(1)
                    start_day = month_match.group(2)
                    end_day = end_str.split(',')[0].strip()
                    
                    start_date = date_parser.parse(f"{month_str} {start_day}, {year}").date()
                    end_date = date_parser.parse(f"{month_str} {end_day}, {year}").date()
                    
                    print(f"[DATE DEBUG] Same month range: {start_date} to {end_date}")
                    return start_date, end_date
            
            try:
                end_date = date_parser.parse(end_str).date()
                
                if year_match and str(year) not in start_str:
                    start_str_with_year = f"{start_str}, {year}"
                    start_date = date_parser.parse(start_str_with_year).date()
                else:
                    start_date = date_parser.parse(start_str).date()
                
                print(f"[DATE DEBUG] Different month range: {start_date} to {end_date}")
                return start_date, end_date
            except Exception as e:
                print(f"[DATE DEBUG] Range parse error: {e}")
                return None, None
        else:
            single_date = date_parser.parse(date_str).date()
            print(f"[DATE DEBUG] Parsed single date: {single_date}")
            return single_date, single_date
            
    except Exception as e:
        print(f"[DATE DEBUG] Parse error: {e}")
        return None, None

def save_hackathon(session: Session, name, link, start_date=None, end_date=None,
                   platform="", city="", state="", online=False, tags=None):
    """Add a hackathon to DB if not exists"""
    if not link:
        return False
    exists = session.query(Hackathons).filter_by(link=link).first()
    if exists:
        return False  
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
    return True 



def scrape_mlh_events(session: Session):
    MLH_URL = "https://mlh.io/seasons/2026/events"
    print("[DEBUG] Launching Chrome for MLH...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.get(MLH_URL)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".event"))
        )
        print("[DEBUG] MLH event elements detected")
    except Exception:
        print("[DEBUG] Timeout waiting for events")
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()

    today = date.today()
    new_hackathons_to_send = []

    for e in soup.find_all("div", class_="event"):
        start_tag = e.select_one("meta[itemprop='startDate']")
        end_tag = e.select_one("meta[itemprop='endDate']")
        if not start_tag or not end_tag:
            continue
        start_date = parse_date(start_tag["content"]).date()
        end_date = parse_date(end_tag["content"]).date()
        if end_date < today:
            continue  


        name_tag = e.select_one(".event-name")
        name = name_tag.get_text(strip=True) if name_tag else "N/A"
        link_tag = e.select_one("a.event-link")
        link = link_tag["href"] if link_tag else None
        city_tag = e.select_one(".event-location [itemprop='city']")
        state_tag = e.select_one(".event-location [itemprop='state']")
        city = city_tag.get_text(strip=True) if city_tag else "N/A"
        state = state_tag.get_text(strip=True) if state_tag else "N/A"
        online_text = clean_text(
            e.select_one(".event-hybrid-notes span").text
            if e.select_one(".event-hybrid-notes span") else ""
        )
        online = "digital" in online_text.lower() or "online" in online_text.lower()
        tags = []
        ribbon = e.select_one(".ribbon")
        if ribbon:
            tags.append(clean_text(ribbon.text))

        hackathon_obj = {
            "name": name,
            "link": link,
            "platform": "MLH",
            "city": city,
            "state": state,
            "online": online,
            "tags": tags
        }

        if not passes_filters(hackathon_obj):
            continue

        added = save_hackathon(session, name, link, start_date, end_date, "MLH", city, state, online, tags)
        if added:
            new_hackathons_to_send.append(f"{name} | {city}, {state} | {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')} | Link: {link}")
            print(f"[MLH ADDED] {name}")

    session.commit()
    send_DiscordMessage(new_hackathons_to_send)
    print("MLH future events added!")


def scrape_devpost_events(session: Session):
    DEV_URL = "https://devpost.com/hackathons"
    today = date.today()
    new_hackathons_to_send = []

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    driver.get(DEV_URL)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".hackathon-tile"))
        )
    except Exception:
        print("[DEBUG] No hackathons found or timeout reached.")
        driver.quit()
        return

    seen_links = set()
    consecutive_ended_count = 0
    MAX_CONSECUTIVE_ENDED = 25  
    SCROLL_PAUSE = 3  
    previous_tile_count = 0
    no_new_tiles_count = 0
    MAX_NO_NEW_TILES = 5 

    print(f"[DEBUG] Starting Devpost scrape. Today's date: {today}")

    while True:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        hackathons = soup.select(".hackathon-tile")
        current_tile_count = len(hackathons)
        
        print(f"[DEBUG] Current tiles on page: {current_tile_count}")

        driver.execute_script("""
            window.scrollTo({
                top: document.body.scrollHeight * 0.85,
                behavior: 'smooth'
            });
        """)
        time.sleep(SCROLL_PAUSE)
        
        driver.execute_script("""
            window.scrollTo({
                top: document.body.scrollHeight - 800,
                behavior: 'smooth'
            });
        """)
        time.sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        hackathons = soup.select(".hackathon-tile")
        new_tile_count = len(hackathons)

        if new_tile_count == previous_tile_count:
            no_new_tiles_count += 1
            print(f"[DEBUG] No new tiles loaded ({no_new_tiles_count}/{MAX_NO_NEW_TILES})")
            if no_new_tiles_count >= MAX_NO_NEW_TILES:
                print("[DEBUG] No new tiles loading after multiple scrolls. Ending scraper.")
                break
        else:
            no_new_tiles_count = 0
            print(f"[DEBUG] New tiles loaded! {previous_tile_count} -> {new_tile_count}")
            previous_tile_count = new_tile_count

        found_future_in_batch = False
        processed_in_batch = 0
        
        for h in hackathons:
            link_tag = h.select_one("a.tile-anchor")
            link = link_tag["href"] if link_tag else None
            if not link or link in seen_links:
                continue

            seen_links.add(link) 
            processed_in_batch += 1

            date_tag = h.select_one(".submission-period")
            start_date, end_date = parse_devpost_date(date_tag.text) if date_tag else (None, None)
            
            if not start_date or not end_date:
                print(f"[DEBUG] Skipping - no valid dates: {link}")
                continue

            if end_date < today:
                consecutive_ended_count += 1
                
                if consecutive_ended_count >= MAX_CONSECUTIVE_ENDED:
                    print(f"[DEBUG] Found {MAX_CONSECUTIVE_ENDED} consecutive ended hackathons. Stopping scrape.")
                    driver.quit()
                    session.commit()
                    send_DiscordMessage(new_hackathons_to_send)
                    print(f"✅ Devpost events added! Total future events: {len(new_hackathons_to_send)}")
                    return
                continue

            consecutive_ended_count = 0
            found_future_in_batch = True

            name_tag = h.select_one("h3")
            name = clean_text(name_tag.text) if name_tag else "N/A"
            
            location_tag = h.select_one(".hackathon-tile .info span")
            if location_tag:
                location_text = location_tag.text.strip()
                parts = location_text.split(",")
                city = parts[0].strip() if len(parts) > 0 and "online" not in parts[0].lower() else ""
                state = parts[1].strip() if len(parts) > 1 else ""
                online = "online" in location_text.lower() or city == ""
            else:
                city = ""
                state = ""
                online = True

            tags = [clean_text(t.text) for t in h.select(".theme-label")]

            hackathon_obj = {
                "name": name,
                "link": link,
                "platform": "Devpost",
                "city": city,
                "state": state,
                "online": online,
                "tags": tags
            }

            if not passes_filters(hackathon_obj):
                print(f"[DEBUG] Filtered out: {name}")
                continue

            added = save_hackathon(
                session, name, link, start_date, end_date,
                platform="Devpost", city=city, state=state,
                online=online, tags=tags
            )
            
            if added:
                location_str = city if city else "ONLINE"
                if state:
                    location_str += f", {state}"
                new_hackathons_to_send.append(
                    f"{name} | {location_str} | {start_date} - {end_date} | Link: {link}"
                )
                print(f"[DEVPOST ADDED] {name} ({start_date} to {end_date})")

        print(f"[DEBUG] Processed {processed_in_batch} new hackathons in this batch")
        if found_future_in_batch:
            print(f"[DEBUG] Found future hackathons! Total so far: {len(new_hackathons_to_send)}")

    driver.quit()
    session.commit()
    send_DiscordMessage(new_hackathons_to_send)
    print(f"Devpost events added! Total future events: {len(new_hackathons_to_send)}")

if __name__ == "__main__":
    session = SessionLocal()
    try:
        scrape_mlh_events(session)
        scrape_devpost_events(session)
        session.commit()
        print("All hackathons added to the database!")
    finally:
        session.close()
