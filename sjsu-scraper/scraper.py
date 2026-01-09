from bs4 import BeautifulSoup
import requests
import sqlite3
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

RELOAD_TIME = 1 # in seconds

# database shit
database = "sjsu_classes.db"
def database_setup():
    create_table = """
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        class_number INTEGER NOT NULL UNIQUE,
        days TEXT NOT NULL,
        times TEXT NOT NULL,
        instructor TEXT NOT NULL,
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
    try:
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            logging.info("connected to db")
            for row in table_rows[1:]: # just for testing we do 5 classes
                info = row.find_all("td")
                
                course_name = info[0].string
                class_number = int(info[1].string)
                days = info[7].string
                times = info[8].string
                instructor= info[9].string
                open_seats = int(info[12].string)

                insert_sql = """

                INSERT INTO classes (course_name, class_number, days, times, instructor, open_seats) 
                VALUES              (?, ?, ?, ?, ?, ?) 
                ON CONFLICT (class_number) DO UPDATE SET
                course_name  = excluded.course_name,
                class_number = excluded.class_number,
                days         = excluded.days,
                times        = excluded.times,
                instructor   = excluded.instructor,
                open_seats   = excluded.open_seats
                """

                cursor.execute(insert_sql, (course_name, class_number, days, times, instructor, open_seats,))
                conn.commit()

                logging.info(f"inserted/updated ({class_number}) : {course_name}")
    except Exception as e:
        logging.error(f"error occured: {e}")


async def scrape_handler():
    database_setup()
    while True:
        await scrape_sjsu()
        await asyncio.sleep(RELOAD_TIME) 



if __name__ == "__main__":
    asyncio.run(scrape_handler())

