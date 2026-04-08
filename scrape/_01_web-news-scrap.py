# _01_web-news-scrap.py

import os
import requests
from bs4 import BeautifulSoup
import time
import json
import re # Regex for keyword filtering
from tqdm import tqdm

BASE_URL = "https://www.antaranews.com/politik"     # Later include many others. 
HEADERS = {"User-Agent": "Mozilla/5.0"}

# KEYWORDS = [
#     #"prabowo",
#     #"presiden",
#     #"pemilu",
#     #"pilpres",
#     #"rakyat",
#     #"politik",
# ]

PATTERNS = [
    # Core political
    re.compile(r"\bprabowo\b", re.IGNORECASE),
    re.compile(r"\bsubianto\b", re.IGNORECASE),
    re.compile(r"\bpresiden\b", re.IGNORECASE),
    re.compile(r"\bpolitik\b", re.IGNORECASE),

    # Election / economy / sentiment
    re.compile(r"\bpemilu\b", re.IGNORECASE),
    re.compile(r"\bpilpres\b", re.IGNORECASE),
    re.compile(r"\brakyat\b", re.IGNORECASE),
    re.compile(r"\bmahal\b", re.IGNORECASE),
    re.compile(r"\bkrisis\b", re.IGNORECASE),

    # Fuel / programs
    re.compile(r"\bmbg\b", re.IGNORECASE),
    #re.compile(r"\bbb m\b|\bbbm\b", re.IGNORECASE),
    re.compile(r"\bbbm\b", re.IGNORECASE),
    re.compile(r"\bgritis\b", re.IGNORECASE),

    # Slang / reactions
    re.compile(r"\bjir\b", re.IGNORECASE),
    re.compile(r"parah\s+banget", re.IGNORECASE),

    # Titles / phrases
    re.compile(r"bapak\s+pandu\s+dunia", re.IGNORECASE),
    re.compile(r"strongman", re.IGNORECASE),

    # Numeric / coded references
    re.compile(r"\b08\b"),

    # Gemoy variations (your regex)
    re.compile(r"\bg+e+m+[uo]+[iy]+\b", re.IGNORECASE),

    # Additional variants
    re.compile(r"\bpapa\b", re.IGNORECASE),
    re.compile(r"joget\s+g+e+m+[uo]+[iy]+", re.IGNORECASE),

    # General context (optional but useful)
    re.compile(r"\bpanggilan\b", re.IGNORECASE),
    re.compile(r"\btugas\b", re.IGNORECASE),
    re.compile(r"\bnegeri\b", re.IGNORECASE),
]


