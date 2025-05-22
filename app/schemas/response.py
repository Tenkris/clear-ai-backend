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
    

class SolutionResponse(BaseModel):
    """Model for the solution structure."""
    question_understanding: str
    solving_strategy: str
    solution_steps: List[str] 