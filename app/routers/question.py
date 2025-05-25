from fastapi import APIRouter, Depends, Query, status
from typing import List, Dict, Any
import logging

from app.services.question import QuestionService
from app.schemas.question import (
    QuestionCreate, 
    QuestionUpdate, 
    QuestionResponse,
    ConversationAppend,
    StepExplanationRequest,
    StepExplanationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate
) -> QuestionResponse:
    return await QuestionService.create_question(question_data)

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str
) -> QuestionResponse:
    """Get a question by ID.
    
    Args:
        question_id: The question ID
        
    Returns:
        QuestionResponse: The question
    """
    return await QuestionService.get_question(question_id)

@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    update_data: QuestionUpdate
) -> QuestionResponse:
    """Update a question.
    
    Args:
        question_id: The question ID
        update_data: The data to update
        
    Returns:
        QuestionResponse: The updated question
    """
    return await QuestionService.update_question(question_id, update_data)

@router.delete("/{question_id}")
async def delete_question(
    question_id: str
) -> Dict[str, str]:
    """Delete a question.
    
    Args:
        question_id: The question ID
        
    Returns:
        Dict: Success message
    """
    return await QuestionService.delete_question(question_id)

@router.get("/", response_model=List[QuestionResponse])
async def list_questions(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of questions to return")
) -> List[QuestionResponse]:
    """List all questions with optional limit.
    
    Args:
        limit: Maximum number of questions to return (1-100)
        
    Returns:
        List[QuestionResponse]: List of questions
    """
    return await QuestionService.list_questions(limit)

@router.post("/{question_id}/conversation", response_model=QuestionResponse)
async def append_conversation(
    question_id: str,
    conversation: ConversationAppend
) -> QuestionResponse:
    """Append a message to the question's conversation history.
    
    Args:
        question_id: The question ID
        conversation: The message to append
        
    Returns:
        QuestionResponse: The updated question with new conversation
    """
    return await QuestionService.append_conversation(question_id, conversation.message)

@router.post("/{question_id}/explain-step", response_model=StepExplanationResponse)
async def explain_solution_step(
    question_id: str,
    request: StepExplanationRequest
) -> StepExplanationResponse:
    """Explain a specific step in the solution.
    
    This endpoint provides two key explanations for a solution step:
    1. Why we need to solve it this way
    2. What are the key concepts in the solution process
    
    Args:
        question_id: The question ID
        request: Contains the step number to explain (1-indexed)
        
    Returns:
        StepExplanationResponse: Detailed explanation of the step
        
    Raises:
        HTTPException: If question not found or step number is invalid
    """
    return await QuestionService.explain_solution_step(question_id, request.step)
