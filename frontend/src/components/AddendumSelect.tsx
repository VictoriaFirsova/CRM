import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { Contract } from '../types'
import { productionStatusLabels } from '../utils/labels'

export function formatAddendumOption(c: Contract): string {
  const add = c.addendum_number != null ? ` доп ${c.addendum_number}` : ''
  return `${c.client_name || '—'} — ${c.contract_number}${add}`
}

function addendumHaystack(c: Contract): string {
  return [
    c.client_name,
    c.contract_number,
    c.parent_contract_number,
    c.display_label,
    c.title,
    c.addendum_number != null ? String(c.addendum_number) : '',
    c.addendum_number != null ? `доп ${c.addendum_number}` : '',
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

type Props = {
  addendums: Contract[]
  value: string
  onChange: (contractId: string) => void
  /** ID приложений, для которых акт уже создан */
  withActIds?: Set<number>
}

export default function AddendumSelect({ addendums, value, onChange, withActIds }: Props) {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return addendums
    return addendums.filter((c) => addendumHaystack(c).includes(q))
  }, [addendums, search])

  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-foreground-muted">Приложение</label>
      <div className="relative mb-2">
        <Search
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-foreground-faint"
        />
        <input
          type="search"
          className="input pl-9"
          placeholder="Поиск: клиент, номер, приложение…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div
        className="mb-1 max-h-56 overflow-y-auto rounded-xl border border-surface-border bg-surface"
        role="listbox"
        aria-label="Список приложений"
      >
        {filtered.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-foreground-muted">Ничего не найдено</p>
        ) : (
          filtered.map((c) => {
            const selected = String(c.id) === value
            const hasAct = withActIds?.has(c.id)
            return (
              <button
                key={c.id}
                type="button"
                role="option"
                aria-selected={selected}
                onClick={() => onChange(String(c.id))}
                className={`flex w-full items-start justify-between gap-3 border-b border-surface-border px-4 py-3 text-left text-sm transition-colors last:border-b-0 ${
                  selected
                    ? 'bg-primary-light text-foreground'
                    : 'hover:bg-primary-light/40'
                }`}
              >
                <span className="min-w-0">
                  <span className="block font-medium">{formatAddendumOption(c)}</span>
                  {c.title ? (
                    <span className="mt-0.5 block truncate text-xs text-foreground-muted">{c.title}</span>
                  ) : null}
                </span>
                <span className="shrink-0 text-right text-xs text-foreground-muted">
                  {productionStatusLabels[c.production_status]}
                  {hasAct ? (
                    <span className="mt-0.5 block text-amber-700 dark:text-amber-400">акт есть</span>
                  ) : null}
                </span>
              </button>
            )
          })
        )}
      </div>
      <p className="text-xs text-foreground-faint">
        {filtered.length} из {addendums.length} приложений
      </p>
    </div>
  )
}
