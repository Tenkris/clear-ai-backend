from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, Optional
import time

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
    language: Optional[str] = Query("thai", description="Response language: 'english' for faster response or 'thai' for Thai translation"),
    llm_service: LLMService = Depends(lambda: LLMService()),
    translation_service: TranslationService = Depends(lambda: TranslationService())
) -> Dict[str, Any]:
    """
    Process an uploaded Thai image:
    1. Prepare image for LLM processing
    2. Send image directly to LLM to get English reasoning and structured answer
    3. If language=thai, translate to Thai with 3 sections: question understanding, solving strategy, and step-by-step solution
    4. Return final result
    
    Args:
        file: The uploaded image file
        language: Response language - 'english' for faster response or 'thai' for Thai translation
        llm_service: Service for LLM processing
        translation_service: Service for translation
        
    Returns:
        Dict[str, Any]: The response containing the processed data in English or Thai
    """
    try:
        start_time = time.time()
        
        # Step 1: Prepare image for LLM
        logger.info(f"Processing image: {file.filename}")
        base64_image = await image_service.prepare_image_for_llm(file)
        logger.info(f"Image prepared for LLM processing: {file.filename}")
        
        # Step 2: Process image with LLM to get English analysis
        logger.info("Processing image with LLM")
        english_result = await llm_service.process_thai_image(base64_image)
        logger.info("LLM processing complete")
        
        # Step 3: Either return English result or translate to Thai based on language parameter
        if language.lower() == "english":
            logger.info("Returning English result directly")
            result = {
                "success": True,
                "message": "Image processed successfully (English)",
                "data": english_result
            }
        else:
            # Translate to Thai
            logger.info("Translating analysis to Thai")
            thai_result = await translation_service.translate_to_thai(english_result)
            logger.info("Translation complete")
            result = thai_result
        
        # Log processing time
        processing_time = time.time() - start_time
        logger.info(f"Request processed in {processing_time:.2f} seconds")
        
        # Step 4: Return the final result
        return result
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}") 