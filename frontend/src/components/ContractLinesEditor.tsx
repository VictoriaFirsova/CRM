import { Plus, Trash2 } from 'lucide-react'
import { documentPresets } from '../utils/documentPresets'
import { emptyLineItem, formatLinePrice, sumLineItems, type LineItemDraft } from '../utils/contractLines'

interface ContractLinesEditorProps {
  lines: LineItemDraft[]
  onChange: (lines: LineItemDraft[]) => void
  disabled?: boolean
  workDays?: string
  onWorkDaysChange?: (value: string) => void
}

export default function ContractLinesEditor({
  lines,
  onChange,
  disabled,
  workDays,
  onWorkDaysChange,
}: ContractLinesEditorProps) {
  const total = sumLineItems(lines)

  const updateLine = (index: number, patch: Partial<LineItemDraft>) => {
    onChange(lines.map((line, i) => (i === index ? { ...line, ...patch } : line)))
  }

  const addLine = (presetDocument?: string) => {
    onChange([...lines, { ...emptyLineItem(), document_name: presetDocument ?? '' }])
  }

  const removeLine = (index: number) => {
    if (lines.length <= 1) {
      onChange([emptyLineItem()])
      return
    }
    onChange(lines.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-foreground-muted">
        1. Исполнитель оказывает услуги Заказчику по подготовке необходимой документации для
        оформления.
      </p>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-foreground">Таблица №1</h3>
        {!disabled && (
          <button type="button" className="btn-ghost text-xs" onClick={() => addLine()}>
            <Plus size={14} /> Строка
          </button>
        )}
      </div>

      {!disabled && (
        <div className="flex flex-wrap gap-1.5">
          {documentPresets.map((preset) => (
            <button
              key={preset.label}
              type="button"
              title={preset.document_name}
              className="rounded-pill bg-surface-border px-2.5 py-1 text-xs text-foreground-muted hover:bg-primary-light hover:text-foreground"
              onClick={() => addLine(preset.document_name)}
            >
              + {preset.label}
            </button>
          ))}
        </div>
      )}

      <div className="contract-lines-wrap">
        <table className="data-table w-full text-sm">
          <colgroup>
            <col style={{ width: '40%' }} />
            <col style={{ width: '32%' }} />
            <col style={{ width: '22%' }} />
            <col style={{ width: '2.5rem' }} />
          </colgroup>
          <thead>
            <tr>
              <th>Наименование документа</th>
              <th>Продукция</th>
              <th>Стоимость</th>
              <th aria-label="Действия" />
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => (
              <tr key={index}>
                <td>
                  <textarea
                    className="input min-h-[52px] w-full resize-y"
                    disabled={disabled}
                    rows={2}
                    value={line.document_name}
                    onChange={(e) => updateLine(index, { document_name: e.target.value })}
                    placeholder="Добровольный сертификат…"
                  />
                </td>
                <td>
                  <textarea
                    className="input min-h-[52px] w-full resize-y"
                    disabled={disabled}
                    rows={2}
                    value={line.product_name}
                    onChange={(e) => updateLine(index, { product_name: e.target.value })}
                    placeholder="Продукция"
                  />
                </td>
                <td>
                  <input
                    className="input w-full font-mono"
                    type="number"
                    min={0}
                    step="1"
                    disabled={disabled}
                    value={line.price}
                    onChange={(e) => updateLine(index, { price: e.target.value })}
                    placeholder="0"
                  />
                  <label className="mt-1.5 flex items-center gap-1.5 text-[11px] leading-tight text-foreground-muted">
                    <input
                      type="checkbox"
                      className="shrink-0"
                      disabled={disabled}
                      checked={line.vat_exempt}
                      onChange={(e) => updateLine(index, { vat_exempt: e.target.checked })}
                    />
                    <span>без НДС</span>
                  </label>
                </td>
                <td className="!px-1">
                  {!disabled && (
                    <button
                      type="button"
                      className="btn-icon h-7 w-7 text-foreground-muted hover:text-red-600"
                      onClick={() => removeLine(index)}
                      aria-label="Удалить строку"
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-4 border-t border-surface-border pt-3">
        {onWorkDaysChange && (
          <div className="w-36">
            <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
              Срок, раб. дней
            </label>
            <input
              className="input"
              type="number"
              min={1}
              disabled={disabled}
              value={workDays ?? ''}
              onChange={(e) => onWorkDaysChange(e.target.value)}
              placeholder="30"
            />
          </div>
        )}
        <p className="text-sm font-medium text-foreground">
          Итого:{' '}
          <span className="font-mono text-primary">{formatLinePrice(total, true)}</span>
        </p>
      </div>
    </div>
  )
}
