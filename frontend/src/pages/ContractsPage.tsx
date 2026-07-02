import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Plus, RotateCcw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../api/client'
import AdvancePaymentFields from '../components/AdvancePaymentFields'
import ContractLinesEditor from '../components/ContractLinesEditor'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../utils/apiError'
import {
  contractKindLabels,
  defaultAddendumTitle,
  frameworkNumberExample,
  todayInputDate,
} from '../utils/contractForm'
import { emptyLineItem, linesToPayload, sumLineItems, type LineItemDraft } from '../utils/contractLines'
import type { Client, Contract, ContractKind, ContractStatus, PaymentStatus, ProductionStatus } from '../types'
import {
  contractStatusLabels,
  paymentStatusLabels,
  productionStatusLabels,
} from '../utils/labels'

interface DuplicateCheck {
  exists: boolean
  message?: string
}

const emptyForm = () => ({
  kind: 'FRAMEWORK' as ContractKind,
  client_id: '',
  parent_contract_id: '',
  contract_number: '',
  addendum_number: '',
  start_date: todayInputDate(),
  title: '',
  work_days: '',
  advance_percent: '100',
  line_items: [emptyLineItem()] as LineItemDraft[],
  comment: '',
})

export default function ContractsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm())
  const [numberWarning, setNumberWarning] = useState<DuplicateCheck | null>(null)
  const [numberHint, setNumberHint] = useState<{ prefix: string; managerName?: string } | null>(null)
  const [numberLoading, setNumberLoading] = useState(false)
  const qc = useQueryClient()

  const filters = {
    contract_status: searchParams.get('contract_status') as ContractStatus | null,
    payment_status: searchParams.get('payment_status') as PaymentStatus | null,
    production_status: searchParams.get('production_status') as ProductionStatus | null,
    search: searchParams.get('search') || '',
    client_id: searchParams.get('client_id') || '',
    contract_number: searchParams.get('contract_number') || '',
  }

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next)
  }

  const resetFilters = () => setSearchParams({})

  const { data, isLoading } = useQuery({
    queryKey: ['contracts', Object.fromEntries(searchParams)],
    queryFn: async () => {
      const params: Record<string, string> = {}
      Object.entries(filters).forEach(([k, v]) => {
        if (v) params[k] = v
      })
      return (await api.get<{ items: Contract[]; total: number }>('/contracts', { params })).data
    },
  })

  const { data: clients = [] } = useQuery({
    queryKey: ['clients-list'],
    queryFn: async () => (await api.get<Client[]>('/clients')).data,
  })

  const { data: frameworks = [], isFetching: frameworksLoading } = useQuery({
    queryKey: ['contract-frameworks', form.client_id],
    queryFn: async () =>
      (
        await api.get<Contract[]>('/contracts/frameworks', {
          params: { client_id: form.client_id },
        })
      ).data,
    enabled: modalOpen && form.kind === 'ADDENDUM' && !!form.client_id,
  })

  const loadFrameworkNumber = useCallback(async () => {
    setNumberLoading(true)
    try {
      const { data } = await api.get<{
        suggested: string
        prefix: string
        manager_name?: string
      }>('/contracts/suggest-number')
      setForm((f) => ({ ...f, contract_number: data.suggested }))
      setNumberHint({ prefix: data.prefix, managerName: data.manager_name })
      setNumberWarning(null)
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Не удалось получить номер'))
    } finally {
      setNumberLoading(false)
    }
  }, [])

  const loadAddendumNumber = async (parentId: string) => {
    if (!parentId) return
    try {
      const { data } = await api.get<{ suggested: number; parent_contract_number: string }>(
        '/contracts/suggest-addendum',
        { params: { parent_contract_id: parentId } },
      )
      setForm((f) => ({
        ...f,
        addendum_number: String(data.suggested),
        title: f.title || defaultAddendumTitle(data.suggested),
      }))
      setNumberWarning(null)
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Не удалось получить номер приложения'))
    }
  }

  useEffect(() => {
    if (!modalOpen || form.kind !== 'FRAMEWORK') return
    void loadFrameworkNumber()
  }, [modalOpen, form.kind, loadFrameworkNumber])

  useEffect(() => {
    if (form.kind === 'ADDENDUM' && form.parent_contract_id) {
      void loadAddendumNumber(form.parent_contract_id)
    }
  }, [form.kind, form.parent_contract_id])

  const frameworkNumberLabel =
    form.contract_number.trim() ||
    (numberHint ? frameworkNumberExample(numberHint.prefix) : 'ФВ-000-2026')

  const checkDuplicate = async () => {
    if (form.kind === 'FRAMEWORK' && form.contract_number.trim()) {
      const { data } = await api.get<DuplicateCheck>('/contracts/check-number', {
        params: { contract_number: form.contract_number.trim() },
      })
      setNumberWarning(data.exists ? data : null)
      return data.exists
    }
    if (form.kind === 'ADDENDUM' && form.parent_contract_id && form.addendum_number) {
      const { data } = await api.get<DuplicateCheck>('/contracts/check-addendum', {
        params: {
          parent_contract_id: form.parent_contract_id,
          addendum_number: form.addendum_number,
        },
      })
      setNumberWarning(data.exists ? data : null)
      return data.exists
    }
    setNumberWarning(null)
    return false
  }

  const openModal = () => {
    setForm(emptyForm())
    setNumberWarning(null)
    setNumberHint(null)
    setModalOpen(true)
  }

  const createMutation = useMutation({
    mutationFn: (allowDuplicate: boolean) =>
      api.post('/contracts', {
        kind: form.kind,
        client_id: Number(form.client_id),
        parent_contract_id:
          form.kind === 'ADDENDUM' ? Number(form.parent_contract_id) : undefined,
        contract_number: form.kind === 'FRAMEWORK' ? form.contract_number.trim() : undefined,
        addendum_number:
          form.kind === 'ADDENDUM' ? Number(form.addendum_number) || undefined : undefined,
        start_date: form.start_date || todayInputDate(),
        title: form.kind === 'ADDENDUM' ? form.title : undefined,
        work_days:
          form.kind === 'ADDENDUM' && form.work_days ? Number(form.work_days) : undefined,
        advance_percent:
          form.kind === 'ADDENDUM' ? Number(form.advance_percent) || 100 : undefined,
        line_items: form.kind === 'ADDENDUM' ? linesToPayload(form.line_items) : undefined,
        comment: form.comment || null,
        allow_duplicate: allowDuplicate,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contracts'] })
      qc.invalidateQueries({ queryKey: ['contract-frameworks'] })
      setModalOpen(false)
      toast.success('Договор создан')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Ошибка создания')),
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.client_id) {
      toast.error('Выберите клиента')
      return
    }
    if (form.kind === 'FRAMEWORK' && !form.contract_number.trim()) {
      toast.error('Укажите номер рамки')
      return
    }
    if (form.kind === 'ADDENDUM' && !form.parent_contract_id) {
      toast.error('Выберите рамочный договор')
      return
    }
    if (form.kind === 'ADDENDUM' && !form.addendum_number) {
      toast.error('Укажите номер приложения')
      return
    }
    if (form.kind === 'ADDENDUM' && !form.title.trim()) {
      toast.error('Укажите название')
      return
    }
    if (form.kind === 'ADDENDUM') {
      const payloadLines = linesToPayload(form.line_items)
      if (payloadLines.length === 0) {
        toast.error('Заполните таблицу: документ, продукция и стоимость')
        return
      }
    }
    const dup = await checkDuplicate()
    if (dup && numberWarning?.message) {
      if (!window.confirm(`${numberWarning.message}\n\nВсё равно создать?`)) return
      createMutation.mutate(true)
      return
    }
    createMutation.mutate(false)
  }

  const contracts = data?.items ?? []

  return (
    <div>
      <PageHeader
        title={`Договоры${data?.total !== undefined ? ` (${data.total})` : ''}`}
        subtitle={`Добро пожаловать, ${user?.full_name ?? ''}!`}
        actions={
          <button type="button" className="btn-primary" onClick={openModal}>
            <Plus size={16} /> Новый договор
          </button>
        }
      />

      <div className="filter-panel">
        <input
          className="input"
          placeholder="Поиск..."
          value={filters.search}
          onChange={(e) => setFilter('search', e.target.value)}
        />
        <input
          className="input"
          placeholder="№ договора"
          value={filters.contract_number}
          onChange={(e) => setFilter('contract_number', e.target.value)}
        />
        <select
          className="select-input"
          value={filters.contract_status || ''}
          onChange={(e) => setFilter('contract_status', e.target.value)}
        >
          <option value="">Статус договора</option>
          {Object.entries(contractStatusLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          className="select-input"
          value={filters.payment_status || ''}
          onChange={(e) => setFilter('payment_status', e.target.value)}
        >
          <option value="">Оплата</option>
          {Object.entries(paymentStatusLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          className="select-input"
          value={filters.production_status || ''}
          onChange={(e) => setFilter('production_status', e.target.value)}
        >
          <option value="">Этап</option>
          {Object.entries(productionStatusLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          className="select-input"
          value={filters.client_id}
          onChange={(e) => setFilter('client_id', e.target.value)}
        >
          <option value="">Клиент</option>
          {clients.map((c) => (
            <option key={c.id} value={c.id}>{c.company_name}</option>
          ))}
        </select>
        <button type="button" className="btn-ghost" onClick={resetFilters}>
          <RotateCcw size={16} /> Сброс
        </button>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>№ / тип</th>
              <th>Название</th>
              <th>Клиент</th>
              <th>Сумма</th>
              <th>Статус</th>
              <th>Оплата</th>
              <th>Этап</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={7}>Загрузка...</td></tr>
            ) : contracts.length === 0 ? (
              <tr><td colSpan={7} className="py-8 text-center text-foreground-muted">Нет договоров</td></tr>
            ) : (
              contracts.map((c) => {
                const isFramework = c.kind === 'FRAMEWORK'
                return (
                  <tr
                    key={c.id}
                    className="cursor-pointer"
                    title="Двойной клик — открыть"
                    onDoubleClick={() => navigate(`/contracts/${c.id}`)}
                  >
                    <td className="font-mono text-xs">
                      <div>{c.display_label || c.contract_number}</div>
                      <div className="text-foreground-faint">{contractKindLabels[c.kind]}</div>
                    </td>
                    <td>{c.title}</td>
                    <td>{c.client_name}</td>
                    <td className="text-foreground-muted">
                      {isFramework ? '—' : `${Number(c.amount).toLocaleString('ru-RU')} ₽`}
                    </td>
                    <td>
                      <StatusBadge
                        status={c.contract_status}
                        label={contractStatusLabels[c.contract_status]}
                      />
                    </td>
                    <td className="text-foreground-muted">
                      {isFramework ? (
                        '—'
                      ) : (
                        <StatusBadge
                          status={c.payment_status}
                          label={paymentStatusLabels[c.payment_status]}
                        />
                      )}
                    </td>
                    <td className="text-foreground-muted">
                      {isFramework ? (
                        '—'
                      ) : (
                        <StatusBadge
                          status={c.production_status}
                          label={productionStatusLabels[c.production_status]}
                        />
                      )}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      <Modal title="Новый договор" open={modalOpen} onClose={() => setModalOpen(false)} wide>
        <form className="space-y-4" onSubmit={(e) => void handleSubmit(e)}>
          <div className="flex flex-wrap gap-2">
            {(['FRAMEWORK', 'ADDENDUM'] as ContractKind[]).map((k) => (
              <button
                key={k}
                type="button"
                className={form.kind === k ? 'pill-active' : 'pill-inactive'}
                onClick={() => {
                  setForm({
                    ...emptyForm(),
                    kind: k,
                    client_id: form.client_id,
                    start_date: todayInputDate(),
                  })
                  setNumberWarning(null)
                  setNumberHint(null)
                }}
              >
                {contractKindLabels[k]}
              </button>
            ))}
          </div>

          <select
            className="input"
            value={form.client_id}
            onChange={(e) =>
              setForm({
                ...form,
                client_id: e.target.value,
                parent_contract_id: '',
              })
            }
            required
          >
            <option value="">Клиент</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.company_name}</option>
            ))}
          </select>

          {form.kind === 'FRAMEWORK' ? (
            <>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
                  Номер рамки ({frameworkNumberLabel})
                </label>
                {numberHint?.managerName && (
                  <p className="mb-1.5 text-xs text-foreground-muted">
                    {numberHint.managerName} → префикс {numberHint.prefix}. Цифры XXX-ГГГГ общие для
                    всех менеджеров.
                  </p>
                )}
                <div className="flex gap-2">
                  <input
                    className="input font-mono"
                    value={form.contract_number}
                    onChange={(e) => {
                      setForm({ ...form, contract_number: e.target.value })
                      setNumberWarning(null)
                    }}
                    onBlur={() => void checkDuplicate()}
                    required
                  />
                  <button
                    type="button"
                    className="btn-ghost shrink-0"
                    disabled={numberLoading}
                    onClick={() => void loadFrameworkNumber()}
                  >
                    {numberLoading ? '…' : 'Следующий'}
                  </button>
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
                  Дата договора
                </label>
                <input
                  className="input"
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                  required
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
                  Рамочный договор
                </label>
                <select
                  className="input"
                  value={form.parent_contract_id}
                  disabled={!form.client_id}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      parent_contract_id: e.target.value,
                      addendum_number: '',
                    })
                  }
                  required
                >
                  <option value="">
                    {!form.client_id
                      ? 'Сначала выберите клиента'
                      : frameworksLoading
                        ? 'Загрузка…'
                        : frameworks.length === 0
                          ? 'Нет открытых рамок у этого клиента'
                          : 'Выберите рамку'}
                  </option>
                  {frameworks.map((fw) => (
                    <option key={fw.id} value={fw.id}>
                      {fw.display_label || fw.contract_number} — {fw.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
                  Номер приложения
                </label>
                <div className="flex gap-2">
                  <input
                    className="input font-mono"
                    type="number"
                    min={1}
                    value={form.addendum_number}
                    onChange={(e) => {
                      setForm({ ...form, addendum_number: e.target.value })
                      setNumberWarning(null)
                    }}
                    onBlur={() => void checkDuplicate()}
                    required
                  />
                  <button
                    type="button"
                    className="btn-ghost shrink-0"
                    disabled={!form.parent_contract_id}
                    onClick={() => void loadAddendumNumber(form.parent_contract_id)}
                  >
                    Следующий
                  </button>
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
                  Дата приложения
                </label>
                <input
                  className="input"
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                />
              </div>
              <input
                className="input"
                placeholder="Название"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
              />
              <AdvancePaymentFields
                advancePercent={form.advance_percent}
                onAdvancePercentChange={(advance_percent) => setForm({ ...form, advance_percent })}
                totalAmount={sumLineItems(form.line_items)}
              />
              <ContractLinesEditor
                lines={form.line_items}
                onChange={(line_items) => setForm({ ...form, line_items })}
                workDays={form.work_days}
                onWorkDaysChange={(work_days) => setForm({ ...form, work_days })}
              />
            </>
          )}

          {numberWarning?.exists && (
            <p className="rounded-lg border border-amber-500/40 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
              {numberWarning.message}
            </p>
          )}

          <textarea
            className="input"
            placeholder="Комментарий"
            value={form.comment}
            onChange={(e) => setForm({ ...form, comment: e.target.value })}
          />
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setModalOpen(false)}>
              Отмена
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              Создать
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
