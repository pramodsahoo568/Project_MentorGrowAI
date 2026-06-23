'''
The main.py file is used for offline execution and Testing.
'''

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import TypedDict, Literal, Annotated,Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.tools import tool
from langgraph.prebuilt import ToolNode
import operator
import json
import time
load_dotenv()

from server.agents.graph_builder import generate_questions, evaluate_performance, AgentState, IntentType

def get_final_ai_response(state):
    from langchain_core.messages import AIMessage

    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return message.content
    return None

'''
def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.
'''
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    questions = generate_questions("Please generate 10 practice questions for AWS AI Practitioner Domain 1","abc@gmial.com")
    print(f"questions: {questions}")
    '''
    result = evaluate_performance("Please Evaluate Exam Readiness for AWS AI Practitioner Exam","abc@gmial.com")
    print(f'Final AI Response:{get_final_ai_response(result)}')
    '''


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
