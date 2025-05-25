from typing import Any, Dict, Optional, List
from pydantic import BaseModel


class ResponseModel(BaseModel):
    """Base response model."""
    success: bool
    message: str
    data: Optional[Any] = None


class ImageProcessingResponse(ResponseModel):
    """Response model for image processing."""
    data: Dict[str, Any]
    s3_url: str
    question_id: str
    

class UploadResponse(BaseModel):
    """Simplified response model for upload endpoint."""
    success: bool
    message: str
    question_id: str
    response_time: float


class SolutionResponse(BaseModel):
    """Model for the solution structure."""
    question_understanding: str
    solving_strategy: str
    solution_steps: List[str] 