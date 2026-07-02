import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, FilePlus, Upload } from 'lucide-react'
import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../api/client'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { downloadAct, downloadDocument, downloadInvoice } from '../utils/downloadFile'
import type { Contract, Document, DocumentType, Invoice } from '../types'
import { documentTypeLabels, invoiceKindLabels, paymentRecordLabels } from '../utils/labels'

type ArchiveRow =
  | { source: 'document'; item: Document }
  | { source: 'invoice'; item: Invoice }

export default function DocumentsPage() {
  const [contractFilter, setContractFilter] = useState('')
  const [genModal, setGenModal] = useState(false)
  const [uploadModal, setUploadModal] = useState(false)
  const [genForm, setGenForm] = useState({ contract_id: '', document_type: 'CONTRACT' as DocumentType })
  const [uploadForm, setUploadForm] = useState({ contract_id: '', document_type: 'SCAN' as DocumentType })
  const fileRef = useRef<HTMLInputElement>(null)
  const qc = useQueryClient()

  const { data: documents = [], isLoading: docsLoading } = useQuery({
    queryKey: ['documents', contractFilter],
    queryFn: async () =>
      (await api.get<Document[]>('/documents', { params: contractFilter ? { contract_id: contractFilter } : {} })).data,
  })

  const { data: invoices = [], isLoading: invLoading } = useQuery({
    queryKey: ['invoices', contractFilter],
    queryFn: async () =>
      (await api.get<Invoice[]>('/invoices', { params: contractFilter ? { contract_id: contractFilter } : {} })).data,
  })

  const isLoading = docsLoading || invLoading

  const rows: ArchiveRow[] = [
    ...documents.map((item) => ({ source: 'document' as const, item })),
    ...invoices.map((item) => ({ source: 'invoice' as const, item })),
  ].sort((a, b) => {
    const da = a.source === 'document' ? a.item.generated_at : a.item.created_at
    const db = b.source === 'document' ? b.item.generated_at : b.item.created_at
    return new Date(db).getTime() - new Date(da).getTime()
  })

  const { data: contractsData } = useQuery({
    queryKey: ['contracts-list'],
    queryFn: async () => (await api.get<{ items: Contract[] }>('/contracts', { params: { limit: 500 } })).data,
  })
  const contracts = contractsData?.items ?? []

  const generateMutation = useMutation({
    mutationFn: () =>
      api.post('/documents/generate', {
        contract_id: Number(genForm.contract_id),
        document_type: genForm.document_type,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['acts'] })
      setGenModal(false)
      toast.success('Документ сгенерирован')
    },
    onError: () => toast.error('Ошибка генерации'),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData()
      fd.append('contract_id', uploadForm.contract_id)
      fd.append('document_type', uploadForm.document_type)
      fd.append('file', file)
      return api.post('/documents/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['acts'] })
      setUploadModal(false)
      toast.success('Файл загружен')
    },
    onError: () => toast.error('Ошибка загрузки'),
  })


  const rowTypeLabel = (row: ArchiveRow) => {
    if (row.source === 'invoice') {
      return `Счёт (${invoiceKindLabels[row.item.kind]})`
    }
    return documentTypeLabels[row.item.type]
  }

  const rowContractLabel = (row: ArchiveRow) => {
    if (row.source === 'invoice') {
      const n = row.item.contract_number || `#${row.item.contract_id}`
      return row.item.addendum_number != null ? `${n} / доп ${row.item.addendum_number}` : n
    }
    return `#${row.item.contract_id}`
  }

  const rowDate = (row: ArchiveRow) => {
    const d = row.source === 'document' ? row.item.generated_at : row.item.created_at
    return new Date(d).toLocaleString('ru-RU')
  }

  const rowDownload = (row: ArchiveRow) => async () => {
    try {
      if (row.source === 'invoice') {
        await downloadInvoice(row.item.id)
        return
      }
      if (row.item.type === 'ACT') {
        await downloadAct(row.item.id)
        return
      }
      await downloadDocument(row.item.id)
    } catch {
      toast.error('Не удалось скачать файл')
    }
  }

  return (
    <div>
      <PageHeader
        title="Документы"
        subtitle="Договоры Word, счета XLS и акты XLSX"
        actions={
          <>
            <select
              className="select-input w-auto min-w-[160px]"
              value={contractFilter}
              onChange={(e) => setContractFilter(e.target.value)}
            >
              <option value="">Все договоры</option>
              {contracts.map((c) => (
                <option key={c.id} value={c.id}>{c.contract_number}</option>
              ))}
            </select>
            <button type="button" className="btn-primary" onClick={() => setGenModal(true)}>
              <FilePlus size={16} /> Сгенерировать
            </button>
            <button type="button" className="btn-ghost" onClick={() => setUploadModal(true)}>
              <Upload size={16} /> Загрузить
            </button>
          </>
        }
      />

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Тип</th>
              <th>Договор</th>
              <th>Дата</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5}>Загрузка...</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={5} className="text-center text-[var(--color-text-muted)]">Нет документов</td></tr>
            ) : (
              rows.map((row) => (
                <tr key={`${row.source}-${row.item.id}`}>
                  <td>{row.item.id}</td>
                  <td>
                    {rowTypeLabel(row)}
                    {row.source === 'invoice' && (
                      <span className="ml-2 text-xs text-foreground-muted">
                        {paymentRecordLabels[row.item.status]}
                      </span>
                    )}
                  </td>
                  <td>{rowContractLabel(row)}</td>
                  <td>{rowDate(row)}</td>
                  <td>
                    <button
                      type="button"
                      className="text-primary hover:underline"
                      onClick={rowDownload(row)}
                    >
                      <Download size={14} className="inline" /> Скачать
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal title="Генерация документа" open={genModal} onClose={() => setGenModal(false)}>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault()
            generateMutation.mutate()
          }}
        >
          <select className="input" value={genForm.contract_id} onChange={(e) => setGenForm({ ...genForm, contract_id: e.target.value })} required>
            <option value="">Договор</option>
            {contracts.map((c) => (
              <option key={c.id} value={c.id}>{c.contract_number}</option>
            ))}
          </select>
          <select className="input" value={genForm.document_type} onChange={(e) => setGenForm({ ...genForm, document_type: e.target.value as DocumentType })}>
            {(['CONTRACT', 'INVOICE', 'ACT'] as DocumentType[]).map((t) => (
              <option key={t} value={t}>{documentTypeLabels[t]}</option>
            ))}
          </select>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setGenModal(false)}>Отмена</button>
            <button type="submit" className="btn-primary">Сгенерировать</button>
          </div>
        </form>
      </Modal>

      <Modal title="Загрузка файла" open={uploadModal} onClose={() => setUploadModal(false)}>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault()
            const file = fileRef.current?.files?.[0]
            if (file) uploadMutation.mutate(file)
          }}
        >
          <select className="input" value={uploadForm.contract_id} onChange={(e) => setUploadForm({ ...uploadForm, contract_id: e.target.value })} required>
            <option value="">Договор</option>
            {contracts.map((c) => (
              <option key={c.id} value={c.id}>{c.contract_number}</option>
            ))}
          </select>
          <select className="input" value={uploadForm.document_type} onChange={(e) => setUploadForm({ ...uploadForm, document_type: e.target.value as DocumentType })}>
            {Object.entries(documentTypeLabels).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <input ref={fileRef} type="file" className="input" required />
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setUploadModal(false)}>Отмена</button>
            <button type="submit" className="btn-primary">Загрузить</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
