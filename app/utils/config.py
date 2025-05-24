import os 
from dotenv import load_dotenv

load_dotenv()
class Config:
    AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    FRONTEND_URL = os.environ.get('FRONTEND_URL')    
    DB_PROFILE = os.environ.get('DB_PROFILE')
    JWT_SECRET = os.environ.get('JWT_SECRET')
                                 