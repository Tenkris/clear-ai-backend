import os
import base64
import tempfile
from PIL import Image
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

class ImageService:
    """Service for handling image processing."""

    @staticmethod
    async def prepare_image_for_llm(file: UploadFile) -> str:
        """Prepare uploaded image for LLM processing.
        
        Args:
            file: The uploaded image file
            
        Returns:
            str: The base64 encoded image
            
        Raises:
            HTTPException: If there's an error processing the image
        """
        try:
            # Create a temporary file to store the uploaded image
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp_path = temp.name
                # Write the uploaded file content to the temporary file
                contents = await file.read()
                temp.write(contents)
            
            # Encode the image as base64
            with open(temp_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Remove temporary file after processing
            os.unlink(temp_path)
            
            if not encoded_image:
                raise HTTPException(status_code=400, detail="Failed to encode image")
                
            return encoded_image
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}") 