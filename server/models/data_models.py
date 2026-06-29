from pydantic import BaseModel, EmailStr

class RegisterUserRequest(BaseModel):
    clerkUserId: str
    email: EmailStr
    name: str | None = None


class RegisterUserResponse(BaseModel):
    status: str
    userId: str
    clerkUserId: str
    email: EmailStr
    name: str | None = None


class ChatRequest(BaseModel):
    message: str
    userId: str | None = "guest"
    sessionId: str | None = None

class ChatResponse(BaseModel):
    response: str

from pydantic import BaseModel
from typing import List, Optional

from pydantic import BaseModel
from typing import List, Optional

class QuestionRequest(BaseModel):
    message: str
    userId: str | None = "guest"
    sessionId: str | None = None

class QuestionResponse(BaseModel):
    response: str


class AnswerItem(BaseModel):
    questionId: int
    selectedAnswers: List[str]


class SubmitTestRequest(BaseModel):
    userId: str
    sessionId: str
    answers: List[AnswerItem]


class QuestionResult(BaseModel):
        questionId: int
        isCorrect: bool
        selectedAnswers: List[str]
        correctAnswers: List[str]

class SubmitTestResponse(BaseModel):
        status: str
        totalQuestions: int
        correctAnswers: int
        wrongAnswers: int
        percentage: float
        results: List[QuestionResult]


class TestSummaryRequest(BaseModel):
    userId: str

from typing import List

class WeakArea(BaseModel):
    domain: str
    failures: int


class TestSummaryResponse(BaseModel):

    status: str
    testsTaken: int
    averageScore: float
    bestScore: float
    latestScore: float
    weakAreas: List[WeakArea]
    summary: str

from pydantic import BaseModel, Field
from typing import Optional, List

class DocumentChatRequest(BaseModel):
    message: str
    userId: str
    sessionId: str


class SourceDocument(BaseModel):
    fileName: Optional[str] = None
    page: Optional[int] = None
    content: Optional[str] = None
    score: Optional[float] = None


class DocumentChatResponse(BaseModel):
    status: str
    text: str
    sessionId: str
    sources: List[SourceDocument] = Field(default_factory=list)
