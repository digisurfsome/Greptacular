import { FileText, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useQAReport } from '../hooks/useProjects'
import { Card, CardContent } from '@/components/ui/card'

interface QAReportPanelProps {
  projectName: string | null
}

export function QAReportPanel({ projectName }: QAReportPanelProps) {
  const { data, isLoading, isError } = useQAReport(projectName)

  if (!projectName) {
    return null
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-muted rounded w-1/3" />
            <div className="h-4 bg-muted rounded w-full" />
            <div className="h-4 bg-muted rounded w-2/3" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (isError || !data) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          <FileText size={32} className="mx-auto mb-2 opacity-50" />
          <p className="font-medium">No QA Report Yet</p>
          <p className="text-sm mt-1">
            A QA report will be generated after all features pass review.
          </p>
        </CardContent>
      </Card>
    )
  }

  const content = data.content
  const isShipIt = content.toLowerCase().includes('ship it')

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileText size={20} />
          <h3 className="font-semibold text-lg">QA Report</h3>
          {isShipIt ? (
            <span className="ml-auto inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-bold bg-green-500 text-white border-2 border-green-700">
              <CheckCircle2 size={14} />
              SHIP IT
            </span>
          ) : (
            <span className="ml-auto inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-bold bg-red-500 text-white border-2 border-red-700">
              <AlertCircle size={14} />
              NEEDS WORK
            </span>
          )}
        </div>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <pre className="whitespace-pre-wrap text-sm font-mono bg-muted/50 p-4 rounded-lg overflow-x-auto">
            {content}
          </pre>
        </div>
      </CardContent>
    </Card>
  )
}
