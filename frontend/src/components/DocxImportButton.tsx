import { useRef, useState } from 'react'
import { FileUp, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'
import { getApiErrorMessage } from '../utils/apiError'
import { clientFieldLabels, emptyClientForm, type ClientFormData } from '../utils/clientFields'

export interface ClientParseResponse {
  fields: Partial<ClientFormData>
  filled: string[]
  warnings: string[]
}

interface DocxImportButtonProps {
  /** Если передан — подставляем только в пустые поля или поверх (mergeMode) */
  currentForm?: ClientFormData
  mergeMode?: 'fill-empty' | 'overwrite'
  onImported: (form: ClientFormData, meta: ClientParseResponse) => void
  disabled?: boolean
  className?: string
}

export default function DocxImportButton({
  currentForm,
  mergeMode = 'overwrite',
  onImported,
  disabled,
  className,
}: DocxImportButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)

  const handleFile = async (file: File) => {
    const lower = file.name.toLowerCase()
    if (!lower.endsWith('.docx') && !lower.endsWith('.doc')) {
      toast.error('Выберите файл Word (.doc или .docx)')
      return
    }
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await api.post<ClientParseResponse>('/clients/parse-docx', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      const base = currentForm ?? emptyClientForm
      const merged: ClientFormData = { ...base }
      for (const key of Object.keys(emptyClientForm) as (keyof ClientFormData)[]) {
        const val = data.fields[key as keyof typeof data.fields]
        if (!val) continue
        if (mergeMode === 'fill-empty' && base[key]?.trim()) continue
        merged[key] = val
      }

      onImported(merged, data)

      const labels = data.filled
        .map((f) => clientFieldLabels[f as keyof ClientFormData] || f)
        .slice(0, 5)
      const more = data.filled.length > 5 ? ` и ещё ${data.filled.length - 5}` : ''

      if (data.filled.length === 0) {
        toast.error(data.warnings[0] || 'Ничего не распознано')
      } else {
        toast.success(`Заполнено полей: ${data.filled.length}. ${labels.join(', ')}${more}`)
        data.warnings.forEach((w) => toast(w, { icon: '⚠️' }))
      }
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Не удалось прочитать файл'))
    } finally {
      setLoading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        disabled={disabled || loading}
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) void handleFile(file)
        }}
      />
      <button
        type="button"
        className={className ?? 'btn-ghost'}
        disabled={disabled || loading}
        onClick={() => inputRef.current?.click()}
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <FileUp size={16} />}
        {loading ? 'Читаем файл...' : 'Загрузить из Word (.doc/.docx)'}
      </button>
    </>
  )
}
