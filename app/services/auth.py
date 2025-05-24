from fastapi import HTTPException
from passlib.context import CryptContext
import httpx
from app.models.user import UserModel
from app.schemas.user import UserCreate, UserResponse 
from app.middleware.auth import create_access_token
from app.utils.config import Config
from pynamodb.exceptions import DoesNotExist

from app.services.logger import Logger

logger = Logger()

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def register(self, user: UserCreate):
        try:
            UserModel.get(user.email)
            raise HTTPException(status_code=409, detail="Email already registered")
        except DoesNotExist:

            hashed_password = self.pwd_context.hash(user.password)
            
            new_user = UserModel(
                email=user.email,
                role=user.role,
                password=hashed_password,
                age = user.age,
            )
            new_user.save()
            
            token = await create_access_token({"sub": user.email, "role": user.role})
            
            return {"token": token, "user": UserResponse(**new_user.to_dict())}

    async def login(self, email: str, password: str):
        try:
            user = UserModel.get(email)
            
            if not self.pwd_context.verify(password, user.password):
                raise HTTPException(status_code=400, detail="Invalid credentials")
            
            token = await create_access_token({"sub": user.email, "role": user.role})
            
            return {"token": token, "user": UserResponse(**user.to_dict())}
            
        except DoesNotExist:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        except Exception as e:
            logger.log_user_error(
                user_email=email,
                error=e,
                function_name="login"
            )
            raise HTTPException(status_code=400, detail=str(e)) 
        
