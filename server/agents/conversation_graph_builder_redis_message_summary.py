'''
This module uses a local llm to summarize the old messages using local llm before sending actual query to openAI
'''
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, trim_messages
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, EmailStr
from typing import TypedDict, Literal, Annotated,Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import json
from server.memory.redis_session_manager import RedisSessionManager
from server.memory.postgre_longterm_memory import PostgresChatStore
from langchain_ollama import ChatOllama

from server.memory.redis_session_manager import (
    session_manager
)

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    user_id: str
    session_id: str
    summary: Optional[str]
    retrieved_memories: Optional[list]
    response: str


## max_tokens restrict the llm response length, llm output
llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.7,top_p=0.9, max_tokens=120)

summary_llm = ChatOllama(
    model="llama3.2:latest",
    temperature=0.2
)

''' Trim the message history based on token count'''
def trim_conversation_history(state: ConversationState):
    print("trim_conversation_history")
    # Define token-aware trimmer
    trimmer = trim_messages(
        max_tokens=400,
        strategy="last",
        token_counter=llm,
        allow_partial=False,
        start_on="human"
    )
    # Trim ONLY conversational history
    trimmed_history = trimmer.invoke(
        state["messages"]
    )
    return trimmed_history

def getMessageSummary(state: ConversationState):

    print("getMessageSummary")

    messages = state["messages"]

    # ---------------------------------------------
    # Convert messages to plain text
    # ---------------------------------------------
    conversation_text = "\n".join(
        [
            f"{msg.type}: {msg.content}"
            for msg in messages
        ]
    )

    summary_prompt = f"""
    You are an AI memory compression assistant.

    Your job is to preserve IMPORTANT conversational memory.

    Extract and preserve:

    1. User personal details
       - name
       - email
       - phone
       - location
    2. Important identifiers
       - order IDs
       - ticket IDs
       - account IDs
    3. Important preferences
    4. Important decisions
    5. Ongoing unresolved issues
    DO NOT use headings
    - DO NOT use special characters like *, #, +
    
    DO NOT write a generic story summary.
    DO NOT omit identifiers or names.
    Return concise structured memory.
    Return plain compact text only
    Conversation:
    {conversation_text}
    """
    print("Invoke Local LLM for Summary generation ")
    summary_response = summary_llm.invoke(
        [
            SystemMessage(
                content="You are a conversation summarization assistant."
            ),
            HumanMessage(content=summary_prompt)
        ]
    )

    summary_text = summary_response.content

    print(f"DEBUG Summary Created:\n{summary_text}")

    return summary_text

''' API to manage message history for shortterm memory /session wise data'''
def get_optimised_message_history(state: ConversationState):
    print("get_optimised_message_history")
    messages = state["messages"]
    # ---------------------------------------------
    # SMALL CHAT
    # ---------------------------------------------
    if len(messages) <= 12:
        print("DEBUG Small conversation -> trim only")
        recent_messages = trim_conversation_history(state)
        print(f"DEBUG Recent messages: {len(recent_messages)}")
        return recent_messages

    # ---------------------------------------------
    # LARGE CHAT; getMessageSummary using llm
    # ---------------------------------------------
    print("DEBUG Large conversation -> summarization enabled")
    old_messages = messages[:-6]

    # Recent messages
    recent_messages = messages[-6:]

    # Create summary using LLM
    summary_text = getMessageSummary(
        {
            **state,   ###Python dictionary unpacking.
            "messages": old_messages
        }
    )
    # ---------------------------------------------
    # Build optimized context
    # ---------------------------------------------
    optimized_messages = [

        SystemMessage(
            content=f"""
    Conversation Summary:
    {summary_text}
    """
        )

    ]

    optimized_messages.extend(recent_messages)

    print(
        f"DEBUG Optimized Messages Count: {len(optimized_messages)}"
    )

    return optimized_messages

    return recent_messages

def chatwith_llm_agent_node(state: ConversationState):
    print("chatwith_llm_agent_node")
    optimised_messages = get_optimised_message_history(state);

    # 3. Add your System Message (Instruction)
    # We add this AFTER slicing so it's always at the top
    system_text = "You are a helpful AI assistant.Answer briefly in 3-4 lines."
    final_messages = [SystemMessage(content=system_text)] + optimised_messages
    # DEBUG TOKEN COUNT
    token_count = llm.get_num_tokens_from_messages(
        final_messages
    )
    print(f"DEBUG: Token Count = {token_count}")
    print(f"DEBUG: Strict Pruning, Sending- {len(final_messages)} messages to LLM.")

    response = llm.invoke(final_messages)

    return {
        "messages": [response],
        "response": response.content
    }

def build_conversation_stategraph():
    ## build graph
    print("Create StateGraph")
    workflow = StateGraph(ConversationState)

    workflow.add_node("chatwith_llm_agent_node", chatwith_llm_agent_node)
    ## Add Edges
    workflow.add_edge(START, "chatwith_llm_agent_node")
    workflow.add_edge("chatwith_llm_agent_node", END)

    graph = workflow.compile()
    return graph

##initilize graph (singleton instance , called only one when the module is loaded
conversation_graph = build_conversation_stategraph()

def save_graph(graph):
    graph_path = "conversation_graph_with.png"
    print(f"Save StateGraph:{graph_path}")
    graph.get_graph().draw_mermaid_png(output_file_path=graph_path)


save_graph(conversation_graph)

def chat_llm_with_stategraph(message: str,user_id, session_id):
    print("##chat_llm_with_stategraph...")
    # Unique conversation key
    ##thread_id = f"{user_id}_{session_id}"
    thread_id = user_id;
    print("##thread_id:", thread_id)
    # 1. Load previous history from Redis
    history = session_manager.load_session(
        thread_id
    )

    # -----------------------------------
    # 2. Refresh TTL on activity  for reddis
    # -----------------------------------
    session_manager.extend_session(
        thread_id
    )
    # 3. Append current user message
    updated_history = history + [
        HumanMessage(content=message)
    ]
    # 4. Invoke graph
    result = conversation_graph.invoke(
        {
            "messages": updated_history,
            "user_id": user_id,
            "session_id": session_id
        }
    )

    # 5. Append AI response
    updated_history.append(
        AIMessage(content=result["response"])
    )
    # 6. Save updated history
    session_manager.save_session(
        thread_id,
        updated_history
    )
    ##print(f"###Result: {result}")
    return result["response"]
