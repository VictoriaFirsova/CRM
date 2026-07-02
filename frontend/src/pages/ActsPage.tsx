import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, FileCheck, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import AddendumSelect from '../components/AddendumSelect'
import PageHeader from '../components/PageHeader'
import { getApiErrorMessage } from '../utils/apiError'
import { downloadAct } from '../utils/downloadFile'
import { todayInputDate } from '../utils/contractForm'
import type { Act, Contract } from '../types'
import { productionStatusLabels } from '../utils/labels'

export default function ActsPage() {
  const [modalOpen, setModalOpen] = useState(false)
  const [contractId, setContractId] = useState('')
  const [actDate, setActDate] = useState(todayInputDate())
  const qc = useQueryClient()

  const { data: acts = [], isLoading } = useQuery({
    queryKey: ['acts'],
    queryFn: async () => (await api.get<Act[]>('/acts')).data,
  })

  const { data: contractsData } = useQuery({
    queryKey: ['contracts-addendums-acts'],
    queryFn: async () => {
      const data = (await api.get<{ items: Contract[] }>('/contracts', { params: { limit: 500 } })).data
      return { items: data.items.filter((c) => c.kind === 'ADDENDUM') }
    },
  })
  const addendums = contractsData?.items ?? []
  const actContractIds = new Set(acts.map((a) => a.contract_id))
  const hasAct = acts.some((a) => a.contract_id === Number(contractId))

  const deleteMutation = useMutation({
    mutationFn: (actId: number) => api.delete(`/acts/${actId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['acts'] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Акт удалён')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось удалить акт')),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.post<Act>('/acts', { contract_id: Number(contractId), act_date: actDate }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['acts'] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      setModalOpen(false)
      setActDate(todayInputDate())
      toast.success('Акт создан')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось создать акт')),
  })

  const updateDateMutation = useMutation({
    mutationFn: ({ actId, date }: { actId: number; date: string }) =>
      api.put<Act>(`/acts/${actId}`, { act_date: date }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['acts'] })
      qc.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Дата акта обновлена')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось изменить дату')),
  })

  return (
    <div>
      <PageHeader
        title="Акты"
        subtitle="Акт выполненных работ (XLSX). Статус оплаты не важен — можно до выставления счёта"
        actions={
          <button type="button" className="btn-primary" onClick={() => setModalOpen(true)}>
            <Plus size={16} /> Сформировать акт
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
              <th>Этап</th>
              <th>Сумма</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-foreground-muted">
                  Загрузка...
                </td>
              </tr>
            ) : acts.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-foreground-muted">
                  Актов пока нет
                </td>
              </tr>
            ) : (
              acts.map((act) => (
                <tr key={act.id}>
                  <td>
                    {act.can_edit ? (
                      <input
                        type="date"
                        className="input w-[9.5rem]"
                        value={act.act_date.slice(0, 10)}
                        disabled={updateDateMutation.isPending}
                        onChange={(e) => {
                          const next = e.target.value
                          if (!next || next === act.act_date.slice(0, 10)) return
                          updateDateMutation.mutate({ actId: act.id, date: next })
                        }}
                      />
                    ) : (
                      new Date(act.act_date).toLocaleDateString('ru-RU')
                    )}
                  </td>
                  <td>{act.client_name || '—'}</td>
                  <td>
                    <Link to={`/contracts/${act.contract_id}`} className="text-primary hover:underline">
                      {act.contract_number}
                      {act.addendum_number != null ? ` / доп ${act.addendum_number}` : ''}
                    </Link>
                  </td>
                  <td>
                    {act.production_status
                      ? productionStatusLabels[act.production_status]
                      : '—'}
                  </td>
                  <td className="font-mono text-sm">
                    {Number(act.amount).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ₽
                  </td>
                  <td>
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        className="text-primary hover:underline"
                        onClick={() => void downloadAct(act.id)}
                      >
                        <Download size={14} className="inline" /> XLSX
                      </button>
                      {act.can_edit && (
                        <button
                          type="button"
                          className="text-red-600 hover:underline dark:text-red-400"
                          disabled={deleteMutation.isPending}
                          onClick={() => {
                            if (!window.confirm('Удалить акт? Файл будет удалён, можно сформировать заново.')) {
                              return
                            }
                            deleteMutation.mutate(act.id)
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
        title="Новый акт"
        wide
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setContractId('')
          setActDate(todayInputDate())
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
          <AddendumSelect
            addendums={addendums}
            value={contractId}
            onChange={setContractId}
            withActIds={actContractIds}
          />

          {contractId && hasAct && (
            <p className="mb-4 mt-3 text-sm text-amber-700 dark:text-amber-400">
              Для этого приложения акт уже создан.
            </p>
          )}

          <label className="mb-4 mt-3 block text-sm">
            <span className="mb-1 block text-foreground-muted">Дата акта</span>
            <input
              type="date"
              className="input w-full max-w-xs"
              value={actDate}
              onChange={(e) => setActDate(e.target.value)}
            />
          </label>

          <div className="flex justify-end gap-2 border-t border-surface-border pt-4">
            <button type="button" className="btn-ghost" onClick={() => setModalOpen(false)}>
              Отмена
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={createMutation.isPending || !contractId || hasAct}
            >
              <FileCheck size={16} />
              {createMutation.isPending ? 'Формирование…' : 'Сформировать'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
