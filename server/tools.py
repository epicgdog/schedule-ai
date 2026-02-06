import re
import sqlite3
from langchain.tools import tool
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# tool to interact with the sql
def get_major_description(major : str):
    """
    Connects to the database to get the major's description, with all of the required classes and what a student should take. Returns 

    :param major: string, name of the major of the student in the format major, type of degree
    """

    with sqlite3.connect(os.getenv("DATABASE")) as conn:
        cursor = conn.cursor()
        sql = """SELECT description FROM reqs WHERE course_name = ?"""
        cursor.execute(sql, (major,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        return "No description found."


def format_tool_to_prompt():
    """Collect and format all tools in the file as a single string for prompts."""
    # Use the available_tools dictionary
    available_tools = {
        "get_major_description": get_major_description,
    }

    # Initialize a list to hold tool metadata
    tool_descriptions = []

    for tool_name, tool in available_tools.items():
        # Collect name, description, and arguments schema for each tool
        name = tool_name
        description = (
            tool.__doc__.strip() if tool.__doc__ else "No description available."
        )
        args = (
            tool.args_schema.model_json_schema() if hasattr(tool, "args_schema") else {}
        )

        # Format metadata
        tool_metadata = (
            f"""Name: {name}\nDescription: {description}\nArguments: {args}"""
        )
        tool_descriptions.append(tool_metadata)

    # Join all tools into a single formatted string
    return "\n\n".join(tool_descriptions)

def extract_tool_call(text):
    import io
    from contextlib import redirect_stdout
 
    pattern = r"```tool_code\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        # Capture stdout in a string buffer
        f = io.StringIO()
        with redirect_stdout(f):
            result = eval(code)
        output = f.getvalue()
        r = result if output == '' else output
        return f'```tool_output\n{r}\n```'''
    return None

# def extract_tool_call(text):
#     """Extract and execute tool calls from LLM response.

#     The LLM should output tool calls like:
#         ```tool_code
#         retrieve_context("your query here")
#         ```

#     Supports:
#         - Single string argument: retrieve_context("query")
#         - Keyword arguments: retrieve_context(query="query")
#         - Multiple arguments: some_tool("arg1", "arg2", key="value")
#     """
#     # Registry of available tools
#     available_tools = {
#         "get_major_description": get_major_description,
#     }

#     pattern = r"```tool_code\s*(.*?)\s*```"
#     match = re.search(pattern, text, re.DOTALL)

#     if not match:
#         logging.warning("No tool call found in response")
#         return None

#     code = match.group(1).strip()
#     logging.info(f"Parsing tool call: {code}")

#     # Parse the function call: function_name(args)
#     func_pattern = r"^(\w+)\s*\((.*)\)$"
#     func_match = re.match(func_pattern, code, re.DOTALL)

#     if not func_match:
#         logging.error(f"Invalid tool call format: {code}")
#         return f"```tool_output\nError: Invalid tool call format. Expected: function_name(args)\n```"

#     func_name = func_match.group(1)
#     args_str = func_match.group(2).strip()

#     # Check if tool exists
#     if func_name not in available_tools:
#         logging.error(f"Unknown tool: {func_name}")
#         return f'```tool_output\nError: Unknown tool "{func_name}". Available tools: {list(available_tools.keys())}\n```'

#     tool = available_tools[func_name]

#     try:
#         # Parse arguments - handle both positional and keyword args
#         tool_input = parse_tool_arguments(args_str, tool)
#         logging.info(f"Invoking {func_name} with: {tool_input}")

#         # Use .invoke() method for LangChain StructuredTool
#         result = tool.invoke(tool_input)

#         # Handle tuple return from content_and_artifact tools
#         if isinstance(result, tuple):
#             content, artifact = result
#             logging.info(f"Tool returned {len(artifact)} documents")
#             return f"```tool_output\n{str(content).strip()}\n```"

#         return f"```tool_output\n{str(result).strip()}\n```"

#     except Exception as e:
#         logging.error(f"Error executing tool {func_name}: {e}")
#         return f"```tool_output\nError executing {func_name}: {str(e)}\n```"


def parse_tool_arguments(args_str: str, tool) -> dict:
    """Parse tool arguments string into a dictionary for .invoke().

    Handles:
        - Empty args: ""
        - Single string: "my query"
        - Keyword args: query="my query"
        - Mixed args: "value", key="other"
    """
    if not args_str:
        return {}

    # Get the expected parameter names from the tool's schema
    schema = tool.args_schema.model_json_schema()
    param_names = list(schema.get("properties", {}).keys())

    # Try to parse as Python literal using ast for safety
    import ast

    args = []
    kwargs = {}

    # Handle keyword arguments pattern: key="value" or key='value'
    kwarg_pattern = r"(\w+)\s*=\s*"

    # Split by comma, but respect quoted strings
    # Use a simple state machine to handle this
    tokens = tokenize_args(args_str)

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # Check if it's a keyword argument
        kwarg_match = re.match(r"^(\w+)\s*=\s*(.+)$", token, re.DOTALL)
        if kwarg_match:
            key = kwarg_match.group(1)
            value = kwarg_match.group(2).strip()
            kwargs[key] = parse_value(value)
        else:
            # Positional argument
            args.append(parse_value(token))

    # Build the final dict - map positional args to parameter names
    result = {}
    for i, arg in enumerate(args):
        if i < len(param_names):
            result[param_names[i]] = arg

    # Add keyword args (these override positional if same name)
    result.update(kwargs)

    return result


def tokenize_args(args_str: str) -> list:
    """Split arguments by comma, respecting quoted strings."""
    tokens = []
    current = ""
    in_quotes = False
    quote_char = None
    paren_depth = 0

    for char in args_str:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
            current += char
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
            current += char
        elif char == "(" and not in_quotes:
            paren_depth += 1
            current += char
        elif char == ")" and not in_quotes:
            paren_depth -= 1
            current += char
        elif char == "," and not in_quotes and paren_depth == 0:
            tokens.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        tokens.append(current.strip())

    return tokens


def parse_value(value_str: str):
    """Parse a string value into its Python type."""
    import ast

    value_str = value_str.strip()

    # Try to evaluate as a Python literal (handles strings, numbers, lists, dicts)
    try:
        return ast.literal_eval(value_str)
    except (ValueError, SyntaxError):
        # If it fails, return as-is (raw string)
        return value_str


#### tool integration with gemma3

# logging.info("Calling LLM")
# ai_msg = llm.invoke(messages)
# tool_result = extract_tool_call(ai_msg.content)

# while tool_result:
#     logging.info(f"{tool_result} was the result of the tool call")
#     messages.append(("user", tool_result))
#     ai_msg = llm.invoke(messages)
#     tool_result = extract_tool_call(ai_msg.content)

# logging.info("No tool call detected, LLM responded directly")
# logging.info(f"{ai_msg.content} is the final result")


# # sqlite integration; don't need embeddings since we just store a link
# database = os.getenv("DATABASE")
# create_table = """
# CREATE TABLE IF NOT EXISTS reqs (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     course_name TEXT NOT NULL,
#     description TEXT
# )
# """

# try:
#     with sqlite3.connect(database) as conn:
#         cursor = conn.cursor()
#         cursor.execute(create_table)
#         conn.commit()
#         logging.info("db successfully made")

# except sqlite3.OperationalError as e:
#     logging.error(e)

# # only look for the actual requirements
# # TODO: need to extend this to every single link and stuff.
# url = "https://catalog.sjsu.edu/preview_program.php?catoid=13&poid=7663"
# logging.info(f"Loading webpage: {url}")
# bs4_strainer = bs4.SoupStrainer(class_="acalog-core")
# loader = WebBaseLoader(
#     web_paths=(url,),
#     bs_kwargs={"parse_only": bs4_strainer},
# )
# docs = loader.load()
# logging.info(f"Loaded {len(docs)} document(s) from webpage")
# assert len(docs) >= 1

# cursor.execute('''
#     INSERT INTO reqs (course_name, description)
#     VALUES              (?, ?)
# ''', ("Computer Science", docs[0].page_content))
# conn.commit()
