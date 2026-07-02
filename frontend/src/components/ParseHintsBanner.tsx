import { clientFieldLabels, type ClientFormData } from '../utils/clientFields'
import type { ClientParseResponse } from './DocxImportButton'

interface ParseHintsBannerProps {
  meta: ClientParseResponse | null
  onDismiss: () => void
}

export default function ParseHintsBanner({ meta, onDismiss }: ParseHintsBannerProps) {
  if (!meta || meta.filled.length === 0) return null

  return (
    <div className="mb-4 rounded-card border border-amber-200/80 bg-amber-50 px-4 py-3 text-sm dark:border-amber-800 dark:bg-amber-900/20">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-medium text-amber-900 dark:text-amber-200">
            Данные подставлены из Word — проверьте и исправьте при необходимости
          </p>
          <p className="mt-1 text-xs text-amber-800/90 dark:text-amber-300/90">
            Распознано:{' '}
            {meta.filled
              .map((f) => clientFieldLabels[f as keyof ClientFormData] || f)
              .join(' · ')}
          </p>
          {meta.warnings.map((w) => (
            <p key={w} className="mt-1 text-xs text-amber-700 dark:text-amber-400">
              ⚠ {w}
            </p>
          ))}
        </div>
        <button type="button" onClick={onDismiss} className="text-xs text-amber-700 hover:underline">
          Скрыть
        </button>
      </div>
    </div>
  )
}
