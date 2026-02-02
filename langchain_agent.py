from langchain_ollama import ChatOllama
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def add_prompt(txt):
    return f'''

At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. The python methods described below are imported and available, you can only use defined methods. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it to call more tools or generate a helpful, friendly response. When using a ```tool_call``` think step by step why and how it should be used.

The following Python methods are available:

```python
def fetch_weather_today():
    """Gets the current weather in San Jose"""
```


User:  {txt}'''

def fetch_weather_today():
    """Get the current weather in San Jose"""

    url = "https://wttr.in/San%20Jose?format=%C+%t"

    try:
        response = requests.get(url)
        response.raise_for_status()
        weather_data = response.text.strip()
        logging.info(weather_data)
        return f"The current weather in San Jose is: {weather_data}"
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch weather data: {e}")
        return f"Failed to fetch weather data: {e}"

def main():
    logging.info("Starting the main function")
    llm = ChatOllama(
        model="gemma3:12b",
        temperature=0,
    )

    messages = [
        (
            "system",
            "You are a helpful assistant.",
        ),
        ("user", add_prompt("What is the weather in San Jose today?")),
    ]
    logging.info("Sending messages to the language model")
    ai_msg = llm.invoke(messages)
    logging.info("Received response from the language model")

    print(ai_msg.content)

if __name__ == "__main__":
    main()