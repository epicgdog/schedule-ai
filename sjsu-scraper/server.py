from scraper import database
from google import genai
from google.genai import types
import sqlite3
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def query_database(query: str) -> str:
    """
    Query the sjsu_classes.db SQLite database to answer user questions about the schedule.
    The table name is 'classes'.
    
    Schema:
    - id INTEGER PRIMARY KEY
    - course_name TEXT NOT NULL (e.g., 'CS 146', 'MATH 30')
    - class_number INTEGER NOT NULL UNIQUE (The section ID)
    - days TEXT (e.g., 'MW', 'TR', 'TBA')
    - times TEXT (e.g., '09:00AM-10:15AM')
    - instructor TEXT
    - open_seats INTEGER NOT NULL
    
    Args:
        query: A valid SQL query string (e.g. "SELECT * FROM classes WHERE course_name LIKE '%CS 146%'").
    Returns:
        String representation of the query results.
    """
    try:
        logger.info(f"Executing SQL: {query}")
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            if not rows:
                return "No results found."
            # Limit results to avoid blowing up context if the query is too broad
            if len(rows) > 50:
                 return f"Found {len(rows)} rows. Here are the first 50: {str(rows[:50])}"
            return str(rows)
    except Exception as e:
        return f"Error executing query: {e}"

# Create a chat session with the tool enabled
chat = client.chats.create(
    model="gemini-2.5-flash", # Using a capable model for SQL generation
    config=types.GenerateContentConfig(
        tools=[query_database],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
        system_instruction="You are a helpful assistant that answers questions about the SJSU class schedule. Use the query_database tool to find information. Always check the database schema. When a user asks about a class, try searching by proper name or partial matches."
    )
)

print("Ask me about the schedule! (Type 'quit' to exit)")
while True:
    try:
        user_txt = input("You: ")
        if user_txt.lower() in ['quit', 'exit']:
            break
            
        print("Bot: ", end="", flush=True)
        response = chat.send_message(user_txt)
        print(response.text)
        
    except Exception as e:
        logging.error(f"Error: {e}")