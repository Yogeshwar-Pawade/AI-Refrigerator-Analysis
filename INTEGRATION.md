# AI Analysis Frontend-Backend Integration

This document explains how the frontend is integrated with the Railway-hosted backend.

## Backend Information

- **Backend URL**: `https://ai-analysis-backend-production.up.railway.app`
- **Framework**: FastAPI (Python)
- **Hosting**: Railway
- **Features**: Video analysis, AI diagnosis, chat interface, file upload

## Frontend Configuration

### Environment Variables

Create a `.env.local` file in the root directory:

```bash
# Backend API Configuration
NEXT_PUBLIC_API_BASE_URL=https://ai-analysis-backend-production.up.railway.app

# Supabase Configuration (if needed for frontend features)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### API Configuration

The frontend automatically connects to the Railway backend through:

- **Config File**: `lib/config.ts`
- **Default Backend**: Railway URL is hardcoded as fallback
- **Environment Override**: Use `NEXT_PUBLIC_API_BASE_URL` to override

## Available API Endpoints

### Core Endpoints
- `GET /health` - Backend health check
- `POST /api/upload/presigned` - Get S3 upload URL
- `POST /api/process-s3-video` - Process uploaded video
- `GET /api/history` - Get diagnosis history
- `DELETE /api/history/{id}` - Delete diagnosis

### Chat Endpoints
- `GET /api/chat/conversations/{id}` - Get conversations
- `POST /api/chat/conversations` - Create conversation
- `POST /api/chat/message` - Send message
- `DELETE /api/chat/conversation/{id}` - Delete conversation

## Components Integration

### 1. Backend Health Check (`components/BackendHealthCheck.tsx`)
- Displays connection status to Railway backend
- Shows backend URL and last check time
- Real-time health monitoring

### 2. Video Upload (`components/VideoUploadS3.tsx`)
- Uses Railway backend for presigned S3 URLs
- Streams upload progress
- Handles video validation

### 3. Video Processing (`app/page.tsx`)
- Streams processing updates from Railway
- Real-time progress tracking
- Error handling and retry logic

### 4. History Management (`app/history/`)
- Fetches diagnosis history from Railway
- Individual diagnosis details
- Delete functionality

### 5. Chat Interface (`components/ChatInterface.tsx`)
- Real-time chat with AI
- Conversation management
- Message history

## Development Commands

```bash
# Start with Railway backend (default)
npm run dev

# Force Railway backend
npm run dev:railway

# Use local backend (if running locally)
npm run dev:local

# Test backend connectivity
npm run test:backend

# Check current backend URL
npm run check:env
```

## Deployment Options

### Frontend Deployment

1. **Vercel** (Recommended)
   ```bash
   npm run build
   # Deploy to Vercel
   ```

2. **Netlify**
   ```bash
   npm run build
   # Deploy to Netlify
   ```

3. **Railway**
   ```bash
   # Add Railway frontend service
   ```

### Environment Variables for Deployment

Set these in your deployment platform:

```bash
NEXT_PUBLIC_API_BASE_URL=https://ai-analysis-backend-production.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key
```

## CORS Configuration

The backend is configured to accept requests from:
- `localhost:3000` (development)
- `*.vercel.app` (Vercel deployments)
- `*.netlify.app` (Netlify deployments)
- `*.railway.app` (Railway deployments)

## Features Integration Status

✅ **Completed Integrations:**
- Backend health monitoring
- Video upload to S3 via Railway
- Video processing with streaming updates
- Diagnosis history viewing
- Chat interface with AI
- Real-time progress tracking
- Error handling and retry logic

✅ **Working API Routes:**
- `/health` - Health check
- `/api/upload/presigned` - S3 upload URLs
- `/api/process-s3-video` - Video processing
- `/api/history` - History management
- `/api/chat/*` - Chat functionality

## Troubleshooting

### Common Issues

1. **Backend Not Accessible**
   ```bash
   npm run test:backend
   ```
   - Check if Railway service is running
   - Verify the backend URL

2. **CORS Errors**
   - Ensure your domain is added to backend CORS config
   - Check browser console for specific errors

3. **Environment Variables**
   ```bash
   npm run check:env
   ```
   - Verify environment variables are set
   - Check `.env.local` exists

4. **Upload Failures**
   - Check AWS S3 credentials in Railway backend
   - Verify file size limits (500MB max)
   - Check file format (video/* only)

### Debug Mode

Enable debug logging by adding to `.env.local`:
```bash
NEXT_PUBLIC_DEBUG=true
```

## Monitoring

- **Backend Health**: Monitored via `/health` endpoint
- **Frontend Performance**: Built-in Next.js analytics
- **API Errors**: Console logging and user notifications
- **Railway Logs**: Check Railway dashboard for backend issues

## Security

- **Environment Variables**: Properly scoped with `NEXT_PUBLIC_` prefix
- **API Security**: CORS properly configured
- **File Upload**: Validation and size limits enforced
- **Error Handling**: No sensitive data exposed in error messages

---

For additional support or issues, check:
1. Railway backend logs
2. Browser console errors
3. Network tab for failed requests
4. Backend health check status 