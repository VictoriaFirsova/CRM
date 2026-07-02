import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Download, FileSpreadsheet, FileCheck, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../api/client'
import AdvancePaymentFields from '../components/AdvancePaymentFields'
import ContractLinesEditor from '../components/ContractLinesEditor'
import InvoiceStatusField from '../components/InvoiceStatusField'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import {
  lineItemsFromContract,
  linesToPayload,
  sumLineItems,
  type LineItemDraft,
} from '../utils/contractLines'
import type {
  Act,
  Contract,
  ContractStatus,
  Invoice,
  InvoiceKind,
  PaymentRecordStatus,
  PaymentStatus,
  ProductionStatus,
} from '../types'
import { contractKindLabels, todayInputDate } from '../utils/contractForm'
import { downloadAct, downloadContractDocx, downloadInvoice } from '../utils/downloadFile'
import { getApiErrorMessage } from '../utils/apiError'
import {
  contractStatusLabels,
  invoiceKindLabels,
  paymentStatusLabels,
  productionStatusLabels,
} from '../utils/labels'

export default function ContractDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: contract, isLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: async () => (await api.get<Contract>(`/contracts/${id}`)).data,
  })

  const { data: contractInvoices = [] } = useQuery({
    queryKey: ['invoices', id],
    queryFn: async () => (await api.get<Invoice[]>(`/invoices`, { params: { contract_id: id } })).data,
    enabled: !!id,
  })

  const [lineItems, setLineItems] = useState<LineItemDraft[]>([])
  const [workDays, setWorkDays] = useState('')
  const [advancePercent, setAdvancePercent] = useState('100')
  const [downloading, setDownloading] = useState(false)
  const [actLoading, setActLoading] = useState(false)
  const [actDate, setActDate] = useState(todayInputDate())
  const [invoiceDate, setInvoiceDate] = useState(todayInputDate())

  const { data: contractActs = [] } = useQuery({
    queryKey: ['acts', id],
    queryFn: async () =>
      (await api.get<Act[]>('/acts', { params: { contract_id: id } })).data,
    enabled: !!id,
  })
  const act = contractActs[0]

  useEffect(() => {
    if (act?.act_date) {
      setActDate(act.act_date.slice(0, 10))
    }
  }, [act?.act_date])

  useEffect(() => {
    if (contract?.start_date) {
      setInvoiceDate(contract.start_date.slice(0, 10))
    }
  }, [contract?.start_date])

  useEffect(() => {
    if (!contract || contract.kind !== 'ADDENDUM') return
    setLineItems(lineItemsFromContract(contract.line_items))
    setWorkDays(contract.work_days ? String(contract.work_days) : '')
    setAdvancePercent(
      contract.advance_percent != null ? String(contract.advance_percent) : '100',
    )
  }, [contract])

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Contract>) => api.put(`/contracts/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contract', id] })
      qc.invalidateQueries({ queryKey: ['contracts'] })
      toast.success('Обновлено')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Ошибка')
    },
  })

  const invoiceMutation = useMutation({
    mutationFn: (kind: InvoiceKind) =>
      api.post<Invoice>('/invoices', {
        contract_id: Number(id),
        kind,
        invoice_date: invoiceDate,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices', id] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      toast.success('Счёт создан')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось создать счёт')),
  })

  const actDeleteMutation = useMutation({
    mutationFn: (actId: number) => api.delete(`/acts/${actId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['acts', id] })
      qc.invalidateQueries({ queryKey: ['acts'] })
      qc.invalidateQueries({ queryKey: ['documents', id] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Акт удалён')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось удалить акт')),
  })

  const actMutation = useMutation({
    mutationFn: () => api.post<Act>(`/contracts/${id}/generate-act`, { act_date: actDate }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['acts', id] })
      qc.invalidateQueries({ queryKey: ['acts'] })
      qc.invalidateQueries({ queryKey: ['documents', id] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Акт сформирован')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось сформировать акт')),
  })

  const actDateMutation = useMutation({
    mutationFn: (date: string) => api.put<Act>(`/acts/${act!.id}`, { act_date: date }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['acts', id] })
      qc.invalidateQueries({ queryKey: ['acts'] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Дата акта обновлена')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось изменить дату')),
  })

  const invoiceDeleteMutation = useMutation({
    mutationFn: (invoiceId: number) => api.delete(`/invoices/${invoiceId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices', id] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['contract', id] })
      qc.invalidateQueries({ queryKey: ['contracts'] })
      toast.success('Счёт удалён')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось удалить счёт')),
  })

  const invoiceStatusMutation = useMutation({
    mutationFn: ({ invoiceId, status }: { invoiceId: number; status: PaymentRecordStatus }) =>
      api.put(`/invoices/${invoiceId}`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices', id] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['contract', id] })
      qc.invalidateQueries({ queryKey: ['contracts'] })
      toast.success('Статус счёта обновлён')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось обновить статус')),
  })

  const invoiceDateMutation = useMutation({
    mutationFn: ({ invoiceId, date }: { invoiceId: number; date: string }) =>
      api.put(`/invoices/${invoiceId}`, { invoice_date: date }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices', id] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Дата счёта обновлена')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось изменить дату')),
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/contracts/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contracts'] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['acts'] })
      toast.success('Договор удалён')
      navigate('/contracts')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось удалить договор')),
  })

  if (isLoading || !contract) return <div className="py-12 text-center text-foreground-muted">Загрузка...</div>

  const canEdit = contract.can_edit
  const isFramework = contract.kind === 'FRAMEWORK'

  const handleDelete = () => {
    const label = contract.display_label || contract.contract_number
    const extra = isFramework
      ? '\n\nСначала должны быть удалены все приложения к этой рамке.'
      : '\n\nБудут удалены счета, акты и связанные файлы.'
    if (!window.confirm(`Удалить «${label}»?${extra}\n\nДействие необратимо.`)) {
      return
    }
    deleteMutation.mutate()
  }

  const StatusPills = <T extends string>({
    options,
    labels,
    current,
    field,
  }: {
    options: T[]
    labels: Record<T, string>
    current: T
    field: keyof Contract
  }) => (
    <div className="flex flex-wrap gap-2">
      {options.map((s) => (
        <button
          key={s}
          type="button"
          disabled={!canEdit}
          onClick={() => updateMutation.mutate({ [field]: s } as Partial<Contract>)}
          className={current === s ? 'pill-active' : 'pill-inactive disabled:opacity-50'}
        >
          {labels[s]}
        </button>
      ))}
    </div>
  )

  return (
    <div>
      <Link
        to="/contracts"
        className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
      >
        <ArrowLeft size={16} /> К списку договоров
      </Link>

      <PageHeader
        title={contract.title}
        subtitle={`${contract.display_label || contract.contract_number} · ${contractKindLabels[contract.kind]} · ${contract.client_name}${!canEdit ? ' · только просмотр' : ''}`}
        actions={
          canEdit ? (
            <>
              <button
                type="button"
                className="btn-ghost text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/40"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                <Trash2 size={16} />
                {deleteMutation.isPending ? 'Удаление…' : 'Удалить'}
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={downloading}
                onClick={async () => {
                  if (contract.kind === 'ADDENDUM' && !contract.line_items?.length) {
                    toast.error('Сначала заполните таблицу №1 и нажмите «Сохранить»')
                    return
                  }
                  setDownloading(true)
                  try {
                    await downloadContractDocx(contract.id)
                    toast.success('Файл Word загружен')
                  } catch (err) {
                    toast.error(getApiErrorMessage(err, 'Не удалось сформировать Word'))
                  } finally {
                    setDownloading(false)
                  }
                }}
              >
                <Download size={16} />
                {downloading ? 'Формирование…' : 'Скачать Word'}
              </button>
            </>
          ) : (
            <button
              type="button"
              className="btn-primary"
              disabled={downloading}
              onClick={async () => {
                if (contract.kind === 'ADDENDUM' && !contract.line_items?.length) {
                  toast.error('Сначала заполните таблицу №1 и нажмите «Сохранить»')
                  return
                }
                setDownloading(true)
                try {
                  await downloadContractDocx(contract.id)
                  toast.success('Файл Word загружен')
                } catch (err) {
                  toast.error(getApiErrorMessage(err, 'Не удалось сформировать Word'))
                } finally {
                  setDownloading(false)
                }
              }}
            >
              <Download size={16} />
              {downloading ? 'Формирование…' : 'Скачать Word'}
            </button>
          )
        }
      />

      {isFramework ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="card">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
              Статус рамки
            </h2>
            {StatusPills({
              options: Object.keys(contractStatusLabels) as ContractStatus[],
              labels: contractStatusLabels,
              current: contract.contract_status,
              field: 'contract_status',
            })}
            {contract.contract_status === 'CLOSED' && (
              <p className="mt-3 text-sm text-foreground-muted">
                К закрытой рамке нельзя добавить новые приложения.
              </p>
            )}
          </div>
          <div className="card">
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
              Комментарий
            </h2>
            <textarea
              className="input min-h-[120px]"
              disabled={!canEdit}
              defaultValue={contract.comment || ''}
              onBlur={(e) => canEdit && updateMutation.mutate({ comment: e.target.value })}
            />
          </div>
        </div>
      ) : (
        <>
          <div className="card mb-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-foreground-faint">
                Таблица №1 (документ · продукция · стоимость работы)
              </h2>
              {canEdit && (
                <button
                  type="button"
                  className="btn-primary text-sm"
                  disabled={updateMutation.isPending}
                  onClick={() => {
                    const payload = linesToPayload(lineItems)
                    if (payload.length === 0) {
                      toast.error('Заполните хотя бы одну строку таблицы')
                      return
                    }
                    updateMutation.mutate({
                      line_items: payload,
                      work_days: workDays ? Number(workDays) : null,
                      advance_percent: Number(advancePercent) || 100,
                    } as Partial<Contract>)
                  }}
                >
                  Сохранить
                </button>
              )}
            </div>
            <div className="mb-4">
              <AdvancePaymentFields
                advancePercent={advancePercent}
                onAdvancePercentChange={setAdvancePercent}
                totalAmount={
                  contract.amount ? Number(contract.amount) : sumLineItems(lineItems)
                }
                disabled={!canEdit}
              />
            </div>
            <ContractLinesEditor
              lines={lineItems}
              onChange={setLineItems}
              disabled={!canEdit}
              workDays={workDays}
              onWorkDaysChange={setWorkDays}
            />
          </div>

          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <div className="kpi-card">
              <span className="kpi-label">Сумма договора</span>
              <p className="kpi-value">{Number(contract.amount).toLocaleString('ru-RU')} ₽</p>
              {contract.advance_percent != null && contract.advance_percent < 100 && (
                <p className="mt-1 text-xs text-foreground-muted">
                  Аванс {contract.advance_percent}% / после {100 - contract.advance_percent}%
                </p>
              )}
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Статус</span>
              <div className="mt-2">
                <StatusBadge
                  status={contract.contract_status}
                  label={contractStatusLabels[contract.contract_status]}
                />
              </div>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Оплата / Этап</span>
              <div className="mt-2 flex flex-wrap gap-2">
                <StatusBadge
                  status={contract.payment_status}
                  label={paymentStatusLabels[contract.payment_status]}
                />
                <StatusBadge
                  status={contract.production_status}
                  label={productionStatusLabels[contract.production_status]}
                />
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="card">
              <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
                Комментарий
              </h2>
              <textarea
                className="input min-h-[100px]"
                disabled={!canEdit}
                defaultValue={contract.comment || ''}
                onBlur={(e) => canEdit && updateMutation.mutate({ comment: e.target.value })}
              />
            </div>

            <div className="card space-y-6">
              <div>
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
                  Статус договора
                </h2>
                {StatusPills({
                  options: Object.keys(contractStatusLabels) as ContractStatus[],
                  labels: contractStatusLabels,
                  current: contract.contract_status,
                  field: 'contract_status',
                })}
              </div>
              <div>
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
                  Оплата
                </h2>
                {StatusPills({
                  options: Object.keys(paymentStatusLabels) as PaymentStatus[],
                  labels: paymentStatusLabels,
                  current: contract.payment_status,
                  field: 'payment_status',
                })}
              </div>
              <div>
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
                  Этап работы
                </h2>
                {StatusPills({
                  options: Object.keys(productionStatusLabels) as ProductionStatus[],
                  labels: productionStatusLabels,
                  current: contract.production_status,
                  field: 'production_status',
                })}
              </div>
            </div>
          </div>

          <div className="card mt-6">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
              Акт выполненных работ
            </h2>
            <p className="mb-4 text-sm text-foreground-muted">
              Можно сформировать в любой момент (статус оплаты не важен). Нужны сохранённые строки
              таблицы №1 и сумма. Для закрытия приложения по-прежнему нужны полная оплата, этап «Готов» и акт.
            </p>
            {canEdit && !act && (
              <div className="mb-4 flex flex-wrap items-end gap-3">
                <label className="text-sm">
                  <span className="mb-1 block text-foreground-muted">Дата акта</span>
                  <input
                    type="date"
                    className="input w-full max-w-xs"
                    value={actDate}
                    onChange={(e) => setActDate(e.target.value)}
                  />
                </label>
                <button
                  type="button"
                  className="btn-primary text-sm"
                  disabled={actMutation.isPending || actLoading}
                  onClick={() => {
                    if (!contract.line_items?.length) {
                      toast.error('Сначала заполните таблицу №1 и нажмите «Сохранить»')
                      return
                    }
                    actMutation.mutate()
                  }}
                >
                  <FileCheck size={14} /> Сформировать акт
                </button>
              </div>
            )}
            {act ? (
              <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <span>Акт от</span>
                  {canEdit && act.can_edit !== false ? (
                    <input
                      type="date"
                      className="input w-[9.5rem]"
                      value={actDate}
                      disabled={actDateMutation.isPending}
                      onChange={(e) => {
                        const next = e.target.value
                        setActDate(next)
                        if (!next || next === act.act_date.slice(0, 10)) return
                        actDateMutation.mutate(next)
                      }}
                    />
                  ) : (
                    <span>{new Date(act.act_date).toLocaleDateString('ru-RU')}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={async () => {
                      setActLoading(true)
                      try {
                        await downloadAct(act.id)
                      } finally {
                        setActLoading(false)
                      }
                    }}
                  >
                    <Download size={14} className="inline" /> XLSX
                  </button>
                  {canEdit && act.can_edit !== false && (
                    <button
                      type="button"
                      className="text-red-600 hover:underline dark:text-red-400"
                      disabled={actDeleteMutation.isPending}
                      onClick={() => {
                        if (!window.confirm('Удалить акт? Можно сформировать заново с актуальным шаблоном.')) {
                          return
                        }
                        actDeleteMutation.mutate(act.id)
                      }}
                    >
                      <Trash2 size={14} className="inline" /> Удалить
                    </button>
                  )}
                </div>
              </div>
            ) : (
              !canEdit && <p className="text-sm text-foreground-muted">Акт не сформирован</p>
            )}
          </div>

          <div className="card mt-6">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
              Счета
            </h2>
            <p className="mb-4 text-sm text-foreground-muted">
              {Number(advancePercent) >= 100
                ? 'Оплата 100% — один счёт на полную сумму.'
                : 'Сначала счёт на аванс, затем на остаток.'}
            </p>
            {canEdit && (
              <div className="mb-4 flex flex-wrap items-end gap-3">
                <label className="text-sm">
                  <span className="mb-1 block text-foreground-muted">Дата счёта</span>
                  <input
                    type="date"
                    className="input w-full max-w-xs"
                    value={invoiceDate}
                    onChange={(e) => setInvoiceDate(e.target.value)}
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                {Number(advancePercent) >= 100 ? (
                  <button
                    type="button"
                    className="btn-primary text-sm"
                    disabled={
                      invoiceMutation.isPending || contractInvoices.some((i) => i.kind === 'FULL')
                    }
                    onClick={() => invoiceMutation.mutate('FULL')}
                  >
                    <FileSpreadsheet size={14} /> Счёт 100%
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      className="btn-primary text-sm"
                      disabled={
                        invoiceMutation.isPending ||
                        contractInvoices.some((i) => i.kind === 'ADVANCE')
                      }
                      onClick={() => invoiceMutation.mutate('ADVANCE')}
                    >
                      <FileSpreadsheet size={14} /> Счёт на аванс ({advancePercent}%)
                    </button>
                    <button
                      type="button"
                      className="btn-ghost text-sm"
                      disabled={
                        invoiceMutation.isPending ||
                        !contractInvoices.some((i) => i.kind === 'ADVANCE') ||
                        contractInvoices.some((i) => i.kind === 'BALANCE')
                      }
                      onClick={() => invoiceMutation.mutate('BALANCE')}
                    >
                      <FileSpreadsheet size={14} /> Счёт на остаток ({100 - Number(advancePercent)}%)
                    </button>
                  </>
                )}
                </div>
              </div>
            )}
            {contractInvoices.length > 0 ? (
              <ul className="space-y-2 text-sm">
                {contractInvoices.map((inv) => (
                  <li key={inv.id} className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span>
                        {invoiceKindLabels[inv.kind]} —{' '}
                        {Number(inv.amount).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ₽
                      </span>
                      {canEdit && inv.can_edit !== false ? (
                        <input
                          type="date"
                          className="input w-[9.5rem]"
                          value={inv.invoice_date.slice(0, 10)}
                          disabled={invoiceDateMutation.isPending}
                          onChange={(e) => {
                            const next = e.target.value
                            if (!next || next === inv.invoice_date.slice(0, 10)) return
                            invoiceDateMutation.mutate({ invoiceId: inv.id, date: next })
                          }}
                        />
                      ) : (
                        <span className="text-foreground-muted">
                          от {new Date(inv.invoice_date).toLocaleDateString('ru-RU')}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <InvoiceStatusField
                        value={inv.status}
                        editable={canEdit && inv.can_edit !== false}
                        disabled={invoiceStatusMutation.isPending}
                        onChange={(status) =>
                          invoiceStatusMutation.mutate({ invoiceId: inv.id, status })
                        }
                      />
                      <button
                        type="button"
                        className="text-primary hover:underline"
                        onClick={() => void downloadInvoice(inv.id)}
                      >
                        <Download size={14} className="inline" /> XLS
                      </button>
                      {canEdit && inv.can_edit !== false && (
                        <button
                          type="button"
                          className="text-red-600 hover:underline dark:text-red-400"
                          disabled={invoiceDeleteMutation.isPending}
                          onClick={() => {
                            if (!window.confirm('Удалить счёт? Можно будет создать заново с актуальным шаблоном.')) {
                              return
                            }
                            invoiceDeleteMutation.mutate(inv.id)
                          }}
                        >
                          <Trash2 size={14} className="inline" />
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-foreground-muted">Счетов пока нет</p>
            )}
          </div>

          <p className="mt-6 rounded-card bg-primary-light/50 px-4 py-3 text-xs text-foreground-muted">
            Закрытие приложения возможно только при полной оплате, этапе Готов и наличии акта
            выполненных работ
          </p>
        </>
      )}
    </div>
  )
}
