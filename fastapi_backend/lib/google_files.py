import google.generativeai as genai
import aiohttp
import asyncio
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import ssl

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Create SSL context that can handle certificate verification issues
def create_ssl_context():
    """Create SSL context with proper certificate handling"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

@dataclass
class GoogleFileUploadResult:
    file_uri: str
    name: str
    mime_type: str
    size_bytes: str
    state: str

@dataclass
class RefrigeratorDiagnosisResult:
    audio_summary: str
    diagnosis_result: str
    solutions: str
    brand: str
    model: str
    refrigerator_type: str
    issue_category: str
    severity_level: str
    duration: Optional[int] = None

class GoogleFilesProcessor:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('Gemini API key is not configured. Please add GEMINI_API_KEY to environment variables.')
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def clean_model_output(self, text: str) -> str:
        """Clean model outputs to remove meta-commentary"""
        import re
        text = re.sub(r'^(Okay|Here\'?s?( is)?|Let me|I will|I\'ll|I can|I would|I am going to|Allow me to|Sure|Of course|Certainly|Alright).*?,\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(Here\'?s?( is)?|I\'?ll?|Let me|I will|I can|I would|I am going to|Allow me to|Sure|Of course|Certainly).*?(summary|translate|breakdown|analysis).*?:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(Based on|According to).*?,\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^I understand.*?[.!]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(Now|First|Let\'s),?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(Here are|The following is|This is|Below is).*?:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(I\'ll provide|Let me break|I\'ll break|I\'ll help|I\'ve structured).*?:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(As requested|Following your|In response to).*?:\s*', '', text, flags=re.IGNORECASE)
        return text.strip()

    def parse_refrigerator_fields(self, diagnosis_text: str) -> Dict[str, str]:
        """Extract structured fields from diagnosis text"""
        import re
        
        # Initialize with defaults
        fields = {
            'brand': 'Unable to determine',
            'model': 'Unable to determine', 
            'refrigerator_type': 'Standard',
            'issue_category': 'General Issue',
            'severity_level': 'Moderate'
        }
        
        try:
            # Extract Brand (multiple patterns)
            brand_patterns = [
                r'Brand:\s*\[([^\]]+)\]',
                r'Brand:\s*([^\n\[]+?)(?:\s*\[|$|\n)',
                r'Brand:\s*([^\n]+)',
                r'Brand\s*:\s*([^\n]+)'
            ]
            for pattern in brand_patterns:
                brand_match = re.search(pattern, diagnosis_text, re.IGNORECASE)
                if brand_match:
                    brand_value = brand_match.group(1).strip()
                    if brand_value and brand_value.lower() not in ['unable to determine', 'not visible', 'unknown']:
                        fields['brand'] = brand_value
                        break
                
            # Extract Model (multiple patterns)
            model_patterns = [
                r'Model Number:\s*\[([^\]]+)\]',
                r'Model Number:\s*([^\n\[]+?)(?:\s*\[|$|\n)',
                r'Model Number:\s*([^\n]+)',
                r'Model\s*Number\s*:\s*([^\n]+)',
                r'Model:\s*([^\n]+)'
            ]
            for pattern in model_patterns:
                model_match = re.search(pattern, diagnosis_text, re.IGNORECASE)
                if model_match:
                    model_value = model_match.group(1).strip()
                    if model_value and model_value.lower() not in ['unable to determine', 'not visible', 'unknown', 'not visible in video']:
                        fields['model'] = model_value
                        break
                
            # Extract Refrigerator Type (multiple patterns)
            type_patterns = [
                r'Refrigerator Type:\s*\[([^\]]+)\]',
                r'Refrigerator Type:\s*([^\n\[]+?)(?:\s*\[|$|\n)',
                r'Refrigerator Type:\s*([^\n]+)',
                r'Type:\s*([^\n]+)'
            ]
            for pattern in type_patterns:
                type_match = re.search(pattern, diagnosis_text, re.IGNORECASE)
                if type_match:
                    type_value = type_match.group(1).strip()
                    if type_value:
                        fields['refrigerator_type'] = type_value
                        break
                
            # Extract Issue Category (multiple patterns)
            category_patterns = [
                r'Primary Issue Category:\s*\[([^\]]+)\]',
                r'Primary Issue Category:\s*([^\n\[]+?)(?:\s*\[|$|\n)',
                r'Primary Issue Category:\s*([^\n]+)',
                r'Issue Category:\s*([^\n]+)',
                r'Problem Category:\s*([^\n]+)'
            ]
            for pattern in category_patterns:
                category_match = re.search(pattern, diagnosis_text, re.IGNORECASE)
                if category_match:
                    category_value = category_match.group(1).strip()
                    if category_value:
                        fields['issue_category'] = category_value
                        break
                
            # Extract Severity Level (multiple patterns)
            severity_patterns = [
                r'Severity Assessment:\s*\[([^\]]+)\]',
                r'Severity Assessment:\s*([^\n\[]+?)(?:\s*\[|$|\n)',
                r'Severity Assessment:\s*([^\n]+)',
                r'Severity:\s*([^\n]+)',
                r'Difficulty:\s*([^\n]+)'
            ]
            for pattern in severity_patterns:
                severity_match = re.search(pattern, diagnosis_text, re.IGNORECASE)
                if severity_match:
                    severity_value = severity_match.group(1).strip()
                    if severity_value:
                        fields['severity_level'] = severity_value
                        break
                
            # Log extracted values for debugging
            logger.info(f'Parsed refrigerator fields: {fields}')
                
        except Exception as e:
            logger.error(f'Error parsing refrigerator fields: {str(e)}')
            
        return fields

    async def upload_to_google_files(self, file_buffer: bytes, file_name: str, mime_type: str) -> GoogleFileUploadResult:
        """Upload file to Google Files API using resumable upload"""
        logger.info(f"Uploading file to Google Files API: {file_name}")

        try:
            # Step 1: Initiate resumable upload
            metadata = {
                "file": {
                    "display_name": file_name,
                },
            }

            logger.info("Starting resumable upload session", {
                "fileName": file_name,
                "fileSize": len(file_buffer),
                "mimeType": mime_type
            })

            # Create SSL context and connector
            ssl_context = create_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                # Step 1: Initiate upload
                init_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={self.api_key}"
                init_headers = {
                    'X-Goog-Upload-Protocol': 'resumable',
                    'X-Goog-Upload-Command': 'start',
                    'X-Goog-Upload-Header-Content-Length': str(len(file_buffer)),
                    'X-Goog-Upload-Header-Content-Type': mime_type,
                    'Content-Type': 'application/json',
                }

                async with session.post(init_url, headers=init_headers, json=metadata) as init_response:
                    if not init_response.ok:
                        error_text = await init_response.text()
                        logger.error('Failed to initiate resumable upload', {
                            'status': init_response.status,
                            'error': error_text
                        })
                        raise Exception(f"Failed to initiate upload: {init_response.status} - {error_text}")

                    # Step 2: Get upload URL from response headers
                    upload_url = init_response.headers.get('x-goog-upload-url')
                    if not upload_url:
                        raise Exception('No upload URL received from Google Files API')

                    logger.info('Upload session initiated, uploading file data', {'uploadUrl': upload_url})

                # Step 3: Upload the actual file data
                upload_headers = {
                    'Content-Length': str(len(file_buffer)),
                    'X-Goog-Upload-Offset': '0',
                    'X-Goog-Upload-Command': 'upload, finalize',
                }

                async with session.post(upload_url, headers=upload_headers, data=file_buffer) as upload_response:
                    if not upload_response.ok:
                        error_text = await upload_response.text()
                        logger.error('Failed to upload file data', {
                            'status': upload_response.status,
                            'error': error_text
                        })
                        raise Exception(f"Failed to upload file data: {upload_response.status} - {error_text}")

                    result = await upload_response.json()
                    logger.info('File uploaded successfully to Google Files API', result)

                    # Check if the response has the expected structure
                    if not result.get('file') or not result['file'].get('name') or not result['file'].get('uri'):
                        logger.error('Unexpected upload response format', result)
                        raise Exception('Google Files API returned unexpected response format')

                    return GoogleFileUploadResult(
                        file_uri=result['file']['uri'],
                        name=result['file']['name'],
                        mime_type=result['file']['mimeType'],
                        size_bytes=result['file']['sizeBytes'],
                        state=result['file']['state'],
                    )
        except Exception as e:
            logger.error(f'Failed to upload to Google Files API: {str(e)}')
            raise Exception(f"Failed to upload to Google Files API: {str(e)}")

    async def wait_for_file_processing(self, file_name: str, max_wait_time: int = 300000) -> bool:
        """Wait for file processing to complete"""
        logger.info(f"Waiting for file processing: {file_name}")

        start_time = asyncio.get_event_loop().time()
        poll_interval = 5  # 5 seconds

        while (asyncio.get_event_loop().time() - start_time) * 1000 < max_wait_time:
            try:
                # Create SSL context and connector
                ssl_context = create_ssl_context()
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={self.api_key}"
                    async with session.get(url) as response:
                        if not response.ok:
                            error_text = await response.text()
                            logger.error('Failed to check file status', {
                                'status': response.status,
                                'statusText': response.reason,
                                'error': error_text
                            })
                            raise Exception(f"Failed to check file status: {response.status} - {error_text}")

                        file_info = await response.json()
                        logger.info('File processing status', {
                            'state': file_info.get('state'),
                            'name': file_info.get('name'),
                            'mimeType': file_info.get('mimeType')
                        })

                        if file_info.get('state') == 'ACTIVE':
                            logger.info('File processing completed successfully')
                            return True
                        elif file_info.get('state') == 'FAILED':
                            raise Exception('File processing failed on Google servers')

                        logger.info(f"File state: {file_info.get('state')}, waiting {poll_interval}s before next check...")

                        # Wait before next poll
                        await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f'Error checking file processing status: {str(e)}')
                raise e

        raise Exception(f"File processing timeout after {max_wait_time / 1000} seconds")

    async def process_refrigerator_video(self, file_uri: str, google_file_name: str, mime_type: str, user_description: Optional[str] = None) -> RefrigeratorDiagnosisResult:
        """Diagnose refrigerator issues using Gemini"""
        logger.info(f"Diagnosing refrigerator video with Gemini: {google_file_name}")

        try:
            model = genai.GenerativeModel("gemini-2.0-flash-001")

            # Get the file object first
            file_obj = genai.get_file(google_file_name)

            # Extract key problem information from audio (no detailed transcript)
            audio_analysis_prompt = """
            Analyze the audio content of this refrigerator video and extract only the key problem information:

            **EXTRACT ONLY:**
            - Main refrigerator problem described
            - Any error codes or display messages mentioned
            - Specific symptoms mentioned (sounds, temperatures, functions not working)
            - Brand/model information if mentioned
            - Any previous troubleshooting attempts mentioned

            **FORMAT:** Provide a brief summary (2-3 sentences) of the key problem information from the audio.
            **DO NOT:** Provide timestamps or detailed transcription.
            """

            audio_response = model.generate_content([
                file_obj,
                audio_analysis_prompt
            ])

            audio_summary = audio_response.text.strip()

            # Then create the refrigerator diagnosis
            diagnosis_prompt = f"""
            You are a master refrigerator technician with 25+ years of experience diagnosing and repairing all major refrigerator brands (Samsung, LG, Whirlpool, GE, Frigidaire, KitchenAid, Bosch, etc.). 

            **ANALYSIS CONTEXT:**
            - Problem Description from Video: {user_description if user_description else "No specific problem description provided"}
            - Video File: {google_file_name}
            - Task: Provide comprehensive refrigerator analysis and diagnosis

            **INSTRUCTIONS:** Analyze both visual and audio elements carefully. Look for brand logos, model numbers, refrigerator layout, problem descriptions, any sounds/noises, and visible issues.

            **AUDIO ANALYSIS SUMMARY:** {audio_summary}

            Provide your expert analysis in this EXACT format:

            🏠 **REFRIGERATOR IDENTIFICATION & FEATURES:**
            Brand: [Identify brand from logos, design, or state "Unable to determine"]
            Model Number: [Look for model stickers/plates or state "Not visible in video"]
            Refrigerator Type: [Top Freezer, Bottom Freezer, Side-by-Side, French Door, Compact, Built-in]
            Estimated Age: [Based on design, features, condition: "1-2 years", "3-5 years", "5-10 years", "10+ years"]
            Estimated Capacity: [Based on size: "10-15 cu ft", "16-20 cu ft", "21-25 cu ft", "26+ cu ft", or "Compact <10 cu ft"]
            
            Key Features Observed:
            • Ice Maker: [Present/Not Present/Not Visible] - [Type: In-door, Freezer compartment, External dispenser]
            • Water Dispenser: [Present/Not Present/Not Visible] - [Internal/External]
            • Display Panel: [Digital/Manual/None visible] - [Working/Not working/Not clear]
            • Door Configuration: [Single/Double/Triple door layout]
            • Special Features: [List any visible: LED lighting, drawers, shelves, temperature zones, etc.]

            ❄️ **DETAILED PROBLEM ANALYSIS:**
            Primary Issue Category: [Ice Making Problems, Cooling/Temperature Issues, Water Dispenser Issues, Strange Noises/Sounds, Door Problems, Electrical Issues, Leaking/Water Issues, Other]
            
            Severity Assessment: [Simple DIY Fix, Moderate Repair, Complex Professional Repair]
            
            **PROBLEM STATEMENT:**
            [Write a clear, comprehensive description of the exact problem based on video evidence and user description]
            
            **SYMPTOMS OBSERVED:**
            • Visual Symptoms: [List everything you see wrong in the video]
            • Audio Symptoms: [List any sounds, noises, or spoken problems]
            • Reported Symptoms: [Summarize what was described in the video]
            
            **ROOT CAUSE ANALYSIS:**
            Most Likely Causes (in order of probability):
            1. [Primary cause with technical explanation]
            2. [Secondary cause with explanation]  
            3. [Tertiary cause with explanation]
            
            **TECHNICAL DIAGNOSIS:**
            [Provide technical explanation of why this problem occurs, which components are involved]

            🔧 **COMPREHENSIVE SOLUTIONS:**
            [Provide detailed solutions based on severity level]

            ⚠️ **SAFETY WARNINGS & PROFESSIONAL RECOMMENDATIONS:**
            **SAFETY FIRST:**
            • [List all safety precautions before attempting any fixes]
            • [Electrical safety warnings if applicable]
            • [When to disconnect power/water]
            
            **CALL PROFESSIONAL SERVICE IF:**
            • [Specific conditions requiring professional help]
            • [Signs that indicate complex electrical/refrigerant issues]
            • [Warranty considerations]
            
            **ESTIMATED COST:**
            • DIY Repair: [Cost range for parts/supplies]
            • Professional Repair: [Estimated service cost range]
            
            **PREVENTION TIPS:**
            [How to prevent this problem in the future]
            """

            # Process the refrigerator video
            diagnosis_response = model.generate_content([
                file_obj,
                diagnosis_prompt
            ])

            diagnosis_text = diagnosis_response.text.strip()

            # Extract solutions from diagnosis  
            solutions_prompt = f"""
            Based on the refrigerator problem analysis, provide comprehensive step-by-step solutions. You are providing expert repair guidance.

            **PROBLEM CONTEXT:** {user_description if user_description else "Refrigerator issue from video analysis"}

            Provide solutions in this EXACT format:

            🔧 **PRIMARY SOLUTION (Recommended)**
            **Solution Name:** [Clear, descriptive name of the fix]
            **Solution Type:** [DIY Simple, DIY Moderate, Professional Required]
            **Time Required:** [Realistic time estimate: "5-10 minutes", "30-45 minutes", "1-2 hours"]
            **Difficulty Level:** [Easy, Medium, Hard]
            **Success Rate:** [High, Medium, Low - based on common success of this fix]

            **TOOLS & MATERIALS NEEDED:**
            • [List specific tools required]
            • [List any replacement parts needed with part numbers if known]
            • [List any supplies like cleaning materials, lubricants, etc.]

            **DETAILED STEP-BY-STEP INSTRUCTIONS:**
            **Preparation:**
            1. [Safety preparation steps]
            2. [Power/water disconnection if needed]
            3. [Access preparation]

            **Main Repair Steps:**
            1. [Detailed step with specific actions]
            2. [Include what to look for, how to test]
            3. [Continue with precise instructions]
            4. [Include reassembly steps]
            5. [Testing and verification steps]

            **TROUBLESHOOTING:**
            • If [specific issue occurs]: [How to resolve]
            • If problem persists: [Next steps to try]

            **SAFETY WARNINGS:**
            ⚠️ [List all safety precautions specific to this repair]
            ⚠️ [Electrical safety if applicable]
            ⚠️ [When to stop and call professional]

            ---

            🔧 **ALTERNATIVE SOLUTION** (If primary doesn't work)
            **Solution Name:** [Alternative approach name]
            **Solution Type:** [DIY Simple, DIY Moderate, Professional Required]
            **Time Required:** [Time estimate]
            **Difficulty Level:** [Easy, Medium, Hard]

            **STEPS:**
            1. [Alternative approach steps]
            2. [Different method to try]
            3. [Continue with alternative process]

            **WHEN THIS IS BETTER:** [Explain when to use this instead of primary solution]

            ---

            🔧 **QUICK TEMPORARY FIX** (If immediate solution needed)
            **Temporary Solution:** [Quick workaround]
            **Duration:** [How long this fix will last]
            **Steps:**
            1. [Quick fix steps]
            2. [Temporary measures]

            **NOTE:** [Explain this is temporary and permanent fix still needed]

            ---

            🚨 **WHEN TO CALL PROFESSIONAL SERVICE IMMEDIATELY:**
            • [Specific dangerous conditions]
            • [Signs of complex electrical/refrigerant issues]
            • [Warranty concerns - don't void warranty]
            • [If multiple attempts have failed]
            • [If special tools/expertise required]

            **PROFESSIONAL SERVICE CONTACT:**
            • Manufacturer warranty service: [When to use]
            • Local appliance repair: [When to use]
            • Emergency service: [When urgent]

            ---

            💡 **COST ANALYSIS:**
            **DIY Repair Costs:**
            • Parts: $[estimate range]
            • Tools (if needed): $[estimate range]
            • Total DIY Cost: $[total range]

            **Professional Repair Costs:**
            • Service Call: $[typical range]
            • Labor: $[estimate range]  
            • Parts: $[estimate range]
            • Total Professional Cost: $[total range]

            **ROI Analysis:** [When DIY vs professional makes financial sense]

            ---

            🛡️ **PREVENTION & MAINTENANCE:**
            **To Prevent This Problem:**
            • [Specific maintenance tasks with frequency]
            • [What to monitor regularly]
            • [Signs to watch for]

            **Regular Maintenance Schedule:**
            • Monthly: [Tasks]
            • Quarterly: [Tasks]
            • Annually: [Tasks]

            **RED FLAGS - Call Professional If You See:**
            • [Warning signs that indicate bigger problems]
            • [Symptoms that suggest professional help needed]
            """

            solutions_response = model.generate_content([
                file_obj,
                solutions_prompt
            ])

            solutions_text = solutions_response.text.strip()

            logger.info('Received refrigerator diagnosis from Gemini', {
                'diagnosisLength': len(diagnosis_text),
                'solutionsLength': len(solutions_text),
                'audioSummaryLength': len(audio_summary)
            })

            # Clean the response text
            diagnosis_content = self.clean_model_output(diagnosis_text)
            solutions_content = self.clean_model_output(solutions_text)
            audio_summary_clean = self.clean_model_output(audio_summary)

            # Parse structured fields from diagnosis
            parsed_fields = self.parse_refrigerator_fields(diagnosis_content)

            return RefrigeratorDiagnosisResult(
                audio_summary=audio_summary_clean,
                diagnosis_result=diagnosis_content,
                solutions=solutions_content,
                brand=parsed_fields['brand'],
                model=parsed_fields['model'],
                refrigerator_type=parsed_fields['refrigerator_type'],
                issue_category=parsed_fields['issue_category'],
                severity_level=parsed_fields['severity_level']
            )

        except Exception as e:
            logger.error(f'Failed to diagnose refrigerator with Gemini: {str(e)}')
            raise Exception(f"Failed to diagnose refrigerator: {str(e)}")



    async def delete_google_file(self, file_name: str) -> None:
        """Delete a file from Google Files API"""
        logger.info(f"Deleting Google file: {file_name}")

        try:
            # Create SSL context and connector
            ssl_context = create_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={self.api_key}"
                async with session.delete(url) as response:
                    if response.ok:
                        logger.info('File deleted successfully from Google Files API')
                    else:
                        error_text = await response.text()
                        logger.error('Failed to delete file from Google Files API', {
                            'status': response.status,
                            'error': error_text
                        })
                        # Don't raise exception for delete failures to avoid breaking the main flow
        except Exception as e:
            logger.error(f'Error deleting file from Google Files API: {str(e)}')
            # Don't raise exception for delete failures



# Create default instance
google_files_processor = GoogleFilesProcessor() 