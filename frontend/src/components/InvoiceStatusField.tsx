import StatusBadge from './StatusBadge'
import type { PaymentRecordStatus } from '../types'
import { paymentRecordLabels } from '../utils/labels'

const OPTIONS: PaymentRecordStatus[] = ['PENDING', 'PAID', 'CANCELED']

const activeClass: Record<PaymentRecordStatus, string> = {
  PENDING:
    'bg-amber-100 text-amber-900 shadow-sm dark:bg-amber-900/50 dark:text-amber-100',
  PAID: 'bg-emerald-100 text-emerald-900 shadow-sm dark:bg-emerald-900/50 dark:text-emerald-100',
  CANCELED: 'bg-gray-100 text-gray-700 shadow-sm dark:bg-gray-800 dark:text-gray-300',
}

type Props = {
  value: PaymentRecordStatus
  onChange?: (status: PaymentRecordStatus) => void
  disabled?: boolean
  editable?: boolean
}

export default function InvoiceStatusField({ value, onChange, disabled, editable = true }: Props) {
  if (!editable || !onChange) {
    return <StatusBadge status={value} label={paymentRecordLabels[value]} />
  }

  return (
    <div
      className="inline-flex flex-wrap gap-0.5 rounded-xl bg-surface p-0.5 ring-1 ring-surface-border"
      role="group"
      aria-label="Статус счёта"
    >
      {OPTIONS.map((s) => (
        <button
          key={s}
          type="button"
          disabled={disabled}
          onClick={() => onChange(s)}
          className={`whitespace-nowrap rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
            value === s
              ? activeClass[s]
              : 'text-foreground-muted hover:bg-surface-elevated hover:text-foreground disabled:opacity-50'
          }`}
        >
          {paymentRecordLabels[s]}
        </button>
      ))}
    </div>
  )
}
