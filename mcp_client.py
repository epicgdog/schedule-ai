import asyncio
import sys
import os
import logging
from contextlib import AsyncExitStack


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from smolagents import CodeAgent, ToolCallingAgent, OpenAIModel, MCPClient


from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Test data
test_classes_list = ["pols 15", "math 42"]

system_prompt = """
You are an intelligent Academic Scheduling Assistant. Your goal is to construct the optimal weekly class schedule based on a provided list of raw course data (in JSON-like format).

### CRITICAL: TOOL CALLING CONVENTION
When calling any tool, you MUST use keyword arguments, NOT positional arguments.
- CORRECT: `get_open_classes_for(course_name="POLS 15")`
- WRONG: `get_open_classes_for("POLS 15")`
- CORRECT: `get_instructor_rating(query="John Smith")`
- WRONG: `get_instructor_rating("John Smith")`

### CORE RESPONSIBILITIES
1.  **Analyze Availability:** You must strictly filter out any class where `open_seats` is 0 or less.
2.  **Course Uniqueness:** You must schedule exactly **one** section for each unique `course_name`. Do not schedule duplicates of the same course (e.g., do not schedule two different Math 42 classes).
3.  **Instructor Optimization:**
    * You have access to a tool named `get_instructor_rating`.
    * For every potential class with open seats, you must verify the instructor's rating using this tool.
    * When choosing between multiple sections of the same `course_name`, prioritize the section taught by the instructor with the highest rating.
4.  **Day Parsing:** You must correctly interpret day codes:
    * `M` = Monday
    * `T` = Tuesday
    * `W` = Wednesday
    * `R` = Thursday
    * `F` = Friday
    * Combinations (e.g., `MW` = Monday and Wednesday; `TR` = Tuesday and Thursday) must result in the class appearing under *each* respective day in the final output.

### OUTPUT FORMATTING
You must output the schedule grouped by Day of the Week (Monday through Friday). Do not display days where no classes are scheduled.

**Format Structure:**
**{Day Name}:**
{Start Time}-{End Time}: {Course Name} Section {Section Number} with {Instructor Name} ({Rating Value})

**Separators:**
Use `-------` to separate days.

### EXAMPLE EXECUTION
**Input Data:**
{ "course_name": "CS 146", "section_number": 1, "days": "MW", "times": "10:30AM-11:45AM", "instructor": "Navrati Saxena", "open_seats": 10 }
{ "course_name": "CS 151", "section_number": 5, "days": "MW", "times": "04:30PM-05:45PM", "instructor": "Robert Nicholson", "open_seats": 15 }

**Internal Logic:**
1. Check seats: Both > 0. Use the get_open-classes_for tool to find these.
2. Check Ratings: Saxena (4.5), Nicholson (3.9).
3. Map Days: MW -> Monday entries and Wednesday entries.

**Final Output:**
**Monday:**
10:30AM-11:45AM: CS 146 Section 1 with Navrati Saxena (4.5/5)
04:30PM-5:45PM: CS 151 Section 5 with Robert Nicholson (3.9/5)

-------

**Wednesday:**
10:30AM-11:45AM: CS 146 Section 1 with Navrati Saxena (4.5/5)
04:30PM-5:45PM: CS 151 Section 5 with Robert Nicholson (3.9/5)

### INSTRUCTIONS FOR HANDLING THE USER PROMPT
The user will provide the list of classes. You will process them according to the rules above and generate the schedule.
"""


basic_system_prompt = '''
You are a helpful assitant designed to help students with classes. You will be given a list of classes that a student will be taking.

'''

basic_user_prompt = '''
Find an open class for each class provided in the list, remember the professor and dates of the class. Then, use the professors name and find their rating.
Now, provide a schedule for the studnet, with the best possible professors. 
If one is not possible, let the student known as soon as possible, do not do any more extra steps.
\n
'''

def run_agent(list_of_classes) -> str:
    """Run the smolagents CodeAgent with MCP tools."""
    server_params = StdioServerParameters(
        command=sys.executable, args=["mcp_server.py"], env=None
    )

    # Uses HF_TOKEN from environment automatically
    # Default model: Qwen/Qwen3-Next-80B-A3B-Thinking (free tier: $0.10/month)
    model = OpenAIModel(
        model_id="deepseek-r1:14b-qwen-distill-q4_K_M",
        api_base="http://100.72.139.71:11434/v1",
        api_key="ollama",
    )

    logger.info("Initialized model: %s", model.model_id)

    with MCPClient(server_params, structured_output=False) as tools:
        logger.info("Loaded %d tools from MCP server", len(tools))

        agent = ToolCallingAgent(
            tools=tools,
            model=model,
            max_steps=10,
            verbosity_level=2,
            instructions=basic_system_prompt,
        )
        result = agent.run(
            basic_user_prompt + f"Here's the list of classes:" +  ' '.join(list_of_classes)
        )

        logger.info("Agent completed task")
        return result


async def main():
    logger.info("Starting schedule generation for classes: %s", test_classes_list)

    # Step 2: Run agent with the prompt
    result = run_agent(test_classes_list)

    logger.info("=" * 50)
    logger.info("FINAL SCHEDULE:")
    logger.info("=" * 50)
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
