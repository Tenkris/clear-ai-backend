import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pynamodb.exceptions import DoesNotExist, PynamoDBException
from fastapi import HTTPException
from openai import OpenAI
import os
import json

from app.models.question import QuestionModel
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse, StepExplanationResponse, AskQuestionResponse

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
            
            # Create prompt for GPT-4o-mini with LaTeX formatting
            system_prompt = """You are an expert educator who explains mathematical and logical solution steps.
            Given a specific step from a solution, provide clear and concise explanations.
            
            You must respond in valid JSON format with exactly these two keys:
            {
                "why_this_way": "explanation of why we need to solve it this way",
                "key_concepts": "explanation of the key concepts in this solution process"
            }
            
            MATHEMATICAL EXPRESSION FORMATTING:
            - For ALL mathematical expressions, equations, formulas, and symbols, use LaTeX syntax enclosed in dollar signs
            - Examples:
              * For inline expressions: $x^2 + 3x - 2 = 0$
              * For fractions: $\\frac{a}{b}$
              * For integrals: $\\int_{a}^{b} f(x) dx$
              * For square roots: $\\sqrt{x}$
              * For subscripts: $a_1, a_2, a_3$
              * For superscripts: $x^n$
            - Always use proper LaTeX syntax for mathematical symbols: $\\pi$, $\\theta$, $\\sum$, $\\prod$, etc.
            - For systems of equations or multi-line expressions, use proper LaTeX line breaks
            - Always include LaTeX formatting even for simple expressions like $5 + 3 = 8$ or $x = 2$
            
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

IMPORTANT: Use LaTeX formatting for ALL mathematical expressions, formulas, and symbols.
Keep explanations concise but comprehensive."""
            
            # Call GPT-4o-mini
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.1,
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

    @staticmethod
    async def ask_about_question(question_id: str, user_question: str) -> AskQuestionResponse:
        """Handle user questions about the solution and get AI responses.
        
        Args:
            question_id: The question ID
            user_question: The user's question about the solution
            
        Returns:
            AskQuestionResponse: Contains the user message and AI response
            
        Raises:
            HTTPException: If question not found or AI service fails
        """
        try:
            # Get the question
            question = QuestionModel.get(question_id)
            
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
            client = OpenAI(api_key=api_key)
            
            # Build context from existing conversation
            conversation_context = ""
            if question.conversations:
                conversation_context = "\n".join(question.conversations[-10:])  # Last 10 messages for context
            
            # Create prompt for GPT-4o-mini with LaTeX formatting
            system_prompt = """You are a concise educational assistant that answers questions about mathematical problem solutions.
            
            IMPORTANT RULES:
            - Be EXTREMELY CONCISE and STRAIGHT TO THE POINT
            - Answer in 1-3 sentences maximum unless complexity requires more
            - NO unnecessary elaboration or filler content
            - Focus only on what directly answers the user's question
            - Use simple, clear language
            - Get to the point immediately
            
            MATHEMATICAL EXPRESSION FORMATTING:
            - For ALL mathematical expressions, equations, formulas, and symbols, use LaTeX syntax enclosed in dollar signs
            - Examples:
              * For inline expressions: $x^2 + 3x - 2 = 0$
              * For fractions: $\\frac{a}{b}$
              * For integrals: $\\int_{a}^{b} f(x) dx$
              * For square roots: $\\sqrt{x}$
              * For subscripts: $a_1, a_2, a_3$
              * For superscripts: $x^n$
            - Always use proper LaTeX syntax for mathematical symbols: $\\pi$, $\\theta$, $\\sum$, $\\prod$, etc.
            - For systems of equations or multi-line expressions, use proper LaTeX line breaks
            - Always include LaTeX formatting even for simple expressions like $5 + 3 = 8$ or $x = 2$"""
            
            user_prompt = f"""Here is the problem context:

Question Understanding: {question.question_understanding}

Solving Strategy: {question.solving_strategy}

Solution Steps:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(question.solution_steps)])}

Recent Conversation History:
{conversation_context if conversation_context else "No previous conversation"}

User's Question: {user_question}

IMPORTANT: 
- Provide a BRIEF, DIRECT answer. Maximum 1-3 sentences. No introduction, no conclusion, just the answer.
- Use LaTeX formatting for ALL mathematical expressions, formulas, and symbols."""
            
            # Call GPT-4o-mini
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150
            )
            
            # Get AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Format messages with proper tags
            user_message_tagged = f"User: {user_question}"
            ai_message_tagged = f"Assistant: {ai_response}"
            
            # Append both messages to conversation history
            if not question.conversations:
                question.conversations = []
            
            question.conversations.append(user_message_tagged)
            question.conversations.append(ai_message_tagged)
            
            # Update timestamp and save
            question.updated_at = datetime.now(timezone.utc)
            question.save()
            
            logger.info(f"Added Q&A to conversation for question: {question_id}")
            
            return AskQuestionResponse(
                user_message=user_question,
                ai_response=ai_response
            )
            
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
