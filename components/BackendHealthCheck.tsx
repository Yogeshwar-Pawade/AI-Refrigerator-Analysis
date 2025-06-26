"use client"

import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, XCircle, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { checkBackendHealth, getApiUrl, API_CONFIG } from '@/lib/config'

interface BackendStatus {
  isHealthy: boolean
  isChecking: boolean
  lastChecked: Date | null
  error: string | null
  response?: any
}

export function BackendHealthCheck() {
  const [status, setStatus] = useState<BackendStatus>({
    isHealthy: false,
    isChecking: true,
    lastChecked: null,
    error: null
  })

  const checkHealth = async () => {
    setStatus(prev => ({ ...prev, isChecking: true, error: null }))
    
    try {
      const response = await fetch(getApiUrl('/health'), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setStatus({
          isHealthy: true,
          isChecking: false,
          lastChecked: new Date(),
          error: null,
          response: data
        })
      } else {
        throw new Error(`Backend returned ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      setStatus({
        isHealthy: false,
        isChecking: false,
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error',
        response: null
      })
    }
  }

  useEffect(() => {
    checkHealth()
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          {status.isHealthy ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-500" />
          )}
          Backend Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Connection</span>
          <Badge variant={status.isHealthy ? "default" : "destructive"} className="flex items-center gap-1">
            {status.isChecking ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : status.isHealthy ? (
              <CheckCircle className="h-3 w-3" />
            ) : (
              <XCircle className="h-3 w-3" />
            )}
            {status.isChecking ? 'Checking...' : status.isHealthy ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Backend URL</span>
          <span className="text-xs font-mono truncate max-w-32" title={API_CONFIG.BASE_URL}>
            {API_CONFIG.BASE_URL.replace('https://', '')}
          </span>
        </div>

        {status.lastChecked && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Last Checked</span>
            <span className="text-xs">{formatTime(status.lastChecked)}</span>
          </div>
        )}

        {status.error && (
          <div className="rounded-md bg-red-50 p-2 border border-red-200">
            <p className="text-xs text-red-600 break-words">{status.error}</p>
          </div>
        )}

        {status.response?.status === 'healthy' && (
          <div className="rounded-md bg-green-50 p-2 border border-green-200">
            <p className="text-xs text-green-600">
              Backend is running (v{status.response.version || '1.0.0'})
            </p>
          </div>
        )}

        <Button 
          variant="outline" 
          size="sm" 
          onClick={checkHealth}
          disabled={status.isChecking}
          className="w-full"
        >
          {status.isChecking ? (
            <>
              <RefreshCw className="h-3 w-3 mr-2 animate-spin" />
              Checking...
            </>
          ) : (
            <>
              <RefreshCw className="h-3 w-3 mr-2" />
              Check Again
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
} 