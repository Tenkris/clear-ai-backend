from fastapi import APIRouter, Depends, Response, HTTPException
from app.models.user import UserModel
from app.schemas.user import UserCreate ,UserLogin , UserResponse , UserUpdate
from app.services.auth import AuthService
from app.middleware.auth import verify_token
from pynamodb.exceptions import DoesNotExist

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=dict)
async def register(user: UserCreate):
    """
    Register a new user
    """
    try:
        result = await auth_service.register(user)
        return {"success": True, "data": result}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        print("error", e)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=dict)
async def login(user_credentials: UserLogin):
    """
    Login user
    """
    try:
        result = await auth_service.login(user_credentials.email, user_credentials.password)
        return {"success": True, "data": result}
    except Exception as e:
        print("error", e)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/logout")
async def logout(response: Response):
    """
    Logout user
    """
    response.delete_cookie("token")
    return {"success": True, "data": {}} 

