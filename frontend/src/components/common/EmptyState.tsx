import { Inbox } from 'lucide-react'

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
      <Inbox className="h-10 w-10 text-navy-500" />
      <p className="text-sm font-semibold text-navy-300">{title}</p>
      {hint && <p className="max-w-sm text-xs text-navy-400">{hint}</p>}
    </div>
  )
}
