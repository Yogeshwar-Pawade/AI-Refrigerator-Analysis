import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Import boto3 with error handling
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError as e:
    logger.error(f"AWS SDK not available: {e}")
    AWS_AVAILABLE = False
    boto3 = None

@dataclass
class UploadProgress:
    loaded: int
    total: int
    percentage: int

@dataclass
class S3UploadResult:
    key: str
    location: str
    bucket: str
    etag: str

class S3MultipartUpload:
    def __init__(self, bucket: Optional[str] = None, key_prefix: str = "videos/"):
        self.bucket = bucket or os.getenv("AWS_S3_BUCKET", "")
        self.key_prefix = key_prefix
        
        if not AWS_AVAILABLE:
            logger.error("AWS SDK is not available")
            self.s3_client = None
            return
        
        if not self.bucket or self.bucket.startswith('your_'):
            logger.warning("AWS S3 bucket name is not configured properly")
            self.s3_client = None
            return
        
        # Check for AWS credentials
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not aws_access_key or not aws_secret_key or aws_access_key.startswith('your_') or aws_secret_key.startswith('your_'):
            logger.warning("AWS credentials are not configured properly")
            self.s3_client = None
            return
        
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            logger.info("✅ AWS S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 client: {e}")
            self.s3_client = None
    
    def is_available(self) -> bool:
        """Check if the S3 client is properly configured"""
        return AWS_AVAILABLE and self.s3_client is not None
    
    async def upload_file(self, file_data: bytes, file_name: str, content_type: str) -> S3UploadResult:
        """Upload a file to S3"""
        if not self.is_available():
            raise Exception("AWS S3 is not properly configured. Check environment variables and dependencies.")
            
        timestamp = int(time.time() * 1000)
        sanitized_name = "".join(c if c.isalnum() or c in ".-_" else "_" for c in file_name)
        key = f"{self.key_prefix}{timestamp}_{sanitized_name}"
        
        try:
            response = self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    'originalName': file_name,
                    'fileSize': str(len(file_data)),
                    'uploadTimestamp': str(timestamp)
                }
            )
            
            return S3UploadResult(
                key=key,
                location=f"https://{self.bucket}.s3.amazonaws.com/{key}",
                bucket=self.bucket,
                etag=response['ETag'].strip('"')
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    async def get_presigned_upload_url(self, file_name: str, file_type: str, file_size: int) -> Dict[str, Any]:
        """Generate a presigned URL for direct client-side upload"""
        if not self.is_available():
            raise Exception("AWS S3 is not properly configured. Check environment variables and dependencies.")
            
        timestamp = int(time.time() * 1000)
        sanitized_name = "".join(c if c.isalnum() or c in ".-_" else "_" for c in file_name)
        key = f"{self.key_prefix}{timestamp}_{sanitized_name}"
        
        try:
            logger.info(f"Generating presigned PUT URL for: {file_name}, type: {file_type}, size: {file_size}")
            
            # Generate presigned URL for PUT operation
            upload_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': key,
                    'ContentType': file_type,
                    'Metadata': {
                        'original-name': file_name,
                        'file-size': str(file_size),
                        'upload-timestamp': str(timestamp)
                    }
                },
                ExpiresIn=3600  # 1 hour
            )
            
            logger.info(f"Generated presigned PUT URL successfully for key: {key}")
            
            return {
                'uploadUrl': upload_url,
                'key': key
            }
        except Exception as e:
            logger.error(f"Failed to generate presigned PUT URL: {e}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")
    
    async def delete_file(self, key: str) -> None:
        """Delete a file from S3"""
        if not self.is_available():
            logger.warning("AWS S3 is not available, cannot delete file")
            return
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def get_file_info(self, key: str) -> Dict[str, Any]:
        """Get file metadata and check if it exists"""
        if not self.is_available():
            raise Exception("AWS S3 is not properly configured. Check environment variables and dependencies.")
            
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return {
                'exists': True,
                'size': response.get('ContentLength'),
                'lastModified': response.get('LastModified'),
                'contentType': response.get('ContentType')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return {'exists': False}
            raise Exception(f"Failed to get file info: {str(e)}")
    
    async def download_file(self, key: str) -> Dict[str, Any]:
        """Download a file from S3"""
        if not self.is_available():
            raise Exception("AWS S3 is not properly configured. Check environment variables and dependencies.")
            
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return {
                'buffer': response['Body'].read(),
                'contentType': response.get('ContentType'),
                'contentLength': response.get('ContentLength')
            }
        except Exception as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise Exception(f"Failed to download file: {str(e)}")

def validate_aws_config() -> Dict[str, Any]:
    """Validate AWS configuration"""
    if not AWS_AVAILABLE:
        return {
            'isValid': False,
            'missing': ['boto3 library not installed']
        }
        
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION',
        'AWS_S3_BUCKET'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing.append(var)
    
    return {
        'isValid': len(missing) == 0 and AWS_AVAILABLE,
        'missing': missing
    }

# Create default instances with error handling
try:
    s3_upload = S3MultipartUpload()
    s3_downloader = S3MultipartUpload()  # For downloading files
    logger.info("✅ S3 clients created successfully")
except Exception as e:
    logger.error(f"Failed to create S3 clients: {e}")
    s3_upload = S3MultipartUpload()
    s3_downloader = S3MultipartUpload() 