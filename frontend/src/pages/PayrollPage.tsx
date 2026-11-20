import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Wallet } from 'lucide-react'
import { useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import api from '../api/client'
import PageHeader from '../components/PageHeader'
import { getApiErrorMessage } from '../utils/apiError'
import { paymentStatusLabels } from '../utils/labels'
import type { PaymentStatus } from '../types'

interface PayrollLine {
  id: number
  contract_id: number
  contract_label: string
  client_name?: string | null
  document_name: string
  product_name: string
  price: number
  cost_price?: number | null
  share_half: boolean
  salary_paid: boolean
  reward_full: number
  reward_mine: number
  payment_status: PaymentStatus
  start_date?: string | null
  year?: number | null
}

interface PayrollList {
  items: PayrollLine[]
  total_to_pay: number
  total_paid: number
  total_all: number
}

function money(n: number) {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
}

export default function PayrollPage() {
  const now = new Date()
  const [year, setYear] = useState<string>(String(now.getFullYear()))
  const [month, setMonth] = useState<string>('')
  const [hidePaid, setHidePaid] = useState(false)
  const qc = useQueryClient()

  const params = useMemo(() => {
    const p: Record<string, string | number | boolean> = {}
    if (year) p.year = Number(year)
    if (month) p.month = Number(month)
    if (hidePaid) p.hide_paid = true
    return p
  }, [year, month, hidePaid])

  const { data, isLoading } = useQuery({
    queryKey: ['payroll', params],
    queryFn: async () => (await api.get<PayrollList>('/payroll/lines', { params })).data,
  })

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number
      payload: Partial<Pick<PayrollLine, 'cost_price' | 'share_half' | 'salary_paid'>>
    }) => api.patch<PayrollLine>(`/payroll/lines/${id}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['payroll'] })
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось сохранить')),
  })

  const years = [now.getFullYear() + 1, now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2, now.getFullYear() - 3]

  const items = data?.items ?? []

  return (
    <div>
      <PageHeader
        title="Расчёт ЗП"
        subtitle="Строки таблицы №1 по оплаченным и предоплаченным договорам, где вы ответственный"
      />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-foreground-muted">Год</span>
          <select className="input" value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="">Все</option>
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-foreground-muted">Месяц</span>
          <select className="input" value={month} onChange={(e) => setMonth(e.target.value)}>
            <option value="">Все</option>
            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 pb-2 text-sm">
          <input
            type="checkbox"
            checked={hidePaid}
            onChange={(e) => setHidePaid(e.target.checked)}
          />
          Скрыть уже выплаченные
        </label>
      </div>

      <div className="mb-4 flex flex-wrap gap-4 rounded-lg border border-surface-border bg-surface-sidebar/40 px-4 py-3 text-sm">
        <div>
          <span className="text-foreground-muted">К выплате: </span>
          <span className="font-semibold text-foreground">{money(Number(data?.total_to_pay ?? 0))} ₽</span>
        </div>
        <div>
          <span className="text-foreground-muted">Уже получено: </span>
          <span className="font-medium">{money(Number(data?.total_paid ?? 0))} ₽</span>
        </div>
        <div>
          <span className="text-foreground-muted">Всего по списку: </span>
          <span className="font-medium">{money(Number(data?.total_all ?? 0))} ₽</span>
        </div>
      </div>

      {isLoading ? (
        <p className="text-foreground-muted">Загрузка...</p>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-16 text-foreground-muted">
          <Wallet size={36} strokeWidth={1.25} />
          <p>Нет подходящих строк. Нужны оплаченные/предоплаченные договоры с таблицей №1.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-surface-border">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-surface-sidebar text-xs uppercase tracking-wide text-foreground-muted">
              <tr>
                <th className="px-3 py-2 font-medium">Договор</th>
                <th className="px-3 py-2 font-medium">Документ</th>
                <th className="px-3 py-2 font-medium">Продукция</th>
                <th className="px-3 py-2 font-medium text-right">Цена</th>
                <th className="px-3 py-2 font-medium text-right">Себ-ть</th>
                <th className="px-3 py-2 font-medium text-right">В ЗП</th>
                <th className="px-3 py-2 font-medium text-center" title="Если оформляли вдвоём — половина">
                  ÷2
                </th>
                <th className="px-3 py-2 font-medium text-center">Выплачено</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr
                  key={row.id}
                  className={`border-t border-surface-border/80 ${
                    row.salary_paid ? 'bg-surface-sidebar/30 opacity-70' : ''
                  }`}
                >
                  <td className="px-3 py-2 align-top">
                    <Link to={`/contracts/${row.contract_id}`} className="font-medium text-primary hover:underline">
                      {row.contract_label}
                    </Link>
                    {row.client_name && (
                      <div className="text-xs text-foreground-muted">{row.client_name}</div>
                    )}
                    <div className="text-[11px] text-foreground-faint">
                      {paymentStatusLabels[row.payment_status]}
                    </div>
                  </td>
                  <td className="px-3 py-2 align-top max-w-[12rem]">{row.document_name}</td>
                  <td className="px-3 py-2 align-top max-w-[16rem] text-foreground-muted">
                    {row.product_name}
                  </td>
                  <td className="px-3 py-2 align-top text-right whitespace-nowrap">
                    {money(Number(row.price))}
                  </td>
                  <td className="px-3 py-2 align-top">
                    <input
                      type="number"
                      min={0}
                      step="0.01"
                      className="input w-28 text-right"
                      defaultValue={row.cost_price != null ? Number(row.cost_price) : ''}
                      key={`${row.id}-${row.cost_price}`}
                      onBlur={(e) => {
                        const raw = e.target.value.trim()
                        const next = raw === '' ? null : Number(raw)
                        const prev = row.cost_price != null ? Number(row.cost_price) : null
                        if (next === prev) return
                        if (next != null && (Number.isNaN(next) || next < 0)) {
                          toast.error('Себестоимость должна быть числом ≥ 0')
                          return
                        }
                        updateMutation.mutate({
                          id: row.id,
                          payload: { cost_price: next },
                        })
                      }}
                    />
                  </td>
                  <td className="px-3 py-2 align-top text-right font-medium whitespace-nowrap">
                    {money(Number(row.reward_mine))}
                  </td>
                  <td className="px-3 py-2 align-top text-center">
                    <input
                      type="checkbox"
                      checked={row.share_half}
                      title="Оформляли вдвоём — ваша доля 50%"
                      onChange={(e) =>
                        updateMutation.mutate({ id: row.id, payload: { share_half: e.target.checked } })
                      }
                    />
                  </td>
                  <td className="px-3 py-2 align-top text-center">
                    <input
                      type="checkbox"
                      checked={row.salary_paid}
                      title="ЗП по этой строке уже выплачена"
                      onChange={(e) =>
                        updateMutation.mutate({ id: row.id, payload: { salary_paid: e.target.checked } })
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-4 text-xs text-foreground-faint">
        Формула: ((цена × 0,94) − себестоимость) × 0,7; при «÷2» — половина. Выплаченные строки не входят в «К
        выплате».
      </p>
    </div>
  )
}
