from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class QuestionCreate(BaseModel):
    question_understanding: str
    solving_strategy: str
    solution_steps: List[str]
    conversations: Optional[List[str]] = []
    image_s3: str

    class Config:
        json_schema_extra = {
            "example": {
                "question_understanding": "Understanding of the mathematical problem",
                "solving_strategy": "Strategy to solve the problem",
                "solution_steps": [
                    "Step 1: Initial step",
                    "Step 2: Next step",
                    "Step 3: Final calculation"
                ],
                "conversations": [],
                "image_s3": "s3://bucket/path/to/image.jpg"
            }
        }

class QuestionResponse(BaseModel):
    question_id: str
    question_understanding: str
    solving_strategy: str
    solution_steps: List[str]
    conversations: List[str]
    image_s3: str
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "question_id": "q_12345678_1234567890",
                "question_understanding": "Understanding of the mathematical problem",
                "solving_strategy": "Strategy to solve the problem",
                "solution_steps": [
                    "Step 1: Initial step",
                    "Step 2: Next step",
                    "Step 3: Final calculation"
                ],
                "conversations": ["User: Can you explain step 2?", "Assistant: Sure, in step 2..."],
                "image_s3": "s3://bucket/path/to/image.jpg",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

class QuestionUpdate(BaseModel):
    question_understanding: Optional[str] = None
    solving_strategy: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    conversations: Optional[List[str]] = None
    image_s3: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "question_understanding": "Updated understanding",
                "solution_steps": ["Updated step 1", "Updated step 2"],
                "conversations": ["User: Can you explain step 2?", "Assistant: Sure, in step 2..."]
            }
        }

class ConversationAppend(BaseModel):
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "User: Can you explain this step in more detail?"
            }
        }

class StepExplanationRequest(BaseModel):
    step: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": 1
            }
        }

class StepExplanationResponse(BaseModel):
    step: int
    step_content: str
    why_this_way: str
    key_concepts: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "step_content": "Step 1: Identify the given values and what we need to find",
                "why_this_way": "We need to solve it this way because identifying given information is crucial for understanding the problem structure and determining which mathematical principles to apply.",
                "key_concepts": "The key concepts in this step include: problem decomposition, variable identification, and establishing relationships between known and unknown values."
            }
        }
