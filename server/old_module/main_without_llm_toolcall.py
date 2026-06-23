# This is a sample Python script.

# Press F6 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import TypedDict, Literal, Annotated,Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.tools import tool
from langgraph.prebuilt import ToolNode
import json
import time
load_dotenv()



IntentType = Literal[
    "generate_questions",
    "start_full_mock_test",
    "evaluate_readiness",
    "show_progress",
    "revise_weak_topics",
    "continue_session",
    "help",
    "unknown"
]

## Create An Agent State

class AgentState(TypedDict):
    message: str
    user_id: str
    intent:str
    # Question Flow Data
    domain: Optional[str]
    difficulty_level: Optional[str]
    questions: Optional[list]
    user_answers: Optional[dict]
    # Evaluation Data
    score: Optional[float]
    domain_scores: Optional[dict]
    weak_concepts: Optional[list]
    # Progress / Readiness
    readiness_score: Optional[float]
    progress_summary: Optional[dict]
    #agent response
    response: str

# Tools
@tool
def evaluate_test_readyness(user_id: str) -> dict:
    """ evaluate certification exam readyness and provide report"""
    return {"user_id": user_id, "readiness_score": 60}

# Setup
tools = [evaluate_test_readyness]

llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)
llm_with_tools = llm.bind_tools(tools)


## Create SuperVisor-pattern Agent
## Add new node for routing decision
# 2. Intent Classifier Node
def intent_classifier_agent_node(state: AgentState):
    """Intent Classifier Node: Mock implementation- need to be used Local LLM  or classifier latter"""
    print("Function: intent_classifier_agent_node")
    # In production, look up user in database
    # For now, mock based on message content
    user_input = state["message"].lower()
    print("User Input:", user_input)
    if "questions" in user_input :
        return {
                "intent": "generate_questions",
                "domain": "Domain 1",
                "difficulty": "medium",
                }
    elif "evaluate" in user_input or "performance" in user_input:
        return {
            "intent": "evaluate_readiness",
            "domain": "Domain 1",
            "difficulty": "medium",
        }
    else:
        return {"intent":"unknown"}

# 3. Routing function
def route_by_intent(state: AgentState) -> str:
    """Route based on intent"""
    if state.get("intent") == "generate_questions":
        return "generate_question_path"
    if state.get("intent") == "evaluate_readiness":
        return "evaluate_performance_path"
    else:
        return "unknown"


# 4. VIP-specific node (auto-resolves)
def generate_questions_agent_node(state: AgentState):
    ''' Generate Question Agent'''
    print("Function: intent_classifier_agent_node")
    domain = state.get("domain","none")
    difficulty = state.get("difficulty_level", "none")
    print("Domain:", domain)
    print("difficulty:", difficulty)
    count = 10

    messages = [
        SystemMessage(content="""
    You are an AWS AI Practitioner Certification(AIF-C01) Exam Question Generator.
    Always return valid JSON.
    Never include markdown or explanation.
        """),
        HumanMessage(content=f"""
    Generate {count} multiple-choice questions.
    Domain: {domain}
    Requirements:
    
    Return JSON list only.
    """)
    ]
    print("Call LLM invoke")
    response = llm.invoke(messages)
    #questions = json.load(response.content)

    print("###response from llm: ",response)
    return {"response": response}
    return {"messages": [response]}


# Nodes
def evaluate_agent_node(state: AgentState):
    ''' Evaluate agent node'''
    print("Function-> evaluate_agent_node")
    messages = state["message"] +" "+"user_id:"+ state["user_id"]
    print("input to llm Messages:",messages)
    ##response = llm_with_tools.invoke(messages)

    tool_result = evaluate_test_readyness.invoke({
        "user_id": state["user_id"]
    })

    return {
        "readiness_score": tool_result["readiness_score"],
        "response": f"Your readiness score is {tool_result['readiness_score']}%"
    }
'''
user Message
Please Evaluate Answer: 
please Evaluate the Answers: Answers:
Please provide 10 practice questions for AWS AI Practitioner Domain 2:
Please generate 20 practice questions for AWS AI Practitioner Domain 1:
'''




## build graph
print("Create StateGraph")
workflow = StateGraph(AgentState)

## Add Nodes
workflow.add_node("intent_classifier_agent_node",intent_classifier_agent_node)
workflow.add_node("generate_questions_agent_node", generate_questions_agent_node)
workflow.add_node("evaluate_agent_node", evaluate_agent_node)
##workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "intent_classifier_agent_node")

# conditional edge :route_by_intent
workflow.add_conditional_edges(
    "intent_classifier_agent_node",
    route_by_intent,
    {
        "generate_question_path": "generate_questions_agent_node",
        "evaluate_performance_path": "evaluate_agent_node"
    }
)

workflow.add_edge("evaluate_agent_node",END)
workflow.add_edge("generate_questions_agent_node", END)


## Add  Edges to Connect Nodes - simple flow
##workflow.add_edge(START, "intent_classifier_agent_node")
##workflow.add_edge("intent_classifier_agent_node","generate_questions_agent_node")
##workflow.add_edge("generate_questions_agent_node", END)



graph = workflow.compile()
print("Save StateGraph")
graph.get_graph().draw_mermaid_png(output_file_path="aws_certification_mock_workflow_graph.png")
# Run
# Test Generate Questions
'''
print("Testing Generate Questions flow")
result = graph.invoke({
    "message": "Please generate 20 practice questions for AWS AI Practitioner Domain 1",
    "user_id":"abc@gmail.com"
})
print(f"###Result: {result}")
print(f"response: {result['response'].content}")

'''

print("Testing Evaluate performance flow")
result = graph.invoke({
    "message": "Please Evaluate Exam Readyness for AWS AI Practitioner Exam",
    "user_id":"abc@gmail.com"
})
print(f"###Result: {result}")


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
#if __name__ == '__main__':
#    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
