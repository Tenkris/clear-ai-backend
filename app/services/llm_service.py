import os
import json
import logging
from typing import Dict, Any
from fastapi import HTTPException
from google import genai
from google.genai import types
import re

logger = logging.getLogger(__name__)

class LLMService:
    """Service for handling LLM processing."""
    
    def __init__(self):
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Check if API key is available
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            raise HTTPException(
                status_code=500,
                detail="Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
            )
        
        try:
            self.client = genai.Client(api_key=api_key)
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing LLM service: {str(e)}")
    
    async def process_thai_image(self, image_base64: str, language: str) -> Dict[str, Any]:
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
            system_message = (
                f"You are an expert assistant that analyzes Thai text in images and provides detailed, structured answers in clear, concise {language}.\n"
                "\n"
                "When analyzing the image, you must carefully read and understand ALL Thai text visible in the image.\n"
                "Apply systematic chain-of-thought reasoning to thoroughly analyze the content and context.\n"
                "\n"
                "Your analysis must follow this structured reasoning process:\n"
                "1. First identify and read ALL Thai text in the image thoroughly\n"
                "2. Think about each piece of information and how they relate to each other\n"
                "3. Consider any implicit information or context that might be important\n"
                "4. Formulate a comprehensive understanding of the text's meaning and purpose\n"
                "5. Develop a logical strategy to address what the text is asking or presenting\n"
                "6. Break down the solution into clear, sequential steps\n"
                "\n"
                "Your response MUST be in this EXACT JSON format:\n"
                "{\n"
                '    "question_understanding": "Provide a concise yet comprehensive understanding of what the text is asking or presenting. Include key context and the main question/problem.",\n'
                '    "solving_strategy": "Explain your approach to solving this problem in clear, logical steps, including your reasoning and key considerations.",\n'
                '    "solution_steps": [\n'
                '        "Step 1: First step in your solution process with clear reasoning",\n'
                '        "Step 2: Second step explained clearly and directly",\n'
                '        "Step 3: Third step with continued work",\n'
                '        // Continue with as many steps as needed\n'
                '        "Conclusion: Final answer or conclusion stated clearly"\n'
                "    ]\n"
                "}\n"
                "\n"
                f"IMPORTANT GUIDELINES:\n"
                "- The solution_steps MUST be an array of strings, with each step clearly numbered\n"
                f"- Write in clear, direct {language} using simple language where possible\n"
                "- Keep explanations concise while maintaining completeness\n"
                "- For math problems, show calculations explicitly and verify your answers\n"
                "- For text analysis, provide logical reasoning for your interpretations\n"
                "- If the problem has multiple valid approaches, choose the most straightforward one\n"
                "\n"
                r"MATHEMATICAL EXPRESSION FORMATTING:\n"
                r"- For ALL mathematical expressions, equations, formulas, and symbols, use LaTeX syntax enclosed in dollar signs\n"
                r"- Examples:\n"
                r"  * For inline expressions: $x^2 + 3x - 2 = 0$\n"
                r"  * For fractions: $\frac{a}{b}$\n"
                r"  * For integrals: $\int_{a}^{b} f(x) dx$\n"
                r"  * For square roots: $\sqrt{x}$\n"
                r"  * For subscripts: $a_1, a_2, a_3$\n"
                r"  * For superscripts: $x^n$\n"
                r"- Always use proper LaTeX syntax for mathematical symbols: $\pi$, $\theta$, $\sum$, $\prod$, etc.\n"
                r"- For systems of equations or multi-line expressions, use proper LaTeX line breaks\n"
                r"- Always include LaTeX formatting even for simple expressions like $5 + 3 = 8$ or $x = 2$\n"
                "\n"
                "Your response should be structured for clarity and ease of understanding, with careful attention to accuracy.\n"
            )   
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.ModelContent(
                        parts=[
                            types.Part.from_text(text=system_message)
                        ]
                    ),
                    types.UserContent(
                        parts=[
                            types.Part.from_text(text=f'Analyze this Thai text image. Apply thorough reasoning and respond with the structured format in clear {language}. Use LaTeX for all mathematical expressions.'),
                            types.Part.from_bytes(
                                mime_type="image/jpeg",
                                data=image_base64,
                            )
                        ]
                    )
                ]
            )
            # Step 1: Get raw response
            response_content = response.text.strip()
  
            # Step 2: Use regex to extract JSON block between the first { and last }
            match = re.search(r'{.*}', response_content, re.DOTALL)
            if not match:
                raise ValueError("No valid JSON object found in model response")

            json_string = match.group(0)

            parsed_response = json.loads(json_string.replace('\\', '\\\\'),strict=False)

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