"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ArrowLeft, Clock, Globe, FileVideo, MessageSquare } from "lucide-react"
import Link from "next/link"
import { getApiUrl, API_CONFIG } from "@/lib/config"

// Refrigerator diagnosis history page

interface RefrigeratorDiagnosis {
  id: string
  videoId: string
  fileName: string
  brand: string
  model: string
  issueCategory: string
  severityLevel: string
  diagnosisResult: string
  solutions: string
  audioSummary: string
  createdAt: string
}

interface HistoryResponse {
  diagnoses: RefrigeratorDiagnosis[]
  total: number
}

export default function HistoryPage() {
  const [diagnoses, setDiagnoses] = useState<RefrigeratorDiagnosis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.HISTORY))
        if (!response.ok) {
          throw new Error("Failed to fetch history")
        }
        const data: HistoryResponse = await response.json()
        setDiagnoses(data.diagnoses || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load history")
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }



  const truncateContent = (content: string, maxLength: number = 150) => {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength) + "..."
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
                <h1 className="text-xl font-semibold text-foreground">Video History</h1>
              </div>
              <Link 
                href="/"
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors px-4 py-2 rounded-lg hover:bg-muted"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-12">
          <div className="max-w-4xl mx-auto space-y-6">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="animate-pulse space-y-3">
                    <div className="h-6 bg-muted rounded w-3/4"></div>
                    <div className="flex gap-2">
                      <div className="h-5 bg-muted rounded w-20"></div>
                      <div className="h-5 bg-muted rounded w-24"></div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="animate-pulse space-y-2">
                    <div className="h-4 bg-muted rounded w-full"></div>
                    <div className="h-4 bg-muted rounded w-2/3"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b bg-card">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <FileVideo className="h-4 w-4 text-primary-foreground" />
                </div>
                <h1 className="text-xl font-semibold text-foreground">Video History</h1>
              </div>
              <Link 
                href="/"
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors px-4 py-2 rounded-lg hover:bg-muted"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-12">
          <div className="max-w-4xl mx-auto">
            <Card className="border-destructive/20 bg-destructive/5">
              <CardContent className="p-8 text-center">
                <div className="text-destructive">
                  <strong>Error:</strong> {error}
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
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
              <h1 className="text-xl font-semibold text-foreground">Video History</h1>
            </div>
            <Link 
              href="/"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors px-4 py-2 rounded-lg hover:bg-muted"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {diagnoses.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                  <FileVideo className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">No refrigerator diagnoses yet</h3>
                <p className="text-muted-foreground mb-6">
                  Upload your first refrigerator video to get started with AI-powered diagnosis
                </p>
                <Link href="/">
                  <Button>Upload Video</Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-foreground">Refrigerator Diagnoses</h2>
                <Badge variant="secondary">{diagnoses.length} diagnoses</Badge>
              </div>

              <div className="space-y-4">
                {diagnoses.map((diagnosis) => (
                  <Card key={diagnosis.id} className="card-interactive">
                    <CardHeader>
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <FileVideo className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1 space-y-2">
                          <CardTitle className="text-lg leading-tight">
                            {diagnosis.fileName}
                          </CardTitle>
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {diagnosis.brand || 'Unknown Brand'}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {diagnosis.model || 'Unknown Model'}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              <Clock className="h-3 w-3 mr-1" />
                              {formatDate(diagnosis.createdAt)}
                            </Badge>
                            <Badge className={`text-xs ${diagnosis.severityLevel === 'Simple DIY' ? 'bg-green-100 text-green-700' : 
                              diagnosis.severityLevel === 'Moderate' ? 'bg-yellow-100 text-yellow-700' : 
                              'bg-red-100 text-red-700'}`}>
                              {diagnosis.severityLevel}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Issue: {diagnosis.issueCategory}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          {diagnosis.audioSummary && (
                            <span className="flex items-center gap-1">
                              <MessageSquare className="h-3 w-3" />
                              Audio summary available
                            </span>
                          )}
                        </div>
                        <Link href={`/history/${diagnosis.id}`}>
                          <Button size="sm" className="interactive-button">
                            View Diagnosis
                          </Button>
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

