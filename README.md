# HackaBot 🤖

HackaBot is an automated hackathon aggregator and notifier that collects upcoming hackathons from MLH and Devpost, filters for user preferences and future events, stores structured details in a database, and alerts users about new opportunities. It saves developers hours of searching, keeps the database clean by only storing future events, increases hackathon participation through notifications.


# Features ✨

**Automatic Scraping:** Handles infinite scroll, pagination, and dynamically loaded content from MLH and Devpost.

**Event Filtering:** Only stores hackathons that aligns with user prefernces starting today or later, ignoring past events.

**Structured Data Storage:** Tracks event name, link, start/end dates, location, online/offline status, and tags.

**Notifications:** Sends alerts via Discord for new hackathons.

**Extensible:** Supports adding more platforms, custom filters, or notification channels without major refactoring to the code setup.

---

# Tech Stack 🛠️

| Layer         | Technology                        |
| ------------- | --------------------------------- |
| Scraping      | Python, Selenium, BeautifulSoup   |
| Database      | SQLAlchemy, SQLite                |
| Scheduler     | APScheduler                       |
| Notifications | Discord Webhooks                  |

---
# Screenshots
<img width="700" height="580" alt="image" src="https://github.com/user-attachments/assets/adcebfe9-7a9d-43f7-9d8e-652f9d96ccba" />

---

# Installation ⚡

```bash
git clone https://github.com/zana9999/HackaBot.git
cd HackaBot
```

**Requirements dependencies:**

```
selenium>=4.15.0
beautifulsoup4>=4.12.2
requests>=2.31.0
apscheduler>=3.10.0
sqlalchemy>=2.1.0
python-dotenv>=1.1.1
```

---

# Usage 🚀

**Run the scraper and scheduler:**

```bash
python -m app.scheduler.scheduler
```

* Scrapes MLH and Devpost for upcoming hackathons.
* Stores them in the database (`hackabot.db`).
* Sends Discord notifications for newly added events.
* Scheduler runs every 24 hours automatically.

---

# Improvements
- Potentially add a description feature to the hackathon message. 


