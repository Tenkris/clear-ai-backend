from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from app.services.image_service import ImageService
from app.services.llm_service import LLMService
from app.services.translation_service import TranslationService
from app.schemas.response import ImageProcessingResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["upload"],
    responses={404: {"description": "Not found"}},
)

# Initialize services
image_service = ImageService()

@router.post("/upload", response_model=ImageProcessingResponse)
async def upload_image(
    file: UploadFile = File(...),
    llm_service: LLMService = Depends(lambda: LLMService()),
    translation_service: TranslationService = Depends(lambda: TranslationService())
) -> Dict[str, Any]:
    """
    Process an uploaded Thai image:
    1. Prepare image for LLM processing
    2. Send image directly to LLM to get English reasoning and structured answer
    3. Translate to Thai with 3 sections: question understanding, solving strategy, and step-by-step solution
    4. Return final result
    
    Args:
        file: The uploaded image file
        llm_service: Service for LLM processing
        translation_service: Service for translation
        
    Returns:
        Dict[str, Any]: The response containing the processed data with Thai translations
    """
    try:
        # Step 1: Prepare image for LLM
        logger.info(f"Processing image: {file.filename}")
        base64_image = await image_service.prepare_image_for_llm(file)
        logger.info(f"Image prepared for LLM processing: {file.filename}")
        
        # Step 2: Process image with LLM to get English analysis
        logger.info("Processing image with LLM")
        english_result = await llm_service.process_thai_image(base64_image)
        logger.info("LLM processing complete")
        
        # Step 3: Translate the complete analysis to Thai
        logger.info("Translating analysis to Thai")
        thai_result = await translation_service.translate_to_thai(english_result)
        logger.info("Translation complete")
        
        # Step 4: Return the final result
        return thai_result
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}") 