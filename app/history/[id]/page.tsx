"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ArrowLeft, Clock, FileVideo, MessageSquare, Bot, MessageCircle, Trash2 } from "lucide-react"
import { use } from "react"
import ReactMarkdown from 'react-markdown'
import { getApiUrl, API_CONFIG, apiRequest } from "@/lib/config"
import { ChatInterface } from "@/components/ChatInterface"

interface RefrigeratorDiagnosis {
  id: string
  videoId: string
  fileName: string
  brand: string
  model: string
  refrigeratorType: string
  issueCategory: string
  severityLevel: string
  diagnosisResult: string
  solutions: string
  audioSummary: string
  createdAt: string
}

interface PageProps {
  params: Promise<{ id: string }>
}

export default function HistoryDetailPage({ params }: PageProps) {
  const [diagnosis, setDiagnosis] = useState<RefrigeratorDiagnosis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showChat, setShowChat] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const router = useRouter()
  const { id } = use(params)

  useEffect(() => {
    const fetchDiagnosis = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch all diagnoses and find the one we need
        const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.HISTORY))
        if (!response.ok) {
          throw new Error("Failed to fetch diagnoses")
        }
        const data = await response.json()
        const foundDiagnosis = data.diagnoses.find((diagnosis: RefrigeratorDiagnosis) => diagnosis.id === id)
        
        if (!foundDiagnosis) {
          throw new Error("Refrigerator diagnosis not found")
        }
        
        setDiagnosis(foundDiagnosis)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load refrigerator diagnosis")
      } finally {
        setLoading(false)
      }
    }

    fetchDiagnosis()
  }, [id])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const handleDeleteDiagnosis = async () => {
    if (!diagnosis) return
    
    const confirmDelete = window.confirm(
      `Are you sure you want to delete this refrigerator diagnosis?\n\nThis will permanently delete the diagnosis and all associated conversations. This action cannot be undone.`
    )
    
    if (!confirmDelete) return

    try {
      setIsDeleting(true)
      
      await apiRequest(`${API_CONFIG.ENDPOINTS.HISTORY}/${diagnosis.id}`, {
        method: 'DELETE'
      })
      
      // Redirect to history page after successful deletion
      router.push('/history')
      
    } catch (err) {
      console.error('Error deleting diagnosis:', err)
      alert('Failed to delete diagnosis. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b bg-card">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <FileVideo className="h-4 w-4 text-primary-foreground" />
                </div>
                <h1 className="text-xl font-semibold text-foreground">Summary Details</h1>
              </div>
              <Button 
                variant="ghost" 
                onClick={() => router.push("/history")}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-12">
          <div className="max-w-4xl mx-auto">
            <Card>
              <CardHeader>
                <div className="animate-pulse space-y-4">
                  <div className="h-8 bg-muted rounded w-3/4"></div>
                  <div className="flex gap-2">
                    <div className="h-6 bg-muted rounded w-20"></div>
                    <div className="h-6 bg-muted rounded w-24"></div>
                    <div className="h-6 bg-muted rounded w-28"></div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="animate-pulse space-y-6">
                  <div className="space-y-3">
                    <div className="h-6 bg-muted rounded w-32"></div>
                    <div className="space-y-2">
                      <div className="h-4 bg-muted rounded w-full"></div>
                      <div className="h-4 bg-muted rounded w-full"></div>
                      <div className="h-4 bg-muted rounded w-3/4"></div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    )
  }

  if (error || !diagnosis) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b bg-card">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <FileVideo className="h-4 w-4 text-primary-foreground" />
                </div>
                <h1 className="text-xl font-semibold text-foreground">Refrigerator Diagnosis</h1>
              </div>
              <Button 
                variant="ghost" 
                onClick={() => router.push("/history")}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-12">
          <div className="max-w-4xl mx-auto">
            <Card className="border-destructive/20 bg-destructive/5">
              <CardContent className="p-8 text-center">
                <div className="text-destructive">
                  <strong>Error:</strong> {error || "Refrigerator diagnosis not found"}
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    )
  }

  // If chat is active, show full-page chat interface without any headers
  if (showChat) {
    return (
      <div className="h-screen">
        <ChatInterface 
          summaryId={diagnosis.id} 
          summaryTitle={diagnosis.fileName}
          onBack={() => setShowChat(false)}
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <FileVideo className="h-4 w-4 text-primary-foreground" />
              </div>
                              <h1 className="text-xl font-semibold text-foreground">Refrigerator Diagnosis</h1>
              </div>
              <div className="flex items-center gap-3">
                {/* Delete Button */}
                <Button 
                  onClick={handleDeleteDiagnosis}
                  disabled={isDeleting}
                  variant="outline"
                  className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200 hover:border-red-300"
                >
                  <Trash2 className="h-4 w-4" />
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </Button>
              {/* Chat Redirect Button */}
              <Button 
                onClick={() => setShowChat(true)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <MessageCircle className="h-4 w-4" />
                Open Chat
              </Button>
              <Button 
                variant="ghost" 
                onClick={() => router.push("/history")}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Refrigerator Info Card */}
          <Card>
            <CardHeader>
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileVideo className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1 space-y-4">
                  <CardTitle className="text-2xl font-bold text-foreground leading-tight">
                    {diagnosis.fileName}
                  </CardTitle>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className="flex items-center gap-1">
                      Brand: {diagnosis.brand || 'Unknown'}
                    </Badge>
                    <Badge variant="outline" className="flex items-center gap-1">
                      Model: {diagnosis.model || 'Unknown'}
                    </Badge>
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(diagnosis.createdAt)}
                    </Badge>
                    <Badge className={`${diagnosis.severityLevel === 'Simple DIY' ? 'bg-green-100 text-green-700' : 
                      diagnosis.severityLevel === 'Moderate' ? 'bg-yellow-100 text-yellow-700' : 
                      'bg-red-100 text-red-700'}`}>
                      {diagnosis.severityLevel}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground">
                    Issue Category: <span className="font-semibold text-foreground">{diagnosis.issueCategory}</span>
                  </p>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Audio Summary */}
          {diagnosis.audioSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  Audio Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose max-w-none">
                  <ReactMarkdown>{diagnosis.audioSummary}</ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Diagnosis Results */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                Diagnosis Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                <ReactMarkdown>{diagnosis.diagnosisResult}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>

          {/* Solutions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-orange-600" />
                Solutions & Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                <ReactMarkdown>{diagnosis.solutions}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}

