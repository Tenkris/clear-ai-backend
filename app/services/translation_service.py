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
        """Translate structured answer from English to Thai using GPT-4o.
        
        Args:
            english_json: The English JSON response from LLM
            
        Returns:
            Dict[str, Any]: The translated JSON with Thai content
            
        Raises:
            HTTPException: If there's an error during translation
        """
        try:
            # Keep the original reasoning in English
            result = {
                "reasoning": english_json.get("reasoning", ""),
                "structured_answer": {}
            }
            
            # Extract the structured answer for translation
            structured_answer = english_json.get("structured_answer", {})
            
            # Translate using GPT-4o with chain-of-thought
            result["structured_answer"] = await self._translate_with_gpt4o(structured_answer)
                
            return result
            
        except Exception as e:
            logger.error(f"Error translating content: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error translating content: {str(e)}")
    
    async def _translate_with_gpt4o(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate using OpenAI's GPT-4o model with chain-of-thought reasoning.
        
        Args:
            data: The dictionary with English values
            
        Returns:
            Dict[str, Any]: The dictionary with Thai values
        """
        try:
            # Convert the data to a JSON string
            json_str = json.dumps(data)
            
            # Create a system prompt with chain-of-thought instructions
            system_prompt = """
            You are a professional translator specializing in English to Thai translation.
            You excel at preserving meaning, cultural nuances, and contextual accuracy.
            When translating, follow these steps:
            
            1. First understand the complete meaning of each English text
            2. Consider cultural context and nuances specific to Thai language
            3. Think about natural-sounding Thai alternatives for English phrases
            4. Select the most accurate and contextually appropriate Thai translation
            5. Ensure the translation follows Thai grammar rules and conventions
            6. Verify that technical terms are translated correctly
            
            Your primary goal is producing high-quality, accurate Thai translations 
            while maintaining the original meaning and tone.
            """
            
            # Create a user prompt for the translation with chain-of-thought instructions
            user_prompt = f"""
            Translate the following JSON from English to Thai using chain-of-thought reasoning.
            
            For each value that needs translation:
            1. Understand the meaning and context
            2. Consider various ways to express it in Thai
            3. Choose the most natural and accurate Thai translation
            
            IMPORTANT:
            - Translate ONLY the string values, keep the keys and structure exactly the same
            - Maintain the same JSON format
            - Preserve numbers, dates, and any special formatting
            - Ensure technical terms are translated correctly
            
            JSON to translate:
            {json_str}
            
            Return ONLY the valid JSON with Thai translations.
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