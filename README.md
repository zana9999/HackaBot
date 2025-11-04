# HackaBot 🚀

HackaBot is an automated hackathon aggregator and notifier that collects upcoming hackathons from MLH and Devpost, filters for future events, stores structured details in a database, and alerts users to new opportunities.

---

## Features

- **Automatic scraping:** Handles infinite scroll, pagination, and dynamically loaded content.  
- **Event filtering:** Only stores and notifies users about upcoming hackathons that aligns with users preferences!  
- **Structured data storage:** Tracks event name, link, start/end dates, location, online/offline status, and tags.  
- **Notifications:** Sends alerts via Discord when new hackathons are added.  
- **Extensible:** Easily add more platforms, filters, or notification channels.

---

## Tech Stack

- **Language:** Python  
- **Scraping & Automation:** Selenium, BeautifulSoup  
- **Database:** SQLAlchemy with SQLite
- **Scheduler:** APScheduler  
- **Notifications:** Discord  

---
