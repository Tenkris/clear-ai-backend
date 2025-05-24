import os
import boto3
import logging
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException, UploadFile
from datetime import datetime
import uuid

from app.utils.config import Config

logger = logging.getLogger(__name__)

class S3Service:
    """Service for handling S3 operations with the clearai-images bucket."""
    
    def __init__(self):
        """Initialize S3 client with credentials from config."""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=Config.AWS_REGION_NAME,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
            )
            self.bucket_name = 'clearai-images'
            logger.info("S3 client initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing S3 service: {str(e)}")
    
    async def upload_image(self, file: UploadFile, folder: str = "uploads") -> str:
        """Upload an image to S3 bucket.
        
        Args:
            file: The uploaded file
            folder: The folder in S3 to store the file
            
        Returns:
            str: The S3 object URL (HTTPS format)
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            s3_key = f"{folder}/{unique_filename}"
            
            # Read file content
            contents = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=contents,
                ContentType=file.content_type or 'image/jpeg'
            )
            
            # Generate HTTPS URL
            # Format: https://bucket-name.s3.region.amazonaws.com/key
            https_url = f"https://{self.bucket_name}.s3.{Config.AWS_REGION_NAME}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded image to S3: {https_url}")
            return https_url
            
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")
    
    async def download_image(self, s3_url: str) -> bytes:
        """Download an image from S3 bucket.
        
        Args:
            s3_url: The S3 URL of the image (s3://bucket/key or https:// format)
            
        Returns:
            bytes: The image content
            
        Raises:
            HTTPException: If download fails
        """
        try:
            # Parse S3 URL - handle both s3:// and https:// formats
            if s3_url.startswith('s3://'):
                parts = s3_url.replace('s3://', '').split('/', 1)
                if len(parts) != 2:
                    raise ValueError("Invalid S3 URL format")
                bucket_name, key = parts
            elif s3_url.startswith('https://'):
                # Parse https://bucket-name.s3.region.amazonaws.com/key format
                url_parts = s3_url.replace('https://', '').split('/')
                if len(url_parts) < 2:
                    raise ValueError("Invalid HTTPS URL format")
                # Extract bucket name from subdomain
                bucket_name = url_parts[0].split('.')[0]
                # Reconstruct key from remaining parts
                key = '/'.join(url_parts[1:])
            else:
                raise ValueError("URL must start with s3:// or https://")
            
            # Download from S3
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            content = response['Body'].read()
            
            logger.info(f"Successfully downloaded image from S3: {s3_url}")
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="Image not found in S3")
            else:
                logger.error(f"S3 download error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to download image from S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")
    
    async def delete_image(self, s3_url: str) -> bool:
        """Delete an image from S3 bucket.
        
        Args:
            s3_url: The S3 URL of the image to delete (s3:// or https:// format)
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Parse S3 URL - handle both s3:// and https:// formats
            if s3_url.startswith('s3://'):
                parts = s3_url.replace('s3://', '').split('/', 1)
                if len(parts) != 2:
                    raise ValueError("Invalid S3 URL format")
                bucket_name, key = parts
            elif s3_url.startswith('https://'):
                # Parse https://bucket-name.s3.region.amazonaws.com/key format
                url_parts = s3_url.replace('https://', '').split('/')
                if len(url_parts) < 2:
                    raise ValueError("Invalid HTTPS URL format")
                # Extract bucket name from subdomain
                bucket_name = url_parts[0].split('.')[0]
                # Reconstruct key from remaining parts
                key = '/'.join(url_parts[1:])
            else:
                raise ValueError("URL must start with s3:// or https://")
            
            # Delete from S3
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
            
            logger.info(f"Successfully deleted image from S3: {s3_url}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 deletion error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete image from S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")
    
    def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for temporary access to an S3 object.
        
        Args:
            s3_url: The S3 URL of the object (s3:// or https:// format)
            expiration: Time in seconds for the URL to remain valid (default: 1 hour)
            
        Returns:
            str: The presigned URL
            
        Raises:
            HTTPException: If URL generation fails
        """
        try:
            # Parse S3 URL - handle both s3:// and https:// formats
            if s3_url.startswith('s3://'):
                parts = s3_url.replace('s3://', '').split('/', 1)
                if len(parts) != 2:
                    raise ValueError("Invalid S3 URL format")
                bucket_name, key = parts
            elif s3_url.startswith('https://'):
                # Parse https://bucket-name.s3.region.amazonaws.com/key format
                url_parts = s3_url.replace('https://', '').split('/')
                if len(url_parts) < 2:
                    raise ValueError("Invalid HTTPS URL format")
                # Extract bucket name from subdomain
                bucket_name = url_parts[0].split('.')[0]
                # Reconstruct key from remaining parts
                key = '/'.join(url_parts[1:])
            else:
                raise ValueError("URL must start with s3:// or https://")
            
            # Generate presigned URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for: {s3_url}")
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}") 