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
from concurrent.futures import ThreadPoolExecutor
from server.database.db_question_repository import save_question_set
from server.classifiers.intent_classifier import rule_based_classifier
##from server.classifiers.llm_intent_classifier import llm_intent_classifier
from server.database.redis_session_manager import session_manager
from server.database.db_mocktest_repository import get_test_result_data
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
    session_id:str
    exam_name:Optional[str]
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
    performance_data: dict
    # agent response
    response: str

from pydantic import BaseModel
from typing import List, Literal

class QuestionSchema(BaseModel):
    question: str
    options: List[str]
    correct_answers: List[str]
    type: Literal["single", "multiple_response"]
    domain: str

class QuestionList(BaseModel):
    count: int
    questions: List[QuestionSchema]



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

    ## Using Rules based classifier
    result  = rule_based_classifier(user_input)

    ##result = llm_intent_classifier(user_input)

    print("Parsed intent:", result)

    return {
        "intent": result.get("intent", "unknown"),
        "exam_name": result.get("exam_name"),
        "domain": result.get("domain"),
        "count": result.get("count", 10)
    }

    return result


# 3. Routing by intent function
def route_by_intent(state: AgentState) -> str:
    """Route based on intent"""
    if state.get("intent") == "generate_questions":
        return "generate_question_path"
    if state.get("intent") == "evaluate_result":
        return "evaluate_performance_path"
    if state.get("intent") == "evaluate_readiness":
        return "evaluate_performance_path"
    else:
        return "unknown"

import yaml
from pathlib import Path
def load_prompt(version="prompt_current.yaml"):
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / version
    try:
        with open(prompt_path, "r") as f:
            data = yaml.safe_load(f)
        return data

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}"
        )

def generate_questions_for_domain(domain, count):
    print(f"Generating questions for {domain} count={count}")

    # Retrieve RAG context
    query = f"What is syllabus for {domain} in AWS AI Practitioner exam?"
    results = retrieve_results(query)

    context_chunks = [doc.page_content.strip() for doc, _ in results]
    context = "\n\n".join(context_chunks)

    #prompt_data = load_prompt("prompt_v1.yaml")
    prompt_data = load_prompt("prompt_current.yaml")

    system_template = prompt_data["system_template"]
    human_template = prompt_data["human_templates"]["domain_standard"]

    system_text = system_template.format(context=context)

    human_text = human_template.format(
        count=count,
        domain=domain
    )

    messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=human_text)
    ]

    #response = llm.invoke(messages)
    structured_llm= llm.with_structured_output(QuestionList)
    response  = structured_llm.invoke(messages)
    print("###response for domain:", response)

    ## store the Question response to Database
    ##save_question_set(response)


    return response

## Generate Questions agent node
def generate_questions_agent_node(state: AgentState):
    ''' Generate Question Agent'''
    print("Function: generate_questions_agent_node")
    domain = state.get("domain", "none")
    difficulty = state.get("difficulty_level", "none")
    count = state.get("count", 10)
    print("Domain:", domain)
    print("difficulty:", difficulty)
    print("count:", count)

    # --------------------------
    # SINGLE DOMAIN
    # --------------------------
    if domain != "Full-Exam":
        response = generate_questions_for_domain(domain, count)
        print("###typeof response:",type(response))
        print("###response:", response)
        #return {"response": response.questions}

        question_records = []

        for q in response.questions:
            question_records.append({
                "question": q.question,
                "options": q.options,
                "correct_answers": q.correct_answers,
                "type": q.type,
                "domain": q.domain
            })
        user_id = state["user_id"]

        session_id = state["session_id"]
        session_manager.save_mocktest(
            user_id=user_id,
            session_id=session_id,
            domain=domain,
            questions=question_records
        )
        response_payload = {
            "intent": "generate_questions",
            "message": None,
            "questions": [q.model_dump() for q in response.questions]
        }

        response_json = json.dumps(response_payload)

        return {"response": response_json}
    # --------------------------
    # FULL EXAM MODE
    # --------------------------

    print("Full exam requested. Running parallel generation.")

    domain_distribution = {
        "Domain 1": 13,
        "Domain 2": 16,
        "Domain 3": 18,
        "Domain 4": 9,
        "Domain 5": 9
    }

    all_results = []

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = [
            executor.submit(generate_questions_for_domain, d, c)
            for d, c in domain_distribution.items()
        ]

        for f in futures:
            result = f.result()
            #print("###mthread result:",result)
            all_results.append(result)


    all_questions = []

    for r in all_results:
        all_questions.extend([q.model_dump() for q in r.questions])

    response = {
        "intent": "generate_questions",
        "questions": all_questions,
        "message": None
    }
    # Convert to JSON string for UI compatibility
    json_response = json.dumps(response)

    return {"response": json_response}

    ##return {"response": all_questions}



# Nodes
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)


