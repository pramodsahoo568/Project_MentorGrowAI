from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, EmailStr
from typing import TypedDict, Literal, Annotated,Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.tools import tool
from langgraph.prebuilt import ToolNode
from rag.document_retrieval_pipeline import retrieve_results
import operator
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
    messages: Annotated[list[BaseMessage], operator.add]
    user_id: str
    intent: str
    # Question Flow Data
    domain: Optional[str]
    count:int
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
    # agent response
    response: str


# Tools
@tool
def evaluate_test_readiness(user_id: str) -> dict:
    """ evaluate certification exam readiness and provide report"""
    return {"user_id": user_id, "readiness_score": 60}


# Setup
tools = [evaluate_test_readiness]

llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.7,top_p=0.9)
llm_with_tools = llm.bind_tools(tools)


## Create SuperVisor-pattern Agent
## Add new node for routing decision
# 2. Intent Classifier Node
def intent_classifier_agent_node(state: AgentState):
    """Intent Classifier Node: this is rule based Mock implementation- need to be used Local LLM  or classifier latter"""
    print("Function: intent_classifier_agent_node")
    # In production, look up user in database
    # For now, mock based on message content
    messages = state["messages"]
    user_input = messages[-1].content.lower()
    print("User Input:", user_input)
    intent = "unknown"
    domain = None
    difficulty = "medium"
    count = 10

    if "question" in user_input:
            intent= "generate_questions"
    elif "evaluate" in user_input or "performance" in user_input:
            intent = "evaluate_readiness"
    else:
        intent =  "unknown"

    if "domain 1" in user_input:
        domain = "Domain 1"
    elif "domain 2" in user_input:
        domain = "Domain 2"
    elif "domain 3" in user_input:
        domain = "Domain 3"
    elif "domain 4" in user_input:
        domain = "Domain 4"
    elif  "full exam"in user_input or "complete test" in user_input:
        domain = "Full Exam"
        count = 65;


    return {
        "intent": intent,
        "domain": domain,
        "count": count,
        "difficulty": difficulty
    }


# 3. Routing by intent function
def route_by_intent(state: AgentState) -> str:
    """Route based on intent"""
    if state.get("intent") == "generate_questions":
        return "generate_question_path"
    if state.get("intent") == "evaluate_readiness":
        return "evaluate_performance_path"
    else:
        return "unknown"

import yaml
from pathlib import Path
def load_prompt(version="prompt_v1.yaml"):
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / version
    try:
        with open(prompt_path, "r") as f:
            data = yaml.safe_load(f)
        return data

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}"
        )

## Generate Questions agent node
def generate_questions_agent_node(state: AgentState):
    ''' Generate Question Agent'''
    print("Function: intent_classifier_agent_node")
    domain = state.get("domain", "none")
    difficulty = state.get("difficulty_level", "none")
    count = state.get("count", 10)
    print("Domain:", domain)
    print("difficulty:", difficulty)
    print("count:", count)


    # -------------------------
    # Retrieve RAG context
    # -------------------------
    query = f"What is syllabus for {domain} in AWS AI Practitioner exam?"
    print("##Query:", query)
    results = retrieve_results(query)

    # Extract only document text (ignore score for prompt)
    context_chunks = []
    for doc, score in results:
        context_chunks.append(doc.page_content.strip())

    # Join context safely
    context = "\n\n".join(context_chunks)
    print("Retrieved Context Length:", len(context))
    print("Context:", context)

    # -------------------------
    # Build LLM Prompt
    # -------------------------

    ###  read from YAML files
    prompt_data = load_prompt("prompt_v1.yaml")
    if not prompt_data:
        raise ValueError("Prompt file is empty.")

    system_template = prompt_data["system_template"]
    print("system_template: ",system_template)

    if "Domain" in domain:
        human_template = prompt_data["human_templates"]["domain_standard"]
    if "Full Exam" in domain:
        human_template = prompt_data["human_templates"]["full_exam"]

    print("##human_template: ",human_template)

    system_text = system_template.format(context=context)
    human_text = human_template.format(
        count=count,
        domain=domain
    )
    print(f"human_text:{human_text}")
    messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=human_text)
    ]
    print("##Messages:", messages)

    ###
    print("Call LLM invoke")
    response = llm.invoke(messages)
    # questions = json.load(response.content)

    print("###response from llm: ", response)
    return {"response": response}
    return {"messages": [response]}


