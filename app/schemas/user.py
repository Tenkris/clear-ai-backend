from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"
    age: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "password123",
                "role": "user", 
                "age": 30
            }
        }

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: EmailStr
    email: EmailStr
    role: str
    age: Optional[int] = None
    created_at: str

    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "id": "john@example.com",
                "email": "john@example.com",
                "role": "user",
                "age": 30,
                "created_at": "2023-01-01T00:00:00"
            }
        }

class UserUpdate(BaseModel):
    role: Optional[str] = None
    age: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin",
                "age": 31
            }
        }