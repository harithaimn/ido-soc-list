# Indonesia Social Listening - Web News Scraper

Web News Scraper for Indonesian news articles with keyword & regex-based filtering.

## Repo Structure

```
.
├── data/
│   └── _01_web_news.json
├── scrape/
│   └── _01_web-news-scrap.py
├── .env
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python scrape/_01_web-news-scrap.py
```

## Output

Saved to:

```
data/_01_web_news.json
```

Each record:

```json
{
  "url": "...",
  "source": "antaranews",
  "title": "...",
  "reporter": "...",
  "editor": "...",
  "translator": "...",
  "date": "...",
  "image_url": "...",
  "image_caption": "...",
  "content": "...",
  "content_paragraphs": ["..."],
  "keywords_article": ["..."],
  "keywords_matched": ["..."],
  "platform": "news"
}
```

## Scope

* **Source:** Antara News (politics section)
* **Pagination:** first 3 pages
* **Article limit:** first 30 links (hardcoded)
* **Filtering:** regex-based keyword matching
* **Delay:** 1 second/request


## Notes

* Only articles matching predefined regex patterns are stored
* Non-relevant articles are skipped
* Basic anti-blocking via headers + delay


## License

Copyright (c) 2026 Harith Aiman.
All rights reserved.
