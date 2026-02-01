from bs4 import BeautifulSoup
import requests
import sqlite3
import asyncio
import logging

from dotenv import load_dotenv
import os
import re

match_string = r"\(Section (\d+)\)"

load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

RELOAD_TIME = 1 # in seconds

# database shit
database = os.getenv("DATABASE")
def database_setup():
    create_table = """
    CREATE TABLE IF NOT EXISTS sjsu_classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        section_number INTEGER NOT NULL,
        class_number INTEGER NOT NULL UNIQUE,
        days TEXT ,
        start_time TEXT,
        end_time TEXT ,
        instructor TEXT ,
        open_seats INTEGER NOT NULL
    )
    """

    try:
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            cursor.execute(create_table)   
            conn.commit()
            logging.info("db successfully made")

    except sqlite3.OperationalError as e:
        logging.error(e)


# SJSU scraper
async def scrape_sjsu():
    logging.info("initiating scraper call")
    res = requests.get("https://www.sjsu.edu/classes/schedules/spring-2026.php")
    soup = BeautifulSoup(res.text, 'html.parser')
    table_rows = soup.find_all("tr")
    logging.info("got the soup")
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        logging.info("connected to db")
        for row in table_rows[1:6]: # just for testing we do 5 classes
            info = row.find_all("td")
            full_course_name = info[0].string
            course_name = full_course_name
            if (full_course_name.index("(") >= 0):
                course_name = full_course_name[:full_course_name.index("(")].strip()
            match = re.search(match_string, full_course_name)
            section_number = int(match.group(1)) if match else None
            class_number = int(info[1].string)
            days = info[7].string
            times = info[8].string
            start_time, end_time = "", ""
            if (times == "TBA"):
                # online class
                start_time = -1
                end_time = -1
            else:
                # times are shown; parse into start and endtime
                [st, en] = times.split("-")
                start_time = st
                end_time = en

            instructor= info[9].string
            open_seats = int(info[12].string)

            try:

                insert_sql = """

                INSERT INTO sjsu_classes (course_name, section_number, class_number, days, start_time, end_time, instructor, open_seats) 
                VALUES              (?, ?, ?, ?, ?, ?, ?, ?) 
                ON CONFLICT (class_number) DO UPDATE SET
                course_name  = excluded.course_name,
                section_number = excluded.section_number,
                class_number = excluded.class_number,
                days         = excluded.days,
                start_time   = excluded.start_time,
                end_time     = excluded.end_time,
                instructor   = excluded.instructor,
                open_seats   = excluded.open_seats
                """

                cursor.execute(insert_sql, (course_name, section_number, class_number, days, start_time, end_time, instructor, open_seats,))
                conn.commit()
            except Exception as e:
                logging.error(f"error occured: {e}")

    logging.info("inserts/updates completed!")

async def scrape_handler():
    database_setup()
    await scrape_sjsu()



if __name__ == "__main__":
    asyncio.run(scrape_handler())

