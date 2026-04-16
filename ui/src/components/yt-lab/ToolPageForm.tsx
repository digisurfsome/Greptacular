import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { InputSchemaField } from '@/lib/types'

interface ToolPageFormProps {
  inputSchema: InputSchemaField[]
  onSubmit: (values: Record<string, string | number>) => void
  isLoading?: boolean
}

export default function ToolPageForm({ inputSchema, onSubmit, isLoading }: ToolPageFormProps) {
  const [values, setValues] = useState<Record<string, string | number>>(() => {
    // Initialize with defaults
    const defaults: Record<string, string | number> = {}
    for (const field of inputSchema) {
      if (field.default !== undefined) {
        defaults[field.name] = field.default
      }
    }
    return defaults
  })

  const handleChange = (name: string, value: string | number) => {
    setValues(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = () => {
    // Validate required fields
    for (const field of inputSchema) {
      if (field.required && !values[field.name] && values[field.name] !== 0) {
        return // Don't submit if required fields are missing
      }
    }
    onSubmit(values)
  }

  if (!inputSchema || inputSchema.length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        This tool has no configurable inputs.
        <div className="mt-3">
          <Button onClick={() => onSubmit({})} disabled={isLoading} size="sm">
            {isLoading ? 'Running...' : 'Run Tool'}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3 p-4">
      {inputSchema.map((field) => (
        <div key={field.name} className="space-y-1">
          <Label className="text-xs">
            {field.label}
            {field.required && <span className="text-red-400 ml-0.5">*</span>}
          </Label>

          {field.type === 'select' && field.options ? (
            <select
              value={String(values[field.name] || '')}
              onChange={(e) => handleChange(field.name, e.target.value)}
              className="w-full h-8 rounded border border-border bg-background px-2 text-sm"
            >
              <option value="">Select...</option>
              {field.options.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          ) : (
            <Input
              type={field.type === 'number' ? 'number' : field.type === 'url' ? 'url' : 'text'}
              value={String(values[field.name] || '')}
              onChange={(e) => handleChange(
                field.name,
                field.type === 'number' ? Number(e.target.value) : e.target.value
              )}
              placeholder={field.placeholder || ''}
              className="h-8 text-sm"
            />
          )}
        </div>
      ))}

      <Button onClick={handleSubmit} disabled={isLoading} className="w-full" size="sm">
        {isLoading ? 'Running...' : 'Run Tool'}
      </Button>
    </div>
  )
}
