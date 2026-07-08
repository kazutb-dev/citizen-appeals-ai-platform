import { Loader2 } from 'lucide-react'

export function LoadingSpinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-10 text-navy-300">
      <Loader2 className="h-5 w-5 animate-spin text-teal-400" />
      {label && <span className="text-sm font-medium">{label}</span>}
    </div>
  )
}
