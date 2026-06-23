from pydantic import BaseModel
from typing import Optional


class IntentOutputSchema(BaseModel):
    intent: str
    exam_name: Optional[str] = None
    domain: Optional[str] = None
    count: Optional[int] = None