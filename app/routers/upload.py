from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, Optional
import time
from app.middleware.auth import verify_token

from app.services.image_service import ImageService
from app.services.llm_service import LLMService
from app.services.translation_service import TranslationService
from app.services.s3_service import S3Service
from app.services.question import QuestionService
from app.schemas.response import UploadResponse
from app.schemas.question import QuestionCreate

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize services
image_service = ImageService()
s3_service = S3Service()

@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    language: Optional[str] = Query("thai", description="Response language: 'english' for faster response or 'thai' for Thai translation"),
    llm_service: LLMService = Depends(lambda: LLMService()),
    translation_service: TranslationService = Depends(lambda: TranslationService())
) -> UploadResponse:
    """
    Process an uploaded Thai image:
    1. Upload image to S3 bucket
    2. Prepare image for LLM processing
    3. Send image directly to LLM to get English reasoning and structured answer
    4. If language=thai, translate to Thai with 3 sections: question understanding, solving strategy, and step-by-step solution
    5. Create a question in the database
    6. Return only question_id and response_time
    
    Args:
        file: The uploaded image file
        language: Response language - 'english' for faster response or 'thai' for Thai translation
        llm_service: Service for LLM processing
        translation_service: Service for translation
        
    Returns:
        UploadResponse: Response containing only question_id and response_time
    """
    try:
        start_time = time.time()
        
        # Step 1: Upload image to S3
        logger.info(f"Uploading image to S3: {file.filename}")
        s3_url = await s3_service.upload_image(file, folder="questions")
        logger.info(f"Image uploaded to S3: {s3_url}")
        
        # Reset file pointer to read again for LLM processing
        await file.seek(0)
        
        # Step 2: Prepare image for LLM
        logger.info(f"Processing image: {file.filename}")
        base64_image = await image_service.prepare_image_for_llm(file)
        logger.info(f"Image prepared for LLM processing: {file.filename}")
        
        # Step 3: Process image with LLM to get English analysis
        logger.info("Processing image with LLM")
        english_result = await llm_service.process_thai_image(base64_image)
        logger.info("LLM processing complete")
        
        # Step 4: Either use English result or translate to Thai based on language parameter
        if language.lower() == "english":
            logger.info("Using English result")
            processed_data = english_result
        else:
            # Translate to Thai
            logger.info("Translating analysis to Thai")
            thai_result = await translation_service.translate_to_thai(english_result)
            logger.info("Translation complete")
            # Extract the data from the thai_result
            processed_data = thai_result["data"]
        
        # Step 5: Create question in database
        logger.info("Creating question in database")
        question_create = QuestionCreate(
            question_understanding=processed_data["question_understanding"],
            solving_strategy=processed_data["solving_strategy"],
            solution_steps=processed_data["solution_steps"],
            conversations=[],
            image_s3=s3_url
        )
        created_question = await QuestionService.create_question(question_create)
        logger.info(f"Question created with ID: {created_question.question_id}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        print(f"Processing time: {processing_time:.2f} seconds")
        logger.info(f"Request processed in {processing_time:.2f} seconds")
        
        # Step 6: Return only question_id and response_time
        return UploadResponse(
            success=True,
            message="Image processed and question created successfully",
            question_id=created_question.question_id,
            response_time=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}") 