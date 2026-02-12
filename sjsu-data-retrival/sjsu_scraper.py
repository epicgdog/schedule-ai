import asyncio
import re
import sys
import time
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, select


def get_db_engine():
    """Creates a SQLAlchemy engine, preferring Turso if configured, otherwise local SQLite."""
    turso_url = os.getenv("TURSO_DATABASE_URL")
    turso_token = os.getenv("TURSO_ACCESS_TOKEN")
    
    if turso_url and turso_token:
        try:
            import libsql
            
            class LibSQLConnectionWrapper:
                def __init__(self, conn):
                    self.conn = conn
                
                def create_function(self, *args, **kwargs):
                    pass # Mock function to avoid SQLAlchemy error
                
                def __getattr__(self, name):
                    return getattr(self.conn, name)

            def creator():
                conn = libsql.connect(database=turso_url, auth_token=turso_token)
                return LibSQLConnectionWrapper(conn)
            
            print(f"Using Turso Database: {turso_url}")
            return create_engine("sqlite://", creator=creator)
        except ImportError:
            print("Warning: 'libsql' package not found. Falling back to local SQLite.")
    
    # Fallback to local SQLite
    database_name = "sjsu_courses.db"
    database_url = f"sqlite:///{database_name}"
    print(f"Using Local SQLite Database: {database_name}")
    return create_engine(database_url)

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# URL Template provided by user for pagination
# filter[cpage] is the query param for page number
LIST_URL_TEMPLATE = "https://catalog.sjsu.edu/content.php?catoid=17&catoid=17&navoid=7688&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D={}#acalog_template_course_filter"

PREVIEW_URL_TEMPLATE = "https://catalog.sjsu.edu/preview_course.php?catoid=17&coid={}"

# SQLAlchemy Setup
metadata = MetaData()
courses_table = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("course_name", String),
    Column("course_description", Text),
    Column("units", String),
    Column("ge_area", String),
    Column("prerequisites", Text),
    Column("corequisites", Text),
)

def setup_database():
    """Initializes the database schema using SQLAlchemy."""
    engine = get_db_engine()
    metadata.create_all(engine)
    print("Database schema initialized.")

async def scrape_courses(start_page=1, end_page=2):
    engine = get_db_engine()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        for page_num in range(start_page, end_page + 1):
            list_url = LIST_URL_TEMPLATE.format(page_num)
            print(f"=== Navigating to Page {page_num}: {list_url} ===")
            
            try:
                await page.goto(list_url)
                # Wait for at least one course link to be visible
                await page.wait_for_selector("a[href*='preview_course_nopop.php']", timeout=10000)
            except Exception as e:
                print(f"Error loading page {page_num}: {e}")
                continue
            
            # Collect links
            raw_links = await page.locator("a[href*='preview_course_nopop.php']").all()
            course_queue = []
            
            print(f"Extracting course IDs from Page {page_num}...")
            for link in raw_links:
                # Filter social media links
                title = await link.get_attribute("title") or ""
                aria = await link.get_attribute("aria-label") or ""
                if "Tweet" in title or "Facebook" in title or "Share" in aria:
                    continue
                    
                href = await link.get_attribute("href")
                # href format: preview_course_nopop.php?catoid=17&coid=159178
                coid_match = re.search(r'coid=(\d+)', href)
                
                text = await link.inner_text()
                if coid_match and text.strip():
                    course_queue.append({
                        'name': text.strip(),
                        'coid': coid_match.group(1)
                    })
            
            print(f"Found {len(course_queue)} courses on Page {page_num}.")
            
            # Tracking for Sanity Check
            page_stats = {"total": 0, "with_coreqs": 0, "inserted": 0, "skipped": 0}
            
            # Scrape each course directly
            for idx, item in enumerate(course_queue):
                course_name = item['name']
                coid = item['coid']
                target_url = PREVIEW_URL_TEMPLATE.format(coid)
                
                print(f"Processing P{page_num} ({idx+1}/{len(course_queue)}): {course_name} [ID: {coid}]")
                
                try:
                    await page.goto(target_url)
                    
                    # Content targeting
                    try:
                        content_locator = page.locator(".block_content_popup td.block_content").first
                        if not await content_locator.count():
                             content_locator = page.locator(".block_content_popup").first
                        
                        await content_locator.wait_for(timeout=5000)
                        full_text = await content_locator.inner_text()
                    except Exception as wait_err:
                        print(f"Timed out waiting for content for {course_name}: {wait_err}")
                        continue

                    # Parse Text
                    # Units
                    units_match = re.search(r'(\d+(?:\.\d+)?)\s*unit\(s\)', full_text)
                    units = units_match.group(1) if units_match else "N/A"
                    
                    # Description
                    description = "N/A"
                    lines = full_text.split('\n')
                    desc_lines = []
                    capture = False
                    
                    for line in lines:
                        line = line.strip()
                        if line == course_name:
                            continue
                            
                        if "unit(s)" in line:
                            capture = True
                            parts = line.split("unit(s)", 1)
                            if len(parts) > 1 and parts[1].strip():
                                desc_lines.append(parts[1].strip())
                            continue
                        
                        if capture:
                            # Stop capturing on metadata keywords
                            if any(marker in line for marker in ["Satisfies", "Prerequisite", "Corequisite", "Grading", "Note(", "Cross-listed"]):
                                capture = False
                            else:
                                if line:
                                    desc_lines.append(line)

                    description = " ".join(desc_lines).strip()
                    
                    # GE Area
                    ge_match = re.search(r'Satisfies\s*(.*?)(?:\.|$)', full_text)
                    ge_area = ge_match.group(1).strip() if ge_match else "N/A"
                    
                    # Prerequisites
                    prereq_match = re.search(r'Prerequisite\(s\):\s*(.*?)(?:Corequisite|Grading|Note\(|$)', full_text, re.DOTALL)
                    prerequisites = prereq_match.group(1).strip() if prereq_match else "N/A"
                    
                    # Corequisites
                    coreq_match = re.search(r'Corequisite(?:\(s\)|s)?:\s*(.*?)(?:Prerequisite|Grading|Note\(|$)', full_text, re.DOTALL)
                    corequisites = coreq_match.group(1).strip() if coreq_match else "N/A"
                    
                    if corequisites != "N/A":
                        page_stats["with_coreqs"] += 1
                    
                    # Insert DB using SQLAlchemy
                    with engine.begin() as conn:
                        # Check existence first
                        exists_query = select(courses_table.c.id).where(courses_table.c.course_name == course_name)
                        if conn.execute(exists_query).first():
                            print(f"   Skipping duplicate: {course_name}")
                            page_stats["skipped"] += 1
                        else:
                            conn.execute(
                                courses_table.insert().values(
                                    course_name=course_name,
                                    course_description=description,
                                    units=units,
                                    ge_area=ge_area,
                                    prerequisites=prerequisites,
                                    corequisites=corequisites
                                )
                            )
                            page_stats["inserted"] += 1
                            page_stats["total"] += 1

                    # Log
                    print(f"   Saved: Units='{units}', GE='{ge_area}'")
                    print(f"   Prereqs: {prerequisites}")
                    print(f"   Coreqs:  {corequisites}")
                    print("-" * 50)
                    
                except Exception as e:
                    print(f"Error processing {course_name}: {e}")

            # Sanity Check per page
            print(f"\n****** SANITY CHECK: PAGE {page_num} COMPLETED ******")
            print(f"   Total Processed: {len(course_queue)}")
            print(f"   Inserted: {page_stats['inserted']}")
            print(f"   Skipped (Dup): {page_stats['skipped']}")
            print(f"   With Coreqs: {page_stats['with_coreqs']}")
            print("**************************************************\n")
            
            # Pause nicely
            await asyncio.sleep(2)

        engine.dispose()
        await browser.close()
        print("Scraping complete.")

if __name__ == "__main__":
    setup_database()
    # Resume scraping from Page 15 (overlapping slightly is fine due to dup check)
    asyncio.run(scrape_courses(start_page=1, end_page=54))
