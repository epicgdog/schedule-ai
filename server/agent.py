from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize LLM
llm = ChatOpenAI(
    model="gemma3:12b",
    temperature=0.1,
    base_url=os.getenv("LOCAL_IP_KEY"),
    api_key="ollama",
    timeout=120,
)

extract_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a transcript parser. Extract the major and list of classes taken from the transcript.",
        ),
        (
            "user",
            """Parse the following transcript and extract:
1. The student's major (as listed in the transcript)
2. A list of all classes the student has taken and passed

Transcript:
{transcript}

Return ONLY a JSON object in this exact format:
{{
    "major": "extracted major name",
    "classes_taken": ["Class Code: Class Name", "Class Code: Class Name", ...]
}}

Be thorough and extract ALL classes mentioned in the transcript.""",
        ),
    ]
)

def invoke(transcript_str: str) -> str:
    """
    Analyze a transcript using structured prompt chaining.

    Args:
        transcript_str: The student's transcript text

    Returns:
        A detailed analysis of completed vs required classes
    """
    logging.info("Starting transcript analysis...")

    # Step 1: Extract major and classes from transcript
    logging.info("Step 1: Extracting data from transcript...")
    extract_chain = extract_prompt | llm | JsonOutputParser()
    extracted_data = extract_chain.invoke({"transcript": transcript_str})

    major = extracted_data["major"]
    classes_taken = extracted_data["classes_taken"]

    # return analysis