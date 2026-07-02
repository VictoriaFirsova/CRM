const colors: Record<string, string> = {
  OPEN: 'bg-sky-50 text-sky-700 ring-1 ring-sky-200/80 dark:bg-sky-900/30 dark:text-sky-300 dark:ring-sky-800',
  CLOSED: 'bg-gray-100 text-gray-600 ring-1 ring-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:ring-gray-700',
  NOT_PAID: 'bg-red-50 text-red-700 ring-1 ring-red-200/80 dark:bg-red-900/30 dark:text-red-300',
  PARTIALLY_PAID: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200/80 dark:bg-amber-900/30 dark:text-amber-300',
  PAID: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200/80 dark:bg-emerald-900/30 dark:text-emerald-300',
  REQUEST: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-300',
  LAYOUT: 'bg-violet-50 text-violet-700 ring-1 ring-violet-200/80 dark:bg-violet-900/30 dark:text-violet-300',
  SCAN: 'bg-cyan-50 text-cyan-700 ring-1 ring-cyan-200/80 dark:bg-cyan-900/30 dark:text-cyan-300',
  READY: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200/80 dark:bg-emerald-900/30 dark:text-emerald-300',
  PENDING: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200/80',
  CANCELED: 'bg-gray-100 text-gray-500 ring-1 ring-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:ring-gray-700',
}

export default function StatusBadge({ status, label }: { status: string; label: string }) {
  return (
    <span
      className={`inline-flex rounded-pill px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${
        colors[status] || 'bg-gray-100 text-gray-600'
      }`}
    >
      {label}
    </span>
  )
}
