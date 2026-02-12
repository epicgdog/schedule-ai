import re
import requests
from bs4 import BeautifulSoup


def scrape_url(url: str) -> BeautifulSoup | None:
    """Fetch the URL and return a BeautifulSoup object."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as exc:  # pragma: no cover - network
        print(f"Error fetching {url}: {exc}")
        return None


def extract_program_block(soup: BeautifulSoup) -> list[str] | None:
    """Return plain text of the second <tr> of the main program table.

    We anchor on the program title <h1>, climb to its containing table, and
    take the second immediate row (index 1), which holds the requirements block.
    """
    h2 = soup.find("h2")
    if not h2:
        return None

    node = h2
    target = None
    while node and node.name != "tr":
        node = node.parent
    target = node if node and node.name == "tr" else None
    if not target:
        return None

    # raw_text = target.get_text(" ", strip=True)
    # cleaned = re.sub(r"\s+", " ", raw_text)
    # cleaned = cleaned.replace("unit(s)", "")

    regex_filter = r"[A-Z]{2,4} [0-9]{1,3}[A-Z]{0,2}"

    cleanedList = re.findall(regex_filter, target.get_text())     
    return cleanedList or None


if __name__ == "__main__":
    TEST_URL = "https://catalog.sjsu.edu/preview_program.php?catoid=17&poid=13693&returnto=7689"
    soup = scrape_url(TEST_URL)
    if soup:
        text_block = extract_program_block(soup)
        print(text_block or "No block found")