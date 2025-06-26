from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from lib.supabase_client import supabase

router = APIRouter()

# Logger
logger = logging.getLogger(__name__)

class RefrigeratorDiagnosisItem(BaseModel):
    id: str
    videoId: str
    fileName: str
    brand: Optional[str] = None
    model: Optional[str] = None
    issueCategory: Optional[str] = None
    severityLevel: Optional[str] = None
    diagnosisResult: str
    solutions: str
    audioSummary: Optional[str] = None
    createdAt: str

class HistoryResponse(BaseModel):
    diagnoses: List[RefrigeratorDiagnosisItem]

class DeleteResponse(BaseModel):
    success: bool
    message: str

@router.get("/history", response_model=HistoryResponse)
async def get_refrigerator_diagnoses_history():
    """Get all refrigerator diagnoses from the database"""
    
    try:
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail={"error": "Database service not available. Please configure Supabase environment variables."}
            )
            
        result = supabase.table('refrigerator_diagnoses').select('*').order('created_at', desc=True).execute()
        
        if result.data is None:
            logger.error('Failed to fetch refrigerator diagnoses from database')
            raise HTTPException(
                status_code=500,
                detail={"error": "Failed to fetch refrigerator diagnoses"}
            )

        processed_diagnoses = []
        for diagnosis in result.data:
            # Process each diagnosis to match the expected format
            processed_diagnosis = RefrigeratorDiagnosisItem(
                id=str(diagnosis.get('id', '')),
                videoId=diagnosis.get('video_id', ''),
                fileName=diagnosis.get('file_name', ''),
                brand=diagnosis.get('brand'),
                model=diagnosis.get('model'),
                issueCategory=diagnosis.get('issue_category'),
                severityLevel=diagnosis.get('severity_level'),
                diagnosisResult=diagnosis.get('diagnosis_result', ''),
                solutions=diagnosis.get('solutions', ''),
                audioSummary=diagnosis.get('audio_summary'),
                createdAt=diagnosis.get('created_at', '')
            )
            processed_diagnoses.append(processed_diagnosis)

        return HistoryResponse(diagnoses=processed_diagnoses)
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f'Error fetching refrigerator diagnoses: {str(error)}')
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch refrigerator diagnoses"}
        )

@router.delete("/history/{diagnosis_id}", response_model=DeleteResponse)
async def delete_refrigerator_diagnosis(diagnosis_id: str):
    """Delete a refrigerator diagnosis"""
    
    try:
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail={"error": "Database service not available. Please configure Supabase environment variables."}
            )
        
        # First, verify the diagnosis exists
        diagnosis_result = supabase.table('refrigerator_diagnoses').select('*').eq('id', diagnosis_id).execute()
        if not diagnosis_result.data:
            raise HTTPException(
                status_code=404,
                detail={"error": "Refrigerator diagnosis not found"}
            )
        
        # Delete the diagnosis
        diagnosis_delete = supabase.table('refrigerator_diagnoses').delete().eq('id', diagnosis_id).execute()
        
        if not diagnosis_delete.data:
            raise HTTPException(
                status_code=500,
                detail={"error": "Failed to delete refrigerator diagnosis"}
            )
        
        logger.info(f"Successfully deleted refrigerator diagnosis {diagnosis_id}")
        return DeleteResponse(
            success=True,
            message="Refrigerator diagnosis deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f'Error deleting refrigerator diagnosis {diagnosis_id}: {str(error)}')
        raise HTTPException(
            status_code=500,
            detail={"error": f"Failed to delete refrigerator diagnosis: {str(error)}"}
        ) 