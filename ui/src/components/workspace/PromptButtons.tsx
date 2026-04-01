import { memo } from 'react'

interface PromptButtonsProps {
  inputIsEmpty: boolean
  isLoading: boolean
  onSendMessage: (message: string) => void
}

const QUICK_PROMPTS = [
  { label: '📋 Summarize', message: 'Summarize this conversation so far.' },
  { label: '🔍 Review Code', message: 'Review the code we have been working on and suggest improvements.' },
  { label: '🐛 Find Bugs', message: 'Look for potential bugs or issues in the current code.' },
  { label: '📝 Write Tests', message: 'Write tests for the code we have been working on.' },
]

export const PromptButtons = memo(function PromptButtons({
  inputIsEmpty,
  isLoading,
  onSendMessage,
}: PromptButtonsProps) {
  if (!inputIsEmpty || isLoading) return null

  return (
    <div className="flex flex-wrap gap-2 px-4 pb-2">
      {QUICK_PROMPTS.map((prompt) => (
        <button
          key={prompt.label}
          type="button"
          onClick={() => onSendMessage(prompt.message)}
          className="rounded-lg border-2 border-black/10 bg-white/50 px-3 py-1.5 text-xs font-medium text-gray-600 transition-all hover:border-black/20 hover:bg-white hover:text-gray-900 hover:shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-gray-400 dark:hover:border-white/20 dark:hover:bg-white/10 dark:hover:text-gray-200"
        >
          {prompt.label}
        </button>
      ))}
    </div>
  )
})
