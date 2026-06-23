
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()
# Configure your API Key (Best practice is using environment variables)



async def ask_openai(prompt: str):
    """
    Python equivalent of your Node.js askGemini function.
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.7
        )

        response = llm.invoke([
            HumanMessage(content=prompt)
        ])

        return response.content

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return "Error: Could not reach the AI server."