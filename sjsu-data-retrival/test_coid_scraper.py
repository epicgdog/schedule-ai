"""
Tests for coid_scraper.extract_coids_from_html.

Uses static HTML fixtures to validate:
- Rows with colspan="2" are skipped (table_default mode)
- The COID is correctly extracted from onclick or href
- Rows without relevant links are ignored
"""

from pathlib import Path

from coid_scraper import extract_coids_from_html, save_coids

# ── Fixture: table_default with onclick (original catalog view) ──

TABLE_HTML = """
<html><body>
<table class="table_default">
  <tbody>
    <tr><td colspan="2">&nbsp;</td></tr>
    <tr>
      <td>
        <a href="#" onclick="hideCatalogData('17', '3', '156584',
             this, 'a:2:...'); return false;">
          KIN 1 - Adapted Physical Activities
        </a>
      </td>
    </tr>
    <tr><td colspan="2">Section Header</td></tr>
    <tr>
      <td>
        <a href="#" onclick="hideCatalogData('17', '3', '159276',
             this, 'a:2:...'); return false;">
          KIN 2A - Beginning Swimming
        </a>
      </td>
    </tr>
    <tr><td><span>No link here</span></td></tr>
  </tbody>
</table>
</body></html>
"""

# ── Fixture: href-based links (paginated filter view) ──

HREF_HTML = """
<html><body>
<div>
  <a href="preview_course_nopop.php?catoid=17&coid=159178"
     title="KIN 1 - Adapted Physical Activities opens a new window">
    KIN 1 - Adapted Physical Activities
  </a>
  <a href="preview_course_nopop.php?catoid=17&coid=159276"
     title="KIN 2A - Beginning Swimming opens a new window">
    KIN 2A - Beginning Swimming
  </a>
  <a href="preview_course_nopop.php?catoid=17&coid=172907"
     title="KIN 6A - Beginning Pickleball opens a new window">
    KIN 6A - Beginning Pickleball
  </a>
  <!-- Social media link — should be skipped -->
  <a href="preview_course_nopop.php?catoid=17&coid=99999"
     title="Tweet this page">
    Share
  </a>
</div>
</body></html>
"""


# ── table_default onclick tests ──

def test_table_skips_colspan2() -> None:
    coids = extract_coids_from_html(TABLE_HTML)
    assert len(coids) == 2


def test_table_coid_values() -> None:
    coids = extract_coids_from_html(TABLE_HTML)
    assert coids == ["156584", "159276"]


# ── href-based tests ──

def test_href_extraction() -> None:
    coids = extract_coids_from_html(HREF_HTML)
    assert coids == ["159178", "159276", "172907"]


def test_href_skips_social_media() -> None:
    coids = extract_coids_from_html(HREF_HTML)
    assert "99999" not in coids


# ── edge cases ──

def test_no_table_no_links() -> None:
    assert extract_coids_from_html("<html><body><p>Empty</p></body></html>") == []


def test_save_coids(tmp_path: Path) -> None:
    output = tmp_path / "test_coids.txt"
    save_coids(["111", "222", "333"], output_path=output)
    lines = output.read_text(encoding="utf-8").strip().split("\n")
    assert lines == ["111", "222", "333"]
