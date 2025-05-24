import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pynamodb.exceptions import DoesNotExist, PynamoDBException
from fastapi import HTTPException

from app.models.question import QuestionModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse

logger = logging.getLogger(__name__)

class QuestionService:
    """Service for handling question-related operations."""
    
    @staticmethod
    async def create_question(question_data: QuestionCreate) -> QuestionResponse:
        """Create a new question.
        
        Args:
            question_data: The question data to create
            
        Returns:
            QuestionResponse: The created question
            
        Raises:
            HTTPException: If there's an error creating the question
        """
        try:
            # Generate unique question ID
            question_id = QuestionModel.generate_id()
            
            # Create question in DynamoDB
            question = QuestionModel(
                question_id=question_id,
                question_understanding=question_data.question_understanding,
                solving_strategy=question_data.solving_strategy,
                solution_steps=question_data.solution_steps,
                conversations=question_data.conversations,
                image_s3=question_data.image_s3
            )
            question.save()
            
            logger.info(f"Created question with ID: {question_id}")
            return QuestionResponse(**question.to_dict())
            
        except PynamoDBException as e:
            logger.error(f"Error creating question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating question: {str(e)}")
    
    @staticmethod
    async def get_question(question_id: str) -> QuestionResponse:
        """Get a question by ID.
        
        Args:
            question_id: The question ID
            
        Returns:
            QuestionResponse: The question
            
        Raises:
            HTTPException: If question not found or other error
        """
        try:
            question = QuestionModel.get(question_id)
            return QuestionResponse(**question.to_dict())
            
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
        except PynamoDBException as e:
            logger.error(f"Error fetching question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching question: {str(e)}")
    
    @staticmethod
    async def update_question(question_id: str, update_data: QuestionUpdate) -> QuestionResponse:
        """Update a question.
        
        Args:
            question_id: The question ID
            update_data: The data to update
            
        Returns:
            QuestionResponse: The updated question
            
        Raises:
            HTTPException: If question not found or other error
        """
        try:
            question = QuestionModel.get(question_id)
            
            # Update fields if provided
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if value is not None:
                    setattr(question, field, value)
            
            # Update timestamp
            question.updated_at = datetime.now(timezone.utc)
            question.save()
            
            logger.info(f"Updated question: {question_id}")
            return QuestionResponse(**question.to_dict())
            
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
        except PynamoDBException as e:
            logger.error(f"Error updating question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error updating question: {str(e)}")
    
    @staticmethod
    async def delete_question(question_id: str) -> Dict[str, str]:
        """Delete a question.
        
        Args:
            question_id: The question ID
            
        Returns:
            Dict: Success message
            
        Raises:
            HTTPException: If question not found or other error
        """
        try:
            question = QuestionModel.get(question_id)
            question.delete()
            
            logger.info(f"Deleted question: {question_id}")
            return {"message": f"Question {question_id} deleted successfully"}
            
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
        except PynamoDBException as e:
            logger.error(f"Error deleting question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error deleting question: {str(e)}")
    
    @staticmethod
    async def list_questions(limit: int = 20) -> List[QuestionResponse]:
        """List all questions with optional limit.
        
        Args:
            limit: Maximum number of questions to return
            
        Returns:
            List[QuestionResponse]: List of questions
            
        Raises:
            HTTPException: If there's an error listing questions
        """
        try:
            questions = []
            for question in QuestionModel.scan(limit=limit):
                questions.append(QuestionResponse(**question.to_dict()))
            
            logger.info(f"Listed {len(questions)} questions")
            return questions
            
        except PynamoDBException as e:
            logger.error(f"Error listing questions: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error listing questions: {str(e)}")
    
    @staticmethod
    async def append_conversation(question_id: str, message: str) -> QuestionResponse:
        """Append a message to the question's conversation history.
        
        Args:
            question_id: The question ID
            message: The message to append
            
        Returns:
            QuestionResponse: The updated question
            
        Raises:
            HTTPException: If question not found or other error
        """
        try:
            question = QuestionModel.get(question_id)
            
            # Append message to conversations
            if not question.conversations:
                question.conversations = []
            question.conversations.append(message)
            
            # Update timestamp
            question.updated_at = datetime.now(timezone.utc)
            question.save()
            
            logger.info(f"Appended conversation to question: {question_id}")
            return QuestionResponse(**question.to_dict())
            
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
        except PynamoDBException as e:
            logger.error(f"Error appending conversation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error appending conversation: {str(e)}")
