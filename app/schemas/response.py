from typing import Any, Dict, Optional
from pydantic import BaseModel


class ResponseModel(BaseModel):
    """Base response model."""
    success: bool
    message: str
    data: Optional[Any] = None


class ImageProcessingResponse(ResponseModel):
    """Response model for image processing."""
    data: Dict[str, Any] 