def evaluate_agent_node(state: AgentState):
    """
    Performance Evaluation Agent

    Uses performance data retrieved from PostgreSQL
    and generates:

    - Performance Summary
    - Strengths
    - Weak Areas
    - Study Recommendations
    - Learning Plan
    """

    print("evaluate_agent_node")

    performance_data = state.get(
        "performance_data",
        {}
    )

    print("Performance Data:")
    print(performance_data)

    # No test history found
    if not performance_data:

        return {
            "messages": [
                AIMessage(
                    content="""
No mock test history was found.

Please complete at least one mock test before requesting a performance evaluation.
"""
                )
            ]
        }

    final_response = llm.invoke(

        [
            SystemMessage(
                content="""
You are an AWS AI Practitioner Certification Coach.

Analyze the user's mock test performance data and provide:

1. Overall Performance Summary
2. Strengths
3. Areas for Improvement
4. Recommended Study Topics
5. Suggested Learning Plan
6. Next Steps

Guidelines:
- Be encouraging and constructive.
- Focus on weak domains and failed questions.
- Recommend AWS services/topics to review.
- Provide actionable study recommendations.
- Keep the response concise but useful.
- Format using markdown.

Use the following sections:

## Performance Summary

## Strengths

## Areas for Improvement

## Recommended Study Topics

## Suggested Learning Plan

## Next Steps
"""
            ),

            HumanMessage(
                content=f"""
User Performance Data:

{performance_data}

Analyze this data and provide personalized feedback and study recommendations.
"""
            ),
        ]
    )

    print("Generated Performance Summary:")
    print(final_response.content)

    # LangGraph will automatically append
    # this AIMessage to message history
    return {
        "messages": [final_response]
    }


'''user Message
Please Evaluate Answer: 
please Evaluate the Answers: Answers:
Please provide 10 practice questions for AWS AI Practitioner Domain 2:
Please generate 20 practice questions for AWS AI Practitioner Domain 1:
'''

def fallback_agent_node(state: AgentState):
    print("Function: fallback_agent_node")

    response_payload = {
        "intent": "unknown",
        "message": (
            "Sorry, I couldn't understand your request. "
            "You can ask me to generate AWS AI Practitioner practice questions "
            "or evaluate your exam performance."
        ),
        "questions": None
    }

    return {"response": json.dumps(response_payload)}

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
    workflow.add_node("fallback_agent_node", fallback_agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "intent_classifier_agent_node")

    #    conditional edge :route_by_intent
    workflow.add_conditional_edges(
        "intent_classifier_agent_node",
        route_by_intent,
        {
            "generate_question_path": "generate_questions_agent_node",
            "evaluate_performance_path": "evaluate_agent_node",
            "unknown": "fallback_agent_node"
        }
    )
    workflow.add_edge("generate_questions_agent_node", END)
    workflow.add_edge("fallback_agent_node", END)

    workflow.add_conditional_edges(
        "evaluate_agent_node",
        route_after_evaluate,
        {
            "tools": "tools",
            END: END
        }
    )

    workflow.add_edge("tools", "evaluate_agent_node")
    graph = workflow.compile()
    return graph

graph = build_stategraph()
import os
def save_graph(graph):
    graph_path = "aws_mock_workflow_graph_with_tool.png"
    if os.getenv("ENABLE_GRAPH_EXPORT", "false").lower() == "true":
        print(f"Save StateGraph:{graph_path}")
        graph.get_graph().draw_mermaid_png(output_file_path=graph_path)

save_graph(graph)
# Run
# Test Generate Questions
def generate_questions(message: str,user_id:EmailStr, sessionId:str):
    print("##Generate Questions")
    print("Invoke StateGraph")
    result = graph.invoke({
        "messages": [HumanMessage(content=message)],
        "user_id": user_id,
        "session_id": sessionId
    })
    print(f"###Result: {result}")
    #print(f"response: {result['response'].content}")
    return result['response']


from pydantic import EmailStr
from langchain_core.messages import (
    HumanMessage,
    AIMessage
)

def evaluate_performance(
    message: str,
    user_id: EmailStr
):
    """
    Evaluate user's overall mock test performance.

    Flow:
    PostgreSQL
        ↓
    Aggregate Performance Data
        ↓
    StateGraph
        ↓
    LLM Summary
        ↓
    API Response
    """

    print("Evaluate Performance")

    # ----------------------------------
    # Retrieve performance data
    # ----------------------------------

    performance_data = get_test_result_data(
        user_id=user_id
    )

    print("Performance Data:")
    print(performance_data)

    # ----------------------------------
    # Invoke Graph
    # ----------------------------------

    result = graph.invoke({

        "messages": [
            HumanMessage(
                content=message
            )
        ],

        "user_id": user_id,

        "performance_data":
            performance_data
    })

    print("Graph Result:")
    print(result)

    # ----------------------------------
    # Extract AI Summary
    # ----------------------------------

    summary = ""

    for msg in reversed(
        result.get("messages", [])
    ):

        if isinstance(msg, AIMessage):

            summary = msg.content
            break

    # Fallback

    if not summary:

        summary = (
            "Performance evaluation "
            "could not be generated."
        )

    # ----------------------------------
    # Return structured response
    # ----------------------------------

    return {

        "testsTaken":
            performance_data.get(
                "tests_taken",
                0
            ),

        "averageScore":
            performance_data.get(
                "average_score",
                0.0
            ),

        "bestScore":
            performance_data.get(
                "best_score",
                0.0
            ),

        "latestScore":
            performance_data.get(
                "latest_score",
                0.0
            ),

        "weakAreas":
            performance_data.get(
                "weak_domains",
                []
            ),

        "summary":
            summary
    }

from langchain_core.messages import AIMessage

def evaluate_agent_node(state: AgentState):

    print("evaluate_agent_node")

    performance_data = state.get(
        "performance_data",
        {}
    )

    response = llm.invoke([
        SystemMessage(
            content="""
You are an AWS AI Practitioner mentor.

Analyze the user's mock test history and provide:

1. Performance Summary
2. Strengths
3. Weak Areas
4. Study Recommendations
5. Next Steps

Use markdown formatting.
"""
        ),

        HumanMessage(
            content=f"""
User Performance Data:

{performance_data}
"""
        )
    ])

    return {
        "messages": [
            AIMessage(
                content=response.content
            )
        ]
    }
def get_final_ai_response(state):
    from langchain_core.messages import AIMessage

    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return message.content
    return None
