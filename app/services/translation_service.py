import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for handling translations between English and Thai using GPT-4o."""
    
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
            logger.info("OpenAI client initialized successfully for translation service")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing translation service: {str(e)}")
    
    async def translate_to_thai(self, english_json: Dict[str, Any]) -> Dict[str, Any]:
        """Translate all sections of the response from English to Thai using GPT-4o.
        
        Args:
            english_json: The English JSON response from LLM
            
        Returns:
            Dict[str, Any]: The translated JSON with Thai content
            
        Raises:
            HTTPException: If there's an error during translation
        """
        try:
            # Translate the entire response to Thai
            thai_result = await self._translate_full_response(english_json)
                
            return {
                "success": True,
                "message": "Translation completed successfully",
                "data": thai_result
            }
            
        except Exception as e:
            logger.error(f"Error translating content: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error translating content: {str(e)}")
    
    async def _translate_full_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate the complete response using OpenAI's GPT-4o model with chain-of-thought reasoning.
        
        Args:
            data: The complete English response
            
        Returns:
            Dict[str, Any]: The Thai translated response
        """
        try:
            # Convert the data to a JSON string
            json_str = json.dumps(data, ensure_ascii=False)
            
            # Create a system prompt with chain-of-thought instructions
            system_prompt = """
            You are a professional Thai translator specializing in educational content and technical explanations.
            Your task is to translate an English analysis into clear, natural Thai language.
            
            Follow these steps to produce high-quality Thai translations:
            
            1. Read and understand the complete English text in each section
            2. Think about how to express each concept naturally in Thai
            3. Consider Thai educational terminology and problem-solving vocabulary
            4. Translate step-by-step, maintaining the logical flow and clarity
            5. Ensure your Thai translations sound natural and are easy to understand
            6. Verify technical accuracy and educational value are preserved
            
            The input will have three important sections:
            1. "question_understanding" - Translate this comprehensively while maintaining all details
            2. "solving_strategy" - Translate the complete strategy and reasoning
            3. "solution_steps" - Translate each step precisely, maintaining the step-by-step format
            
            Your output must maintain the exact same JSON structure but with Thai content.
            """
            
            # Create a user prompt for the translation with chain-of-thought instructions
            user_prompt = f"""
            Translate this English analysis into clear, natural Thai language.
            
            Apply chain-of-thought reasoning to create high-quality Thai translations:
            1. First, understand the complete meaning of the English text
            2. Think about the most natural Thai expressions for each concept
            3. Ensure educational clarity and technical accuracy
            4. Preserve the step-by-step nature of explanations
            
            IMPORTANT RULES:
            - Translate all text to Thai language
            - Keep the exact same JSON structure and field names
            - For "solution_steps", maintain the array format with each step translated to Thai
            - Keep "Step 1:", "Step 2:", etc. at the beginning of each step
            - Make the Thai text clear, natural, and educational
            - Ensure the Thai explanation is complete and detailed
            
            JSON to translate:
            {json_str}
            
            Return ONLY valid JSON with Thai translations.
            """
            
            # Send the request to OpenAI using GPT-4o
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract and parse the response
            translated_json = json.loads(response.choices[0].message.content)
            return translated_json
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            # If translation fails, return the original data
            return data 