import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pynamodb.exceptions import DoesNotExist, PynamoDBException
from fastapi import HTTPException
from openai import OpenAI
import os
import json

from app.models.question import QuestionModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse, StepExplanationResponse

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

    @staticmethod
    async def explain_solution_step(question_id: str, step_number: int) -> StepExplanationResponse:
        """Explain a specific step in the solution using GPT-4o-mini.
        
        Args:
            question_id: The question ID
            step_number: The step number to explain (1-indexed)
            
        Returns:
            StepExplanationResponse: Explanation of the step
            
        Raises:
            HTTPException: If question not found, step invalid, or LLM error
        """
        try:
            # Get the question
            question = QuestionModel.get(question_id)
            
            # Validate step number
            if step_number < 1 or step_number > len(question.solution_steps):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid step number. Question has {len(question.solution_steps)} steps."
                )
            
            # Get the specific step content (0-indexed)
            step_content = question.solution_steps[step_number - 1]
            
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
            client = OpenAI(api_key=api_key)
            
            # Create prompt for GPT-4o-mini
            system_prompt = """You are an expert educator who explains mathematical and logical solution steps.
            Given a specific step from a solution, provide clear and concise explanations.
            
            You must respond in valid JSON format with exactly these two keys:
            {
                "why_this_way": "explanation of why we need to solve it this way",
                "key_concepts": "explanation of the key concepts in this solution process"
            }
            
            Keep your explanations educational, clear, and focused on helping students understand the reasoning."""
            
            user_prompt = f"""Here is the context of the problem:
Question Understanding: {question.question_understanding}
Solving Strategy: {question.solving_strategy}

The specific step to explain is:
{step_content}

This is step {step_number} out of {len(question.solution_steps)} total steps.

Please provide a JSON response with:
1. "why_this_way": A clear explanation of WHY we need to solve it this way (focus on the reasoning and necessity)
2. "key_concepts": The KEY CONCEPTS involved in this step (mathematical principles, techniques, or important ideas)

Keep explanations concise but comprehensive."""
            
            # Call GPT-4o-mini
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            llm_response = response.choices[0].message.content
            
            try:
                # Parse JSON response
                parsed_response = json.loads(llm_response)
                why_this_way = parsed_response.get("why_this_way", "")
                key_concepts = parsed_response.get("key_concepts", "")
            except json.JSONDecodeError:
                # Fallback parsing if JSON fails
                lines = llm_response.strip().split('\n\n')
                why_this_way = lines[0] if len(lines) > 0 else "This approach is necessary for solving the problem systematically."
                key_concepts = lines[1] if len(lines) > 1 else "Key concepts include the mathematical and logical principles applied in this step."
            
            return StepExplanationResponse(
                step=step_number,
                step_content=step_content,
                why_this_way=why_this_way,
                key_concepts=key_concepts
            )
            
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
        except Exception as e:
            logger.error(f"Error explaining step: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error explaining step: {str(e)}")
