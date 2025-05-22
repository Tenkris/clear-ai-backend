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
            You are an expert assistant that analyzes Thai text in images and provides detailed, structured answers in clear, concise English.
            
            When analyzing the image, you must carefully read and understand ALL Thai text visible in the image.
            Apply systematic chain-of-thought reasoning to thoroughly analyze the content and context.
            
            Your analysis must follow this structured reasoning process:
            
            1. First identify and read ALL Thai text in the image thoroughly
            2. Think about each piece of information and how they relate to each other
            3. Consider any implicit information or context that might be important
            4. Formulate a comprehensive understanding of the text's meaning and purpose
            5. Develop a logical strategy to address what the text is asking or presenting
            6. Break down the solution into clear, sequential steps
            
            Your response MUST be in this EXACT JSON format:
            {
                "question_understanding": "Provide a concise yet comprehensive understanding of what the text is asking or presenting. Include key context and the main question/problem.",
                
                "solving_strategy": "Explain your approach to solving this problem in clear, logical steps, including your reasoning and key considerations.",
                
                "solution_steps": [
                    "Step 1: First step in your solution process with clear reasoning",
                    "Step 2: Second step explained clearly and directly",
                    "Step 3: Third step with continued work",
                    // Continue with as many steps as needed
                    "Conclusion: Final answer or conclusion stated clearly"
                ]
            }
            
            IMPORTANT GUIDELINES:
            - The solution_steps MUST be an array of strings, with each step clearly numbered
            - Write in clear, direct English using simple language where possible
            - Keep explanations concise while maintaining completeness
            - For math problems, show calculations explicitly and verify your answers
            - For text analysis, provide logical reasoning for your interpretations
            - If the problem has multiple valid approaches, choose the most straightforward one
            
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
            
            Your response should be structured for clarity and ease of understanding, with careful attention to accuracy.
            """
            
            # Send the request to the LLM with the image
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o which has vision capabilities
                temperature=0.2,  # Lower temperature for more deterministic/accurate responses
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Analyze this Thai text image. Apply thorough reasoning and respond with the structured format in clear English. Use LaTeX for all mathematical expressions."},
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
            
            # Validate the response format
            self._validate_response_structure(parsed_response)
            
            # Return the parsed response directly
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error processing image with LLM: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing image with LLM: {str(e)}")
    
    def _validate_response_structure(self, response: Dict[str, Any]) -> None:
        """Validate that the response has the required structure.
        
        Args:
            response: The parsed LLM response
            
        Raises:
            ValueError: If the response doesn't have the required structure
        """
        required_keys = ["question_understanding", "solving_strategy", "solution_steps"]
        
        for key in required_keys:
            if key not in response:
                raise ValueError(f"LLM response is missing required field: {key}")
        
        # Ensure solution_steps is a list
        if not isinstance(response["solution_steps"], list) or len(response["solution_steps"]) == 0:
            raise ValueError("solution_steps must be a non-empty list") 