// API Configuration for FastAPI Backend
export const API_CONFIG = {
  // FastAPI backend URL - Railway deployment
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'https://ai-analysis-backend-production.up.railway.app',
  
  // API endpoints
  ENDPOINTS: {
    SUMMARIZE: '/api/summarize',
    PROCESS_VIDEO: '/api/process-video',
    PROCESS_S3_VIDEO: '/api/process-s3-video',
    UPLOAD_PRESIGNED: '/api/upload/presigned',
    HISTORY: '/api/history',
    DELETE_SUMMARY: '/api/history',
    CHAT_CONVERSATIONS: '/api/chat/conversations',
    CHAT_CONVERSATION: '/api/chat/conversation',
    CHAT_MESSAGE: '/api/chat/message',
    HEALTH: '/health',
  }
}

// Helper function to build full API URLs
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}

// Helper function for API fetch with proper error handling
export const apiRequest = async (endpoint: string, options?: RequestInit) => {
  const url = getApiUrl(endpoint)
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  }

  const response = await fetch(url, defaultOptions)
  
  if (!response.ok) {
    let errorMessage = `HTTP error! status: ${response.status}`
    try {
      const errorData = await response.json()
      errorMessage = errorData.detail || errorData.message || errorMessage
    } catch {
      // If we can't parse JSON, use the default message
    }
    throw new Error(errorMessage)
  }
  
  return response
}

// Health check function
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.HEALTH), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return response.ok
  } catch (error) {
    console.error('Backend health check failed:', error)
    return false
  }
} 