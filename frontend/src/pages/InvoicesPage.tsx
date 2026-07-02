import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, FileSpreadsheet, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import InvoiceStatusField from '../components/InvoiceStatusField'
import { getApiErrorMessage } from '../utils/apiError'
import { downloadInvoice } from '../utils/downloadFile'
import type { Contract, Invoice, InvoiceKind, PaymentRecordStatus } from '../types'
import { invoiceKindLabels } from '../utils/labels'
import { todayInputDate } from '../utils/contractForm'

export default function InvoicesPage() {
  const [modalOpen, setModalOpen] = useState(false)
  const [contractId, setContractId] = useState('')
  const [kind, setKind] = useState<InvoiceKind>('ADVANCE')
  const [invoiceDate, setInvoiceDate] = useState(todayInputDate())
  const qc = useQueryClient()

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: async () => (await api.get<Invoice[]>('/invoices')).data,
  })

  const { data: contractsData } = useQuery({
    queryKey: ['contracts-addendums'],
    queryFn: async () => {
      const data = (await api.get<{ items: Contract[] }>('/contracts', { params: { limit: 500 } })).data
      return { items: data.items.filter((c) => c.kind === 'ADDENDUM') }
    },
  })
  const addendums = contractsData?.items ?? []

  const selected = addendums.find((c) => String(c.id) === contractId)
  const advance = selected?.advance_percent ?? 100
  const canAdvance = advance < 100
  const existingKinds = invoices.filter((i) => i.contract_id === Number(contractId)).map((i) => i.kind)

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: PaymentRecordStatus }) =>
      api.put(`/invoices/${id}`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['contracts'] })
      qc.invalidateQueries({ queryKey: ['contract'] })
      toast.success('Статус счёта обновлён')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось обновить статус')),
  })

  const dateMutation = useMutation({
    mutationFn: ({ id, date }: { id: number; date: string }) =>
      api.put(`/invoices/${id}`, { invoice_date: date }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Дата счёта обновлена')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось изменить дату')),
  })

  const deleteMutation = useMutation({
    mutationFn: (invoiceId: number) => api.delete(`/invoices/${invoiceId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['contracts'] })
      qc.invalidateQueries({ queryKey: ['contract'] })
      toast.success('Счёт удалён')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось удалить счёт')),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.post<Invoice>('/invoices', {
        contract_id: Number(contractId),
        kind: advance >= 100 ? 'FULL' : kind,
        invoice_date: invoiceDate,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      setModalOpen(false)
      setInvoiceDate(todayInputDate())
      toast.success('Счёт создан')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось создать счёт')),
  })

  return (
    <div>
      <PageHeader
        title="Счета"
        subtitle="Сначала счёт на аванс, затем на остаток (при оплате не 100%)"
        actions={
          <button type="button" className="btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={16} /> Создать счёт
          </button>
        }
      />

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Клиент</th>
              <th>Приложение</th>
              <th>Тип</th>
              <th>Сумма</th>
              <th className="min-w-[17rem]">Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-foreground-muted">
                  Загрузка...
                </td>
              </tr>
            ) : invoices.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-foreground-muted">
                  Счетов пока нет
                </td>
              </tr>
            ) : (
              invoices.map((inv) => (
                <tr key={inv.id}>
                  <td>
                    {inv.can_edit ? (
                      <input
                        type="date"
                        className="input w-[9.5rem]"
                        value={inv.invoice_date.slice(0, 10)}
                        disabled={dateMutation.isPending}
                        onChange={(e) => {
                          const next = e.target.value
                          if (!next || next === inv.invoice_date.slice(0, 10)) return
                          dateMutation.mutate({ id: inv.id, date: next })
                        }}
                      />
                    ) : (
                      new Date(inv.invoice_date).toLocaleDateString('ru-RU')
                    )}
                  </td>
                  <td>{inv.client_name || '—'}</td>
                  <td>
                    <Link to={`/contracts/${inv.contract_id}`} className="text-primary hover:underline">
                      {inv.contract_number}
                      {inv.addendum_number != null ? ` / доп ${inv.addendum_number}` : ''}
                    </Link>
                  </td>
                  <td>{invoiceKindLabels[inv.kind]}</td>
                  <td className="font-mono text-sm">
                    {Number(inv.amount).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ₽
                  </td>
                  <td>
                    <InvoiceStatusField
                      value={inv.status}
                      editable={!!inv.can_edit}
                      disabled={statusMutation.isPending}
                      onChange={(status) => statusMutation.mutate({ id: inv.id, status })}
                    />
                  </td>
                  <td>
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        className="text-primary hover:underline"
                        onClick={() => void downloadInvoice(inv.id)}
                      >
                        <Download size={14} className="inline" /> XLS
                      </button>
                      {inv.can_edit && (
                        <button
                          type="button"
                          className="text-red-600 hover:underline dark:text-red-400"
                          disabled={deleteMutation.isPending}
                          onClick={() => {
                            if (!window.confirm('Удалить счёт? Файл будет удалён, счёт можно создать заново.')) {
                              return
                            }
                            deleteMutation.mutate(inv.id)
                          }}
                        >
                          <Trash2 size={14} className="inline" /> Удалить
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        title="Новый счёт"
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setInvoiceDate(todayInputDate())
        }}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (!contractId) {
              toast.error('Выберите приложение')
              return
            }
            createMutation.mutate()
          }}
        >
          <label className="mb-1.5 block text-xs font-medium text-foreground-muted">Приложение</label>
          <select
            className="select-input mb-4 w-full"
            value={contractId}
            onChange={(e) => {
              setContractId(e.target.value)
              const c = addendums.find((x) => String(x.id) === e.target.value)
              const pct = c?.advance_percent ?? 100
              setKind(pct >= 100 ? 'FULL' : 'ADVANCE')
            }}
          >
            <option value="">— выберите —</option>
            {addendums.map((c) => (
              <option key={c.id} value={c.id}>
                {c.client_name || ''} — {c.contract_number}
                {c.addendum_number != null ? ` доп ${c.addendum_number}` : ''} (аванс {c.advance_percent ?? 100}%)
              </option>
            ))}
          </select>

          {canAdvance && contractId ? (
            <>
              <label className="mb-1.5 block text-xs font-medium text-foreground-muted">Тип счёта</label>
              <select
                className="select-input mb-4 w-full"
                value={kind}
                onChange={(e) => setKind(e.target.value as InvoiceKind)}
              >
                <option value="ADVANCE" disabled={existingKinds.includes('ADVANCE')}>
                  На аванс ({advance}%)
                </option>
                <option
                  value="BALANCE"
                  disabled={!existingKinds.includes('ADVANCE') || existingKinds.includes('BALANCE')}
                >
                  На остаток ({100 - advance}%){!existingKinds.includes('ADVANCE') ? ' — сначала аванс' : ''}
                </option>
              </select>
            </>
          ) : contractId ? (
            <p className="mb-4 text-sm text-foreground-muted">
              Оплата 100% — будет создан один счёт на полную сумму.
              {existingKinds.includes('FULL') ? ' (уже создан)' : ''}
            </p>
          ) : null}

          <label className="mb-4 block text-sm">
            <span className="mb-1 block text-foreground-muted">Дата счёта</span>
            <input
              type="date"
              className="input w-full max-w-xs"
              value={invoiceDate}
              onChange={(e) => setInvoiceDate(e.target.value)}
            />
          </label>

          <div className="flex justify-end gap-2 border-t border-surface-border pt-4">
            <button type="button" className="btn-ghost" onClick={() => setModalOpen(false)}>
              Отмена
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending || !contractId}>
              <FileSpreadsheet size={16} />
              {createMutation.isPending ? 'Создание…' : 'Создать'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
