from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
import logging

from dotenv import load_dotenv
import os
import tools
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


llm = ChatOpenAI(
    model="gemma3:12b",
    temperature=0.1,
    base_url=os.getenv("LOCAL_IP_KEY"),
    api_key="ollama",
    max_tokens=2048,
    timeout=120
)

system_prompt = (
    "You have access to a tool that retrieves "
)
agent = create_agent(llm, tools, system_prompt=(""))

'''
# At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used.
# The following Python methods are available: {tools.format_tool_to_prompt()}\n'''

base_prompt = f'''

# At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used.
# The following Python methods are available:
def get_major_description(major : str):
    """
    Connects to the database to get the major's description, with all of the required classes and what a student should take. Returns 

    :param major: string, name of the major of the student in the format major, type of degree
    """

Generate a list of classes the user has taken. Then, using your knowledge of their major, look for and generate a list of required classes for the major.
# User's transcript:\n
# '''

def invoke(transcript_str):

    messages = [
        ("system", "You are a helpful AI assistant"),
        ("user", base_prompt + (transcript_str))
    ]
    
    logging.info("Calling LLM")
    ai_msg = llm.invoke(messages)
    # tool_result = tools.extract_tool_call(ai_msg.content)

    # reps = 0
    # while tool_result or reps < 5:
    #     logging.info(f"{tool_result} was the result of the tool call")
    #     messages.append(("user", tool_result))
    #     ai_msg = llm.invoke(messages)
    #     tool_result = tools.extract_tool_call(ai_msg.content)
    #     reps += 1

    logging.info("No tool call detected, LLM responded directly")
    return ai_msg