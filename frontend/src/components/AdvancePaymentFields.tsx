import { formatLinePrice } from '../utils/contractLines'

interface AdvancePaymentFieldsProps {
  advancePercent: string
  onAdvancePercentChange: (value: string) => void
  totalAmount?: number
  disabled?: boolean
}

export function balancePercent(advance: number): number {
  const safe = Math.min(100, Math.max(0, advance))
  return 100 - safe
}

export default function AdvancePaymentFields({
  advancePercent,
  onAdvancePercentChange,
  totalAmount = 0,
  disabled,
}: AdvancePaymentFieldsProps) {
  const advance = Math.min(100, Math.max(0, parseInt(advancePercent, 10) || 0))
  const balance = balancePercent(advance)
  const advanceAmount = (totalAmount * advance) / 100
  const balanceAmount = (totalAmount * balance) / 100

  return (
    <div className="rounded-card border border-surface-border bg-surface-elevated/50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-foreground">Условия оплаты</h3>
      <div className="flex flex-wrap items-end gap-4">
        <div className="w-28">
          <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
            Аванс, %
          </label>
          <input
            className="input font-mono"
            type="number"
            min={1}
            max={100}
            disabled={disabled}
            value={advancePercent}
            onChange={(e) => onAdvancePercentChange(e.target.value)}
          />
        </div>
        <div className="text-sm text-foreground-muted">
          <span className="text-foreground">Сразу:</span> {advance}%
          <span className="mx-2 text-foreground-faint">·</span>
          <span className="text-foreground">После:</span> {balance}%
        </div>
      </div>
      {totalAmount > 0 && (
        <p className="mt-3 text-sm text-foreground-muted">
          {formatLinePrice(advanceAmount, true)} — аванс,{' '}
          {formatLinePrice(balanceAmount, true)} — по завершении
        </p>
      )}
    </div>
  )
}
