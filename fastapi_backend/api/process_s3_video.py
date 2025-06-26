from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from lib.supabase_client import supabase
from lib.aws_s3 import s3_downloader
from lib.google_files import google_files_processor, RefrigeratorDiagnosisResult

router = APIRouter()

# Logger
logger = logging.getLogger(__name__)

class RefrigeratorDiagnosisRequest(BaseModel):
    s3Key: str
    fileName: str
    userDescription: Optional[str] = None  # User's description of the refrigerator problem

@router.post("/process-s3-video")
async def process_s3_video(request: RefrigeratorDiagnosisRequest):
    """Diagnose refrigerator issues from S3 video with streaming response"""
    
    if not request.s3Key or not request.fileName:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: s3Key, fileName"
        )

    logger.info(f"Processing refrigerator video: {request.s3Key}, fileName: {request.fileName}")

    async def stream_response():
        try:
            yield json.dumps({
                'type': 'progress',
                'message': 'Downloading refrigerator video from S3...',
                'progress': 10
            }) + '\n'

            # Step 1: Download from S3
            download_result = await s3_downloader.download_file(request.s3Key)
            
            yield json.dumps({
                'type': 'progress',
                'message': 'Uploading to AI analysis service...',
                'progress': 30
            }) + '\n'

            # Step 2: Upload to Google Files API
            upload_result = await google_files_processor.upload_to_google_files(
                download_result['buffer'],
                request.fileName,
                download_result['contentType']
            )

            yield json.dumps({
                'type': 'progress',
                'message': 'Waiting for video processing...',
                'progress': 50
            }) + '\n'

            # Step 3: Wait for Google processing
            await google_files_processor.wait_for_file_processing(upload_result.name)

            yield json.dumps({
                'type': 'progress',
                'message': 'Analyzing refrigerator and diagnosing issues...',
                'progress': 70
            }) + '\n'

            # Step 4: Process with refrigerator-specific AI
            result = await google_files_processor.process_refrigerator_video(
                upload_result.file_uri,
                upload_result.name,
                download_result['contentType'],
                request.userDescription
            )

            yield json.dumps({
                'type': 'progress',
                'message': 'Cleaning up temporary files...',
                'progress': 85
            }) + '\n'

            # Step 5: Cleanup Google Files
            await google_files_processor.delete_google_file(upload_result.name)

            yield json.dumps({
                'type': 'progress',
                'message': 'Saving diagnosis to database...',
                'progress': 90
            }) + '\n'

            # Step 6: Save to database
            try:
                if not supabase:
                    raise Exception('Database service not available. Please configure Supabase environment variables.')
                    
                db_result = supabase.table('refrigerator_diagnoses').insert({
                    'video_id': request.s3Key,
                    'file_name': request.fileName,
                    'video_url': f's3://{request.s3Key}',
                    'user_description': request.userDescription,
                    'brand': result.brand,
                    'model': result.model,
                    'refrigerator_type': result.refrigerator_type,
                    'issue_category': result.issue_category,
                    'severity_level': result.severity_level,
                    'diagnosis_result': result.diagnosis_result,
                    'solutions': result.solutions,
                    'audio_summary': result.audio_summary,
                    'ai_model': 'gemini-2.0-flash-001',
                    'created_at': datetime.utcnow().isoformat()
                }).execute()

                if not db_result.data:
                    raise Exception('No data returned from database insert')

                diagnosis_data = db_result.data[0]

            except Exception as db_error:
                logger.error(f'Database error: {str(db_error)}')
                raise Exception('Failed to save diagnosis to database')

            yield json.dumps({
                'type': 'complete',
                'message': 'Refrigerator diagnosis completed successfully!',
                'progress': 100,
                'diagnosis_result': result.diagnosis_result,
                'solutions': result.solutions,
                'audio_summary': result.audio_summary,
                'diagnosisId': str(diagnosis_data['id']),
                'fileName': request.fileName,
                's3Key': request.s3Key
            }) + '\n'

        except Exception as error:
            logger.error(f'Refrigerator diagnosis failed: {str(error)}')
            yield json.dumps({
                'type': 'error',
                'message': str(error) if str(error) else 'Failed to diagnose refrigerator',
                'progress': 0
            }) + '\n'

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    ) 