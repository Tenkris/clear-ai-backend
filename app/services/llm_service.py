import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class LLMService:
    """Service for handling LLM processing."""
    
    def __init__(self):
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Check if API key is available
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
            )
        
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing LLM service: {str(e)}")
    
    async def process_thai_image(self, image_base64: str) -> Dict[str, Any]:
        """Process Thai image directly using LLM with chain-of-thought reasoning.
        
        Args:
            image_base64: The base64 encoded image
            
        Returns:
            Dict[str, Any]: The processed response with reasoning and structured data
            
        Raises:
            HTTPException: If there's an error processing the image
        """
        try:
            # Create a system message that instructs the model to use chain-of-thought reasoning
            system_message = """
            You are an expert assistant that analyzes Thai text in images and provides detailed, structured answers in English.
            
            When analyzing the image, you must carefully read and understand ALL Thai text visible in the image.
            Think step-by-step about the content, context, and meaning of the text.
            
            Your analysis must follow this structured chain-of-thought reasoning process:
            
            1. First identify and read ALL Thai text in the image thoroughly
            2. Think about each piece of information and how they relate to each other
            3. Consider any implicit information or context that might be important
            4. Formulate a comprehensive understanding of the text's meaning and purpose
            5. Develop a logical strategy to address what the text is asking or presenting
            6. Break down the solution into clear, sequential steps
            
            Your response MUST be in this exact JSON format:
            {
                "question_understanding": {
                    "identified_text": "The Thai text you identified in the image",
                    "context": "The broader context or situation of the text",
                    "key_elements": "Important elements or components identified",
                    "main_question": "What the text is asking or what problem needs to be solved"
                },
                "solving_strategy": {
                    "approach": "Your overall approach to solving this problem",
                    "reasoning": "Why you chose this approach",
                    "considerations": "Important factors to consider in your solution"
                },
                "solution": {
                    "step1": "First step in your solution process",
                    "step2": "Second step in your solution process",
                    "step3": "Third step in your solution process",
                    // Continue with as many steps as needed
                    "conclusion": "Final answer or conclusion"
                }
            }
            
            For each section, think carefully before responding. Your chain-of-thought reasoning should be evident in how you break down the problem and explain your solution process.
            """
            
            # Send the request to the LLM with the image
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o which has vision capabilities
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Analyze this Thai text image. Apply chain-of-thought reasoning and respond with the structured format."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract the response content
            response_content = response.choices[0].message.content
            
            # Parse the JSON response
            parsed_response = json.loads(response_content)
            
            # Restructure for backward compatibility
            restructured_response = {
                "reasoning": json.dumps({
                    "question_understanding": parsed_response.get("question_understanding", {}),
                    "solving_strategy": parsed_response.get("solving_strategy", {})
                }, ensure_ascii=False),
                "structured_answer": {
                    "solution": parsed_response.get("solution", {})
                }
            }
            
            return restructured_response
            
        except Exception as e:
            logger.error(f"Error processing image with LLM: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing image with LLM: {str(e)}") 