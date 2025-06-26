"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { VideoUploadS3 } from "@/components/VideoUploadS3"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { FileVideo, History, Upload, Sparkles } from "lucide-react"
import { getApiUrl, API_CONFIG } from "@/lib/config"
import Link from "next/link"

export default function Home() {
  const [s3Key, setS3Key] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState("")
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleVideoUploaded = (uploadedS3Key: string, uploadedFileName: string) => {
    setS3Key(uploadedS3Key)
    setFileName(uploadedFileName)
    setError(null)
  }

  const handleUploadProgress = (progress: number) => {
    setProgress(progress)
  }

  const processS3Video = async () => {
    if (!s3Key || !fileName) return

    setIsProcessing(true)
    setProgress(0)
    setError(null)
    setProgressMessage("Initializing analysis...")

    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.PROCESS_S3_VIDEO), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          s3Key,
          fileName,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to process S3 video')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Failed to read response stream')
      }

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line)
              
              if (data.type === 'progress') {
                setProgress(data.progress)
                setProgressMessage(data.message)
              } else if (data.type === 'complete') {
                setProgress(100)
                setProgressMessage("Analysis complete! Redirecting...")
                // Show completion notification
                setTimeout(() => {
                  router.push(`/history/${data.diagnosisId}`)
                }, 1500)
              } else if (data.type === 'error') {
                throw new Error(data.message)
              }
            } catch (parseError) {
              // Skip lines that aren't valid JSON
              console.debug('Skipping non-JSON line:', line)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error processing S3 video:', error)
      setError(error instanceof Error ? error.message : 'Failed to process S3 video')
      setProgress(0)
      setProgressMessage("")
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <FileVideo className="h-4 w-4 text-primary-foreground" />
              </div>
              <h1 className="text-xl font-semibold text-foreground">Refrigerator Diagnostic Tool</h1>
            </div>
            <Link 
              href="/history"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors px-4 py-2 rounded-lg hover:bg-muted"
            >
              <History className="h-4 w-4" />
              History
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto space-y-12">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <h2 className="text-4xl font-bold text-foreground">
              AI-Powered Refrigerator Diagnosis
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Upload a video of your refrigerator problem and get instant AI diagnosis with step-by-step repair solutions.
            </p>
          </div>

          {/* Upload Section */}
          <Card className="card-interactive">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Upload className="h-6 w-6 text-primary" />
                Upload Refrigerator Video
              </CardTitle>
              <CardDescription>
                Upload a video showing your refrigerator problem to get AI-powered diagnosis and repair solutions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <VideoUploadS3
                onVideoUploaded={handleVideoUploaded}
                onProgress={handleUploadProgress}
                maxDuration={30}
              />
              
              {/* Processing Progress */}
              {isProcessing && (
                <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl shadow-lg">
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900">Diagnosing Refrigerator</p>
                            <p className="text-sm text-slate-600">{progressMessage || "Analyzing refrigerator problem..."}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-blue-600">{progress}%</p>
                          <p className="text-xs text-slate-500">Complete</p>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Progress 
                          value={progress} 
                          className="h-3 bg-slate-200 rounded-full"
                        />
                        <div className="flex justify-between text-xs text-slate-500">
                          <span>Started</span>
                          <span>In Progress</span>
                          <span>Complete</span>
                        </div>
                      </div>

                      {progress >= 100 && (
                        <div className="bg-green-50 rounded-xl p-3 border border-green-200">
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-sm font-medium text-green-800">
                              Diagnosis complete! Redirecting to results...
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Error Display */}
              {error && (
                <Card className="border-destructive/20 bg-destructive/5">
                  <CardContent className="p-4">
                    <div className="text-destructive text-sm">
                      <strong>Error:</strong> {error}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Generate Summary Button */}
              {s3Key && !isProcessing && (
                <Button 
                  onClick={processS3Video}
                  className="w-full interactive-button" 
                  size="lg"
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  Start Diagnosis
                </Button>
              )}
            </CardContent>
          </Card>

          {/* How it Works */}
          <Card>
            <CardHeader>
              <CardTitle>How It Works</CardTitle>
              <CardDescription>Simple steps to diagnose your refrigerator problems</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-8">
                <div className="text-center space-y-3">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                    <span className="text-2xl font-bold text-primary">1</span>
                  </div>
                  <h3 className="font-semibold">Upload Refrigerator Video</h3>
                  <p className="text-sm text-muted-foreground">
                    Record and upload a video showing your refrigerator problem or unusual behavior
                  </p>
                </div>
                <div className="text-center space-y-3">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                    <span className="text-2xl font-bold text-primary">2</span>
                  </div>
                  <h3 className="font-semibold">AI Diagnosis</h3>
                  <p className="text-sm text-muted-foreground">
                    Our AI analyzes your video to identify the brand, model, and diagnose the specific problem
                  </p>
                </div>
                <div className="text-center space-y-3">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                    <span className="text-2xl font-bold text-primary">3</span>
                  </div>
                  <h3 className="font-semibold">Get Solutions & Chat</h3>
                  <p className="text-sm text-muted-foreground">
                    Receive step-by-step repair solutions and chat with AI for additional guidance
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}

