import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search, Archive } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../api/client'
import ClientForm from '../components/ClientForm'
import DocxImportButton, { type ClientParseResponse } from '../components/DocxImportButton'
import ParseHintsBanner from '../components/ParseHintsBanner'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../utils/apiError'
import { emptyClientForm, formToPayload, type ClientFormData } from '../utils/clientFields'
import type { Client } from '../types'

export default function ClientsPage() {
  const { user } = useAuth()
  const [search, setSearch] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<ClientFormData>(emptyClientForm)
  const [parseMeta, setParseMeta] = useState<ClientParseResponse | null>(null)
  const qc = useQueryClient()

  const { data: clients = [], isLoading } = useQuery({
    queryKey: ['clients', search, showArchived],
    queryFn: async () =>
      (
        await api.get<Client[]>('/clients', {
          params: { search: search || undefined, archived: showArchived },
        })
      ).data,
  })

  const createMutation = useMutation({
    mutationFn: () => api.post('/clients', formToPayload(form)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clients'] })
      setModalOpen(false)
      setForm(emptyClientForm)
      setParseMeta(null)
      toast.success('Клиент создан')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Ошибка создания')),
  })

  return (
    <div>
      <PageHeader
        title={showArchived ? 'Архив клиентов' : 'Клиенты'}
        subtitle={`Добро пожаловать, ${user?.full_name ?? ''}!`}
        actions={
          !showArchived ? (
            <button type="button" className="btn-primary" onClick={() => setModalOpen(true)}>
              <Plus size={16} /> Добавить
            </button>
          ) : undefined
        }
      />

      <div className="filter-panel !grid-cols-1 sm:!grid-cols-[1fr_auto_auto]">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground-faint" size={16} />
          <input
            className="input pl-11"
            placeholder="Поиск по названию, ИНН..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button
          type="button"
          className={!showArchived ? 'pill-active' : 'pill-inactive'}
          onClick={() => setShowArchived(false)}
        >
          Активные
        </button>
        <button
          type="button"
          className={showArchived ? 'pill-active' : 'pill-inactive'}
          onClick={() => setShowArchived(true)}
        >
          <Archive size={14} className="inline" /> Архив
        </button>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Компания</th>
              <th>ИНН</th>
              {showArchived ? <th>Комментарий</th> : <th>Банк</th>}
              {showArchived ? <th>Дата архива</th> : <th>р/с</th>}
              <th></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="py-8 text-center text-foreground-muted">Загрузка...</td></tr>
            ) : clients.length === 0 ? (
              <tr><td colSpan={5} className="py-8 text-center text-foreground-muted">
                {showArchived ? 'Архив пуст' : 'Нет клиентов'}
              </td></tr>
            ) : (
              clients.map((c) => (
                <tr key={c.id}>
                  <td className="font-semibold text-foreground">{c.company_name}</td>
                  <td className="font-mono text-xs text-foreground-muted">{c.inn || '—'}</td>
                  {showArchived ? (
                    <>
                      <td className="max-w-xs text-sm text-foreground-muted">{c.archive_comment || '—'}</td>
                      <td className="text-sm text-foreground-muted">
                        {c.archived_at ? new Date(c.archived_at).toLocaleDateString('ru-RU') : '—'}
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="text-foreground-muted">{c.bank_name || '—'}</td>
                      <td className="font-mono text-xs text-foreground-muted">{c.settlement_account || '—'}</td>
                    </>
                  )}
                  <td>
                    <Link to={`/clients/${c.id}`} className="text-sm font-medium text-primary hover:underline">
                      Карточка →
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal title="Новый клиент" open={modalOpen} onClose={() => setModalOpen(false)} wide>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (!form.company_name.trim()) {
              toast.error('Укажите краткое наименование')
              return
            }
            createMutation.mutate()
          }}
        >
          <ParseHintsBanner meta={parseMeta} onDismiss={() => setParseMeta(null)} />
          <ClientForm form={form} onChange={setForm} compact />
          <div className="mt-6 flex flex-wrap justify-between gap-2 border-t border-surface-border pt-4">
            <DocxImportButton
              currentForm={form}
              onImported={(next, meta) => {
                setForm(next)
                setParseMeta(meta)
              }}
            />
            <div className="flex gap-2">
            <button type="button" className="btn-ghost" onClick={() => { setModalOpen(false); setParseMeta(null) }}>
              Отмена
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              Создать
            </button>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  )
}