def get_article_links(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    links = []
    for a in soup.select("a"):
        href = a.get("href")
        if href and "/berita/" in href:
            if href.startswith("/"):
                href = "https://www.antaranews.com" + href
            links.append(href)

    return list(set(links))


def is_relevant(text):
    # text = text.lower()
    # return any(k in text for k in KEYWORDS)
    return any(p.search(text) for p in PATTERNS)


def extract_keywords(text):
    matches = []
    for p in PATTERNS:
        found = p.findall(text)
        if found:
            matches.extend(found)
    return list(set(matches))


def scrape_article(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Image URLs and captions
    image_url = None
    image_caption = None

    # img_tag = soup.select_one("figure img")
    # if img_tag:
    #     image_url = img_tag.get("src")

    # caption_tag = soup.select_one("figure figcaption")
    # if caption_tag:
    #     image_caption = caption_tag.get_text(strip=True)


    # Try main content image first
    img_tag = soup.select_one("div.post-content img")

    if img_tag:
        image_url = img_tag.get("data-src") or img_tag.get("src")

    # Fallback: og:image (very reliable)
    if not image_url:
        og = soup.find("meta", property="og:image")
        if og:
            image_url = og.get("content")


    # Safer fallback
    caption_tag = soup.select_one("figure figcaption, div.post-content figcaption")
    if caption_tag:
        image_caption = caption_tag.get_text(strip=True)

    # Info for Pewarta & Editor & Translator
    reporter = None
    editor = None
    translator = None

    # Content
    paragraphs = soup.select("div.post-content p")
    #content = " ".join(p.get_text(strip=True) for p in paragraphs)  # one long line of row
    content_list = []
    for p in paragraphs:
        text = p.get_text(strip=True)

        # skip empty
        if not text:
            continue

        # remove noise
        if text.startswith("Baca juga"):
            continue
        
        # Take Pewarta & Editor info as "author" info
        # if text.startswith("Pewarta"):
        #     reporter = text.replace("Pewarta:", "").strip()
        #     continue

        # if text.startswith("Editor"):
        #     editor = text.replace("Editor:", "").strip()
        #     continue

        if any(k in text for k in ["Pewarta", "Penerjemah", "Editor"]):
            # Extract reporter (Pewarta)
            match_reporter = re.search(r"Pewarta\s*:\s*(.*?)(?=Editor\s*:|Penerjemah\s*:|Copyright|$)", text)
            if match_reporter:
                reporter = match_reporter.group(1).strip()

            # Extract translator (Penerjemah)
            match_translator = re.search(r"Penerjemah\s*:\s*(.*?)(?=Editor\s*:|Pewarta\s*:|Copyright|$)", text)
            if match_translator:
                translator = match_translator.group(1).strip()

            # Extract editor
            match_editor = re.search(r"Editor\s*:\s*(.*?)(?=Pewarta\s*:|Penerjemah\s*:|Copyright|$)", text)
            if match_editor:
                editor = match_editor.group(1).strip()

            continue


        # Remove noises
        if "Copyright" in text:
            continue
        if "Dilarang keras" in text:        # Remove "dilarang keras"
            continue

    
        content_list.append(text)

    content = "\n\n".join(content_list)

    # Date
    date = None

    #date_tag = soup.find("time")
    #date = date_tag.get("datetime") if date_tag else None
    date_tag = soup.select_one("span.text-secondary, span.text-muted")
    if date_tag:
        date = date_tag.get_text(strip=True)

    

    #full_text = f"{title} {content_list}"
    full_text = f"{title} {' '.join(content_list)}"

    # Keyword filtering
    if not is_relevant(full_text):
        return None
    
    keywords = extract_keywords(full_text)


    # Article keywords (from tags)
    keywords_article = []

    tag_elements = soup.select("a[href*='/tag/']")

    for tag in tag_elements:
        text = tag.get_text(strip=True)

        if text:
            keywords_article.append(text)

    keywords_article = list(set(keywords_article))


    return {
        "url": url,
        "source": "antaranews",  # Later all /subarticles  i.g "politik" or "ekonomi" etc
        "title": title,
        "subtitle": None,  # Remove this since it's useless.
        #"author": None, # Replaced with "reporter" and "editor"
        "reporter": reporter,
        "editor": editor,
        "translator": translator,
        "date": date,
        "image_url": image_url,
        "image_caption": image_caption,
        "content": content,     # Full-text version (one long line) is for downstream NLP tasks that prefer raw text. The list version is for human readability
        "content_paragraphs": content_list,
        "keywords_article": keywords_article,
        "keywords_matched": keywords,
        "platform": "news",
    }


def main():
    all_links = []

    # Pagination (first 3 pages)
    for page in range(1, 4):
        url = f"{BASE_URL}?page={page}"
        links = get_article_links(url)
        all_links.extend(links)

    all_links = list(set(all_links))

    print(f"Total links collected: {len(all_links)}")

    results = []

    #for i, link in enumerate(all_links[:30]):  # limit for testing
    for i, link in enumerate(tqdm(all_links[:30], desc="Scraping articles")): # limit for testing
        try:
            time.sleep(1)  # delay to avoid blocking

            article = scrape_article(link)

            if article:
                results.append(article)
                #print(f"[{i+1}] ✓ {article['title']}")
                tqdm.write(f"[{i+1}] ✓ {article['title']}")
            else:
                #print(f"[{i+1}] skipped (not relevant)")
                tqdm.write(f"[{i+1}] skipped (not relevant)")

        except Exception as e:
            #print("Error:", link, e)
            tqdm.write(f"Error: {link} {e}")

    # Save output
    os.makedirs("data", exist_ok=True)

    #with open("news.json", "w", encoding="utf-8") as f:
    with open("data/_01_web_news.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nTotal relevant articles: {len(results)}")


if __name__ == "__main__":
    main()