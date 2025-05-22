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
            You are an assistant that analyzes Thai text in images and provides detailed answers in English.
            Follow these steps:
            1. First, identify and read all Thai text in the image.
            2. Understand the Thai text thoroughly.
            3. Think step by step about what the text is asking or stating.
            4. Provide your reasoning in English, explaining your thought process.
            5. Finally, provide a structured JSON answer that includes key information.
            
            Your response must be in this format:
            {
                "reasoning": "Your step-by-step reasoning in English",
                "structured_answer": {
                    // JSON-formatted answer with the key information from the text
                }
            }
            """
            
            # Send the request to the LLM with the image
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o which has vision capabilities
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Analyze this Thai text image and respond according to the format instructions."},
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
            
            # Ensure the response has the required fields
            if "reasoning" not in parsed_response or "structured_answer" not in parsed_response:
                raise ValueError("LLM response does not have the required fields")
                
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error processing image with LLM: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing image with LLM: {str(e)}") 