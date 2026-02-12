import logging
import uvicorn
import fitz
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import json
import agent
from modules import get_instructor_rating, get_open_classes_for, get_ge_areas, get_courses_by_ge, get_open_ge_classes, get_major_ge_exceptions



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Schedule AI API",
    description="Chat API for the Schedule AI agent",
    version="1.0.0",
)

# Configure CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScheduleRequest(BaseModel):
    major: str
    courses: str
    schedule: str


def get_time(n):
    hour = 7 + (n // 4)
    minute = (n % 4) * 15
    return hour + minute / 60


def get_time_from_str(s: str):
    if s == "TBA":
        return -1
    if s.find("AM") > -1:
        s = s.replace("AM", "")
        [hour, minute] = s.split(":")
        return int(hour) + int(minute) / 60
        # am time
    else:
        s = s.replace("PM", "")
        [hour, minute] = s.split(":")
        if hour == "12":
            hour = 12
        else:
            hour = int(hour) + 12
        return hour + int(minute) / 60
        # pm time



import pandas as pd
import xlrd
import io

@app.post("/api/generate_classes")
async def generate_possible_classes(file: UploadFile = File(...)):
    # Validate Excel content type
    if file.content_type not in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        return {"error": "Invalid file type. Please upload an Excel file (.xls or .xlsx)."}
    logging.info(file.filename)
    # Read file bytes
    contents = await file.read()
    

    # Read file content
    # User confirmed all files are HTML ("fake .xls"), so we prioritize read_html.
    html_error = None
    try:
        # Try parsing as HTML table first
        # default flavor='bs4' uses lxml or html5lib.
        dfs = pd.read_html(io.BytesIO(contents), flavor='bs4', header=None)
        if not dfs:
             # If read_html runs but finds no tables, try excel just in case
             raise ValueError("No tables found in HTML")
        df = dfs # agent.invoke handles list of DataFrames
    except Exception as e:
        html_error = e
        # Fallback: Try standard Excel parsing (xlrd) if HTML parsing failed
        try:
            df = pd.read_excel(io.BytesIO(contents), engine='xlrd')
        except Exception as excel_e:
            return {"error": f"Error reading file. \nHTML Parse Error: {html_error} \nExcel Parse Error: {excel_e}"}
    
    msg = agent.invoke(df)
    
    return {"text": msg}


@app.post("/api/schedule")
async def receive_schedule(request: ScheduleRequest):
    """Receive schedule data from the frontend."""

    # schedule: receive everyday and which days ar e open and which days are not open and stuff
    # figure out a way to find # of consecutive ones in a 15 bit number
    # 100011100101010    --> this would have 5 consecutive, and we need to reutrn which power they are on

    schedule = json.loads(request.schedule)
    for day in schedule:
        num = int(schedule[day])
        curr = -1
        end = -1
        ranges = []
        for i in range(60):
            if num & (1 << i):
                if curr == -1:  # hasn't been set or there's a gap
                    curr = i
                    end = i
                else:
                    end += 1  # expand the window
            else:
                if curr == -1:
                    continue  # still 0 still big gap
                ranges.append((get_time(curr), get_time(end)))
                curr = -1
                end = -1

        # Don't forget to append the last range if it ends at the last slot
        if curr != -1:
            ranges.append((get_time(curr), get_time(end)))

        schedule[day] = ranges

    classes_in_schedule = []
    classes_with_best_rmp = []
    # get all the free classes
    for requested_classes in request.courses.split(","):
        classes = await get_open_classes_for(requested_classes)
        for potential_class in classes:
            # calc the rmp
            rmp_result = await get_instructor_rating(
                potential_class["instructor"], count=1
            )
            rmp_dict = rmp_result[0]
            avg_rating = rmp_dict["avgRating"]
            avg_difficulty = rmp_dict["avgDifficulty"]

            potential_class["rating"] = avg_rating
            potential_class["difficulty"] = avg_difficulty

            classes_with_best_rmp.append(potential_class)
            classes_with_best_rmp = sorted(
                classes_with_best_rmp, key=lambda x: (-x["rating"], x["difficulty"])
            )

            # calc if in schedule
            days = potential_class["days"]
            start_time = potential_class["start_time"]
            end_time = potential_class["end_time"]
            for day in days:
                # compare start and end time with schedule
                match day:
                    case "M":
                        day = "Monday"
                    case "T":
                        day = "Tuesday"
                    case "W":
                        day = "Wednesday"
                    case "R":
                        day = "Thursday"
                    case "F":
                        day = "Friday"

                for schedule_start, schedule_end in schedule[day]:
                    if (
                        min(schedule_start, get_time_from_str(start_time))
                        == schedule_start
                        and max(schedule_end, get_time_from_str(end_time))
                        == schedule_end
                    ):
                        # valid class for schedule
                        classes_in_schedule.append(potential_class)

    logging.info(classes_in_schedule)
    logging.info(classes_with_best_rmp)

    return {"status": "success", "data": "hi"}


# @app.get("/api/ge_areas")
# async def get_all_ge_areas():
#     """Get all available GE Areas."""
#     areas = await get_ge_areas()
#     return {"status": "success", "areas": areas}


@app.get("/api/ge_courses/{area}")
async def get_ge_classes(area: str):
    """Get all courses for a specific GE Area."""
    courses = await get_courses_by_ge(area)
    return {"status": "success", "courses": courses}


@app.get("/api/open_ge_classes/{area}")
async def get_open_ge_classes_endpoint(area: str):
    """Get all open class sections satisfying a GE Area."""
    classes = await get_open_ge_classes(area)
    return {"status": "success", "classes": classes}


# @app.get("/api/major_exceptions/{major}")
# async def get_major_exceptions_endpoint(major: str):
#     """Get GE area exceptions/waivers for a given major."""
#     exceptions = get_major_ge_exceptions(major)
#     return {"status": "success", "exceptions": exceptions}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
