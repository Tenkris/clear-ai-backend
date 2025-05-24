from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta, timezone
from app.utils.config import Config
from app.models.user import UserModel
from pynamodb.exceptions import DoesNotExist

security = HTTPBearer()

async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, Config.JWT_SECRET, algorithm="HS256")

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, Config.JWT_SECRET, algorithms=["HS256"])
        try:
            user = UserModel.get(payload["sub"])
            return payload
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def check_permissions(allowed_roles):
    async def wrapper(payload: dict = Depends(verify_token)):
        if payload.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"User role {payload.get('role')} is not authorized to access this route"
            )
        return payload
    return wrapper 