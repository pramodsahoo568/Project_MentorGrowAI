'''
run the AWS Mock Test Agent REST api Server,
>go to project root folder
 >uvicorn server.app:app --reload --port 8000
'''
APP_VERSION = "1.0.4"

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from server.models.data_models import (RegisterUserRequest, RegisterUserResponse,
                                       QuestionRequest, QuestionResponse, ChatRequest,
                                       SubmitTestRequest,SubmitTestResponse,TestSummaryResponse,
                                       TestSummaryRequest)


from server.llms.geminiapi import ask_gemini
from server.llms.askopenai import ask_openai
from server.agents.graph_builder import generate_questions, evaluate_performance
from server.agents.conversation_graph_builder_redis_memory import chat_llm_with_stategraph
##from server.agents.conversation_graph_builder_redis_memory import chat_with_llm_stream
from server.evaluate.evaluate_test_result import evaluate_result
from fastapi.responses import StreamingResponse
from server.memory.postgre_longterm_memory import PostgresChatStore

logger = logging.getLogger(__name__)

app = FastAPI(title="AWS Mock Test Agent Server")

'''
To deal with CORS error 
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Cloudflare Pages
        "https://mentorgrowai-ui.pages.dev",

        # Production Domain
        "https://mentorgrowai.com",
        "https://www.mentorgrowai.com",

        # Local Development
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "http://localhost:6001",
        "http://127.0.0.1:6001",
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

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": APP_VERSION
    }


@app.post(
    "/api/register_user",
    response_model=RegisterUserResponse
)
async def register_user_endpoint(request: RegisterUserRequest):
    print("register user endpoint")
    print("clerk_user_id: ", request.clerkUserId)
    print("email: ", request.email)

    chat_store = None

    try:
        chat_store = PostgresChatStore()
        user = chat_store.get_or_create_user(
            external_user_id=request.clerkUserId,
            email=str(request.email),
            display_name=request.name
        )
    except Exception as e:
        logger.exception("Failed to register user")
        raise HTTPException(
            status_code=500,
            detail="Failed to register user"
        ) from e
    finally:
        if chat_store:
            chat_store.close()

    return RegisterUserResponse(
        status="success",
        userId=str(user["user_id"]),
        clerkUserId=user["clerk_user_id"],
        email=user["email"],
        name=user["name"]
    )

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

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


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



'''
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
'''
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
