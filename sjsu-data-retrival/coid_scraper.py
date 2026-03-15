"""
COID Scraper — Extract course IDs from the SJSU catalog.

Scrapes all 54 pages of the SJSU Course Descriptions listing and extracts
the `coid` parameter from each course link's href attribute.

The paginated filter URL renders courses as a list of <a> tags with
href="preview_course_nopop.php?catoid=17&coid=XXXXX". We extract the
coid parameter from each link.

Output: coids.txt — one COID per line, deduplicated.

Usage:
    python coid_scraper.py
"""

import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Paginated URL template — pages 1 through 54
LIST_URL_TEMPLATE = (
    "https://catalog.sjsu.edu/content.php?catoid=17&catoid=17&navoid=7688"
    "&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1"
    "&filter%5Bcpage%5D={}#acalog_template_course_filter"
)

TOTAL_PAGES = 2
REQUEST_DELAY_SECONDS = 2

# Regex to extract coid from href like "preview_course_nopop.php?catoid=17&coid=159178"
COID_FROM_HREF_PATTERN = re.compile(r"coid=(\d+)")

# Regex to extract coid from onclick like "hideCatalogData('17', '3', '159178', ...)"
COID_FROM_ONCLICK_PATTERN = re.compile(
    r"hideCatalogData\(\s*'17'\s*,\s*'3'\s*,\s*'(\d+)'"
)

OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "coids.txt"


def extract_coids_from_html(html: str) -> list[str]:
    """Parse one page of HTML and return a list of COID strings.

    Supports two catalog rendering modes:
    1) Links with href containing "preview_course_nopop.php?...coid=XXXXX"
    2) Links with onclick containing "hideCatalogData('17','3','XXXXX',...)"
       inside a table_default (skipping rows with colspan="2")
    """
    soup = BeautifulSoup(html, "html.parser")
    coids: list[str] = []

    # --- Strategy 1: table_default with onclick ---
    table = soup.find("table", class_="table_default")
    if table:
        for tr in table.find_all("tr"):
            if tr.find("td", attrs={"colspan": "2"}):
                continue
            link = tr.find("a", onclick=True)
            if not link:
                continue
            onclick = link.get("onclick", "")
            match = COID_FROM_ONCLICK_PATTERN.search(onclick)
            if match:
                coids.append(match.group(1))

    # --- Strategy 2: href-based course links (paginated filter view) ---
    if not coids:
        for link in soup.find_all("a", href=re.compile(r"preview_course_nopop\.php")):
            # Filter out social-media share links
            title = link.get("title", "")
            if any(kw in title for kw in ("Tweet", "Facebook", "Share")):
                continue
            href = link.get("href", "")
            match = COID_FROM_HREF_PATTERN.search(href)
            if match:
                coids.append(match.group(1))

    return coids


def scrape_all_pages(
    start_page: int = 1,
    end_page: int = TOTAL_PAGES,
    delay: float = REQUEST_DELAY_SECONDS,
) -> list[str]:
    """Fetch pages start_page..end_page and return deduplicated COIDs."""
    seen: set[str] = set()
    ordered: list[str] = []

    for page_num in range(start_page, end_page + 1):
        url = LIST_URL_TEMPLATE.format(page_num)
        logger.info("Fetching page %d / %d", page_num, end_page)

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Page fetch failed: page=%d error=%s", page_num, exc)
            continue

        page_coids = extract_coids_from_html(response.text)
        new_count = 0
        for coid in page_coids:
            if coid not in seen:
                seen.add(coid)
                ordered.append(coid)
                new_count += 1

        logger.info(
            "Page %d: found %d COIDs (%d new, %d duplicates)",
            page_num,
            len(page_coids),
            new_count,
            len(page_coids) - new_count,
        )

        # Be polite — don't hammer the server
        if page_num < end_page:
            time.sleep(delay)

    return ordered


def save_coids(coids: list[str], output_path: Path = OUTPUT_FILE) -> None:
    """Write COIDs to a text file, one per line."""
    output_path.write_text("\n".join(coids) + "\n", encoding="utf-8")
    logger.info("Saved %d COIDs to %s", len(coids), output_path)


def main() -> None:
    logger.info("Starting COID scraper — pages 1 to %d", TOTAL_PAGES)
    coids = scrape_all_pages()
    save_coids(coids)
    logger.info("Done — %d unique COIDs collected", len(coids))


if __name__ == "__main__":
    main()
