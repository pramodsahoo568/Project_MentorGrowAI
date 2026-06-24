'''
run the AWS Mock Test Agent REST api Server,
>go to project root folder
 >uvicorn server.app:app --reload --port 8000
'''

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.models.data_models import (QuestionRequest, QuestionResponse, ChatRequest,
                                       SubmitTestRequest,SubmitTestResponse,TestSummaryResponse,
                                       TestSummaryRequest,DocumentChatRequest,DocumentChatResponse,SourceDocument)
##from main_with_toolcalling import graph  # your compiled LangGraph
from langchain_core.messages import HumanMessage, AIMessage
import json

from server.llms.geminiapi import ask_gemini
from server.llms.askopenai import ask_openai
from server.agents.graph_builder import generate_questions, evaluate_performance
from server.agents.conversation_graph_builder_redis_memory import chat_llm_with_stategraph
##from server.agents.conversation_graph_builder_redis_memory import chat_with_llm_stream
from server.evaluate.evaluate_test_result import evaluate_result
from fastapi.responses import StreamingResponse

app = FastAPI(title="AWS Mock Test Agent Server")

'''
To deal with CORS error 
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:6001",
        "http://127.0.0.1:6001",
        "http://localhost:5001",
        "http://127.0.0.1:5001",

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_final_ai_message(state):
    """Extract final AI response from graph state"""
    from langchain_core.messages import AIMessage

    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage) and not message.tool_calls:
            return message.content
    return None


@app.post("/generate-questions", response_model=QuestionResponse)
async def generate_questions_endpoint(request: QuestionRequest):
    print("generate questions endpoint")
    print("message: ", request.message)
    print("user_id: ", request.userId)

    result = generate_questions(message=request.message,user_id=request.userId,sessionId=request.sessionId)
    print(f"response: {result}")

    #final_message='{"response":"This is response"}'
    return QuestionResponse(
        response=result  # JSON string from LLM
    )


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    print("chat endpoint")
    """The REST API endpoint your React frontend will call"""
    # Later, you will use request.userId and request.sessionId
    # to load chat history from your DB here.

    ##result = await ask_gemini(request.message) ## without state graph
    result= chat_llm_with_stategraph(request.message,request.userId,request.sessionId)
    print("response: ", result);

    # Return a structured JSON response
    return {
        "status": "success",
        "text": result,
        "sessionId": request.sessionId
    }
'''
@app.post("/api/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest
):

    async def generate():

        async for chunk in chat_with_llm_stream(
            request.message,
            request.userId,
            request.sessionId
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
'''

from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


'''
@app.post("/document-chat", response_model=DocumentChatResponse)
async def document_chat_endpoint(request: DocumentChatRequest):
    try:
        logger.info(
            "Document chat request received | userId=%s | sessionId=%s",
            request.userId,
            request.sessionId
        )

        result = await chat_with_document_kb(
            message=request.message,
            user_id=request.userId,
            session_id=request.sessionId
        )

        return DocumentChatResponse(
            status="success",
            text=result.get("answer", ""),
            sessionId=request.sessionId,
            sources=result.get("sources", [])
        )

    except Exception:
        logger.exception("Document chat failed")

        raise HTTPException(
            status_code=500,
            detail="Failed to process document chat request"
        )

'''

@app.post(
    "/submit-test",
    response_model=SubmitTestResponse
)
async def submit_test_endpoint(request: SubmitTestRequest):
    print("Submit Test Endpoint")
    result = evaluate_result(
        user_id=request.userId,
        session_id=request.sessionId,
        answers=request.answers
    )

    return SubmitTestResponse(
        status="success",
        totalQuestions=result["totalQuestions"],
        correctAnswers=result["correctAnswers"],
        wrongAnswers=result["wrongAnswers"],percentage=
        result["percentage"],results=result["results"]
    )




@app.post("/api/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest
):

    async def generate():

        graph_state = {
            "messages": [
                HumanMessage(
                    content=request.message
                )
            ],
            "user_id": request.userId,
            "session_id": request.sessionId
        }

        response_stream = chat_with_llm_stream(
            graph_state
        )

        async for chunk in response_stream:

            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )

@app.post(
    "/performance-summary",
    response_model=TestSummaryResponse
)
async def performance_summary_endpoint(
    request: TestSummaryRequest
):

    result = evaluate_performance(
        message="Evaluate Performance",
        user_id=request.userId
    )

    return TestSummaryResponse(
        status="success",
        testsTaken=result["testsTaken"],
        averageScore=result["averageScore"],
        bestScore=result["bestScore"],
        latestScore=result["latestScore"],
        weakAreas=result["weakAreas"],
        summary=result["summary"]
    )