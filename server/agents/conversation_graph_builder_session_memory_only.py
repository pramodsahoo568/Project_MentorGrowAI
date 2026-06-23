
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, trim_messages
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, EmailStr
from typing import TypedDict, Literal, Annotated,Optional
from langchain_core.messages import BaseMessage, HumanMessage
import operator
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage
import json
from server.memory.redis_session_manager import RedisSessionManager


class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    user_id: str
    session_id: str
    summary: Optional[str]
    retrieved_memories: Optional[list]
    response: str


## max_tokens restrict the llm response length, llm output
llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.7,top_p=0.9, max_tokens=120)

'''
Sliding window with n recent messages
'''
def sliding_window_with_recent_messages(state: ConversationState):
    window_size = 6
    messages = state["messages"]

    print("Message Length: ", len(messages));
    # If history is too long, prune it before the chat node sees it
    if len(messages) > window_size:
        number_to_delete = len(messages) - window_size

        # Identify the oldest messages to drop
        delete_instructions = [
            RemoveMessage(id=m.id) for m in messages[:number_to_delete]
        ]

        print(f"--- PRE-CHAT PRUNING: Removing {number_to_delete} messages to save tokens ---")
        return {"messages": delete_instructions}

    print("do not perform PRUNING on recent messages")
    return {"messages": []}


def sliding_window_with_message_count(state: ConversationState):
    print("sliding_window_with_message_count")
    all_messages = state["messages"];
    # 2. STRICT ENFORCEMENT: Take only the last 6 messages
    window_size = 6
    # Keep only recent messages for LLM context
    recent_messages = all_messages[-window_size:]
    return recent_messages

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
    # recent_messages = sliding_window_with_message_count(state);
    recent_messages = trim_conversation_history(state);
    print(f"DEBUG Recent messages: {len(recent_messages)}")

    ## todo getMessageSummary using llm

    return recent_messages


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

    ## Add Nodes
    ##workflow.add_node("manage_memory_node", manage_memory_node)
    workflow.add_node("chatwith_llm_agent_node", chatwith_llm_agent_node)
    ## Add Edges
    ##workflow.add_edge(START, "manage_memory_node")
    workflow.add_edge(START, "chatwith_llm_agent_node")
    workflow.add_edge("chatwith_llm_agent_node", END)

    ## initialize memory   , Buffer memory implementation
    memory = InMemorySaver()
    graph = workflow.compile(checkpointer=memory)
    return graph

##initilize graph (singleton instance , called only one when the module is loaded
conversation_graph = build_conversation_stategraph()

def save_graph(graph):
    graph_path = "conversation_graph_with.png"
    print(f"Save StateGraph:{graph_path}")
    graph.get_graph().draw_mermaid_png(output_file_path=graph_path)


save_graph(conversation_graph)

def chat_llm_with_stategraph(message: str, user_id, session_id):
    print("##chat_llm_with_stategraph")
    print("##user: ", user_id)
    config: RunnableConfig = {"configurable": {"thread_id": session_id}}

    print("Invoke StateGraph")
    result = conversation_graph.invoke(
        {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,  # Pass these so they exist in the state
            "session_id": session_id
        },
        config=config
    )

    print(f"###Result: {result}")
    #print(f"response: {result['response'].content}")
    return result['response']

