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
from app.services.discordnotifs import send_discord_notification
from app.services.filter import passes_filters
import json
from app.database import SessionLocal



def parse_date(date_str):
    """Parse MLH ISO date string YYYY-MM-DD"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None

def clean_text(text):
    return text.strip().replace("\n", " ").replace("\t", " ") if text else ""


def parse_devpost_date(date_str):
    """Parse Devpost submission period string into start_date and end_date"""
    try:
        if "-" in date_str:
            start_str, end_str = date_str.split("-")
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


def send_DiscordMessage(hackathons):
    if not hackathons:
        return

    webhook_url = "https://discord.com/api/webhooks/1433976383326916689/5Lg0LuXAR0yKtaemQFcwdk6_kql5-KA26noo3jbrzEkbry14ONTGoR_K3mQen4dbkd5d"

    CHUNK_SIZE = 10 

    for i in range(0, len(hackathons), CHUNK_SIZE):
        chunk = hackathons[i:i+CHUNK_SIZE]
        embed_fields = []

        for h in chunk:
            parts = h.split(" | ")
            title = parts[0] 
            raw_location = parts[1] if len(parts) > 1 else ""
            # Clean location
            location = raw_location.replace(",", "").strip() or "ONLINE"

            dates = parts[2] if len(parts) > 2 else ""
            link = parts[3] if len(parts) > 3 else ""
            description = f"📍 {location}\n🗓️ {dates}\n🔗({link})"
            
            embed_fields.append({
                "name": title,
                "value": description,
                "inline": False
            })


        payload = {
            "embeds": [{
                "title": "🌟 New Hackathons Added! 🌟",
                "color": 0xE4A0B7,
                "fields": embed_fields
            }]
        }

        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204 or response.status_code == 200:
            print("Discord embed sent!")
        else:
            print(f"Failed to send Discord embed: {response.status_code}, {response.text}")




def scrape_mlh_events(session: Session):
    MLH_URL = "https://mlh.io/seasons/2026/events"
    print("[DEBUG] Launching Chrome for MLH...")
    options = Options()
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
    MAX_CONSECUTIVE_ENDED = 25  # Stop after 25 consecutive ended hackathons
    SCROLL_PAUSE = 3  # Increased wait time for content to load
    previous_tile_count = 0
    no_new_tiles_count = 0
    MAX_NO_NEW_TILES = 5  # Stop if no new tiles appear after 5 scrolls

    print(f"[DEBUG] Starting Devpost scrape. Today's date: {today}")

    while True:
        # Get current tile count before scrolling
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        hackathons = soup.select(".hackathon-tile")
        current_tile_count = len(hackathons)
        
        print(f"[DEBUG] Current tiles on page: {current_tile_count}")

        # Scroll near the bottom (not all the way) to trigger lazy loading
        # Scroll to 90% of the page height to stay in the "trigger zone"
        driver.execute_script("""
            window.scrollTo({
                top: document.body.scrollHeight * 0.85,
                behavior: 'smooth'
            });
        """)
        time.sleep(SCROLL_PAUSE)
        
        # Now scroll closer to trigger more loading
        driver.execute_script("""
            window.scrollTo({
                top: document.body.scrollHeight - 800,
                behavior: 'smooth'
            });
        """)
        time.sleep(2)

        # Get new tile count after scrolling
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        hackathons = soup.select(".hackathon-tile")
        new_tile_count = len(hackathons)

        # Check if new tiles were loaded
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

        # Track if we found any future hackathons in this batch
        found_future_in_batch = False
        processed_in_batch = 0
        
        for h in hackathons:
            link_tag = h.select_one("a.tile-anchor")
            link = link_tag["href"] if link_tag else None
            if not link or link in seen_links:
                continue

            seen_links.add(link)  # Mark as seen immediately
            processed_in_batch += 1

            # Parse dates
            date_tag = h.select_one(".submission-period")
            start_date, end_date = parse_devpost_date(date_tag.text) if date_tag else (None, None)
            
            if not start_date or not end_date:
                print(f"[DEBUG] Skipping - no valid dates: {link}")
                continue

            # Check if hackathon has ended
            if end_date < today:
                consecutive_ended_count += 1
                
                # If we've seen too many ended ones in a row, stop
                if consecutive_ended_count >= MAX_CONSECUTIVE_ENDED:
                    print(f"[DEBUG] Found {MAX_CONSECUTIVE_ENDED} consecutive ended hackathons. Stopping scrape.")
                    driver.quit()
                    session.commit()
                    send_DiscordMessage(new_hackathons_to_send)
                    print(f"✅ Devpost events added! Total future events: {len(new_hackathons_to_send)}")
                    return
                continue

            # Reset counter when we find a future hackathon
            consecutive_ended_count = 0
            found_future_in_batch = True

            # Extract hackathon details
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