# Nodes
def evaluate_agent_node(state: AgentState):
    ''' Evaluate agent node'''
    messages = state["messages"]

    # If last message is ToolMessage → generate final response
    if isinstance(messages[-1], ToolMessage):
        tool_result = messages[-1].content

        final_response = llm.invoke([
            SystemMessage(content="Summarize readiness result clearly."),
            HumanMessage(content=f"Tool returned: {tool_result}")
        ])

        return {"messages": [final_response]}

    # Otherwise → first LLM call
    user_input = messages[-1].content

    response = llm_with_tools.invoke([
        SystemMessage(content="""
    If user asks about exam readiness,
    call the tool evaluate_test_readyness.
    Do not answer directly.
    """),
        HumanMessage(content=user_input)
    ])

    return {"messages": [response]}


'''
user Message
Please Evaluate Answer: 
please Evaluate the Answers: Answers:
Please provide 10 practice questions for AWS AI Practitioner Domain 2:
Please generate 20 practice questions for AWS AI Practitioner Domain 1:
'''


def route_after_tool(state: AgentState):
    return "evaluate_agent_node"


def route_after_evaluate(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]

    # If AIMessage has tool_calls → go to tools
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    # Otherwise → stop
    return END


def build_stategraph():
    ## build graph
    print("Create StateGraph")
    workflow = StateGraph(AgentState)

    ## Add Nodes
    workflow.add_node("intent_classifier_agent_node", intent_classifier_agent_node)
    workflow.add_node("generate_questions_agent_node", generate_questions_agent_node)
    workflow.add_node("evaluate_agent_node", evaluate_agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "intent_classifier_agent_node")

    #    conditional edge :route_by_intent
    workflow.add_conditional_edges(
        "intent_classifier_agent_node",
        route_by_intent,
        {
            "generate_question_path": "generate_questions_agent_node",
            "evaluate_performance_path": "evaluate_agent_node"
        }
    )
    workflow.add_edge("generate_questions_agent_node", END)

    workflow.add_conditional_edges(
        "evaluate_agent_node",
        route_after_evaluate,
        {
            "tools": "tools",
            END: END
        }
    )

    workflow.add_edge("tools", "evaluate_agent_node")

    ## Add  Edges to Connect Nodes - simple flow
    ##workflow.add_edge(START, "intent_classifier_agent_node")
    ##workflow.add_edge("intent_classifier_agent_node","generate_questions_agent_node")
    ##workflow.add_edge("generate_questions_agent_node", END)

    graph = workflow.compile()
    return graph


def save_graph(graph):
    graph_path = "aws_mock_workflow_graph_with_tool.png"
    print(f"Save StateGraph:{graph_path}")
    graph.get_graph().draw_mermaid_png(output_file_path=graph_path)


# Run
# Test Generate Questions
def generate_questions(message: str,user_id:EmailStr):
    print("##Generate Questions")
    graph = build_stategraph()

    save_graph(graph)
    print("Invoke StateGraph")
    print("Testing Generate Questions flow")
    result = graph.invoke({
        "messages": [HumanMessage(content=message)],
        "user_id": user_id
    })
    print(f"###Result: {result}")
    print(f"response: {result['response'].content}")
    return result['response'].content


def evaluate_performance(message: str,user_id:EmailStr):
    print("Evaluate Performance")
    graph = build_stategraph()
    save_graph(graph)
    print("Invoke StateGraph")
    print("Testing Evaluate performance flow")
    result = graph.invoke({
        "messages": [HumanMessage(content=message)],
        "user_id": user_id
    })
    print(f"###Result: {result}")
    return result


def get_final_ai_response(state):
    from langchain_core.messages import AIMessage

    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return message.content
    return None