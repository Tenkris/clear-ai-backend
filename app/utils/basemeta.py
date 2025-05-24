# app/utils/base_meta.py
from app.utils.config import Config

class BaseMeta:
    region = Config.AWS_REGION_NAME
    aws_access_key_id = Config.AWS_ACCESS_KEY_ID
    aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY