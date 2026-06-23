
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
llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.7,top_p=0.9, max_tokens=200)

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
    ## TODO to implement the summarised message history using a Local LLM

''' API to manage message history for shortterm memory /session wise data'''
def get_optimised_message_history(state: ConversationState):
    print("get_optimised_message_history")
    recent_messages = trim_conversation_history(state);
    print(f"DEBUG Recent messages: {len(recent_messages)}")

    ## todo getMessageSummary using llm

    return recent_messages
'''
def chatwith_llm_agent_node(state: ConversationState):
    print("chatwith_llm_agent_node")
    optimised_messages = get_optimised_message_history(state);

    # 3. Add your System Message (Instruction)
    # We add this AFTER slicing so it's always at the top
    system_text = "Answer briefly in 3-4 lines."
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
'''
''' This is stream version '''
def chatwith_llm_agent_node(state: ConversationState):
    print("chatwith_llm_agent_node")
    optimised_messages = get_optimised_message_history(state);

    # 3. Add your System Message (Instruction)
    # We add this AFTER slicing so it's always at the top
    system_text = "Answer briefly in 3-4 lines."
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


from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

async def chat_with_llm_stream(
    message: str,
    user_id: str,
    session_id: str
):

    print("Streaming Chat")

    thread_id = user_id

    # Load Redis history

    history = session_manager.load_session(
        thread_id
    )

    session_manager.extend_session(
        thread_id
    )

    updated_history = history + [
        HumanMessage(
            content=message
        )
    ]

    full_response = ""

    # Build prompt exactly same way

    optimised_messages = (
        get_optimised_message_history(
            {
                "messages":
                    updated_history
            }
        )
    )

    final_messages = [

        SystemMessage(
            content=
            "Answer briefly in 3-4 lines."
        )

    ] + optimised_messages

    # Stream from OpenAI

    for chunk in llm.stream(
        final_messages
    ):

        if chunk.content:

            full_response += (
                chunk.content
            )

            yield chunk.content

    # Save final response

    updated_history.append(

        AIMessage(
            content=full_response
        )

    )

    session_manager.save_session(
        thread_id,
        updated_history
    )