from fastapi import FastAPI
from scraper import database
import sqlite3
import logging
import json

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@app.get("/")
def get_everything():
    try:
        r = []
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            get_sql = """
            SELECT * FROM classes
            """
            cursor.execute(get_sql)
            rows = cursor.fetchall()
            for row in rows:
                logging.info(row)
                (_,course_name, class_number, days, times, instructor, open_seats) = row
                r.append({
                    course_name : course_name,
                    class_number : class_number,
                    days : days,
                    times : times,
                    instructor : instructor,
                    open_seats : open_seats,
                })

        return r


    except Exception as e:
        logging.error(f"error occured: {e}")
