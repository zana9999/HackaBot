import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.item import TrackedItem

def scrape(url: str, selector: str) -> str:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    element = soup.select_one(selector)
    if not element:
        return None
    return element.get_text(strip=True)

def check_all_items(db: Session):
    """
    Scrape all tracked items in the database, detect changes, and update last_value.
    """
    items = db.query(TrackedItem).all()
    changed_items = []

    for item in items:
        current_value = scrape(item.url, item.selector)
        if current_value is None:
            continue  # selector not found, skip

        if item.last_value != current_value:
            changed_items.append({
                "id": item.id,
                "url": item.url,
                "old_value": item.last_value,  # previous value
                "new_value": current_value     # newly scraped value
            })
            # Now update DB
            item.last_value = current_value
            db.commit()

    return changed_items
