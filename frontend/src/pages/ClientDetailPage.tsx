import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Archive, ArchiveRestore, Save, Trash2 } from 'lucide-react'
import api from '../api/client'
import ClientForm from '../components/ClientForm'
import DocxImportButton, { type ClientParseResponse } from '../components/DocxImportButton'
import ParseHintsBanner from '../components/ParseHintsBanner'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { getApiErrorMessage } from '../utils/apiError'
import { clientFieldLabels, clientToForm, formToPayload, type ClientFormData } from '../utils/clientFields'
import type { Client, ClientHistory } from '../types'

export default function ClientDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [form, setForm] = useState<ClientFormData | null>(null)
  const [parseMeta, setParseMeta] = useState<ClientParseResponse | null>(null)
  const [archiveModalOpen, setArchiveModalOpen] = useState(false)
  const [archiveComment, setArchiveComment] = useState('')

  const { data: client, isLoading } = useQuery({
    queryKey: ['client', id],
    queryFn: async () => (await api.get<Client>(`/clients/${id}`)).data,
  })

  const { data: history = [] } = useQuery({
    queryKey: ['client-history', id],
    queryFn: async () => (await api.get<ClientHistory[]>(`/clients/${id}/history`)).data,
  })

  useEffect(() => {
    if (client) setForm(clientToForm(client))
  }, [client])

  const updateMutation = useMutation({
    mutationFn: (data: ReturnType<typeof formToPayload>) => api.put(`/clients/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client', id] })
      qc.invalidateQueries({ queryKey: ['client-history', id] })
      qc.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Реквизиты сохранены')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось сохранить')),
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/clients/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Клиент удалён')
      navigate('/clients')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось удалить')),
  })

  const archiveMutation = useMutation({
    mutationFn: (comment: string) => api.post<Client>(`/clients/${id}/archive`, { comment }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client', id] })
      qc.invalidateQueries({ queryKey: ['client-history', id] })
      qc.invalidateQueries({ queryKey: ['clients'] })
      setArchiveModalOpen(false)
      setArchiveComment('')
      toast.success('Клиент перенесён в архив')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось архивировать')),
  })

  const unarchiveMutation = useMutation({
    mutationFn: () => api.post<Client>(`/clients/${id}/unarchive`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['client', id] })
      qc.invalidateQueries({ queryKey: ['client-history', id] })
      qc.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Клиент восстановлен из архива')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось восстановить')),
  })

  const handleDelete = () => {
    if (
      !window.confirm(
        `Удалить клиента «${client?.company_name ?? ''}»? Действие необратимо.`,
      )
    ) {
      return
    }
    deleteMutation.mutate()
  }

  if (isLoading || !client || !form) {
    return <div className="py-12 text-center text-foreground-muted">Загрузка...</div>
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    if (client.is_archived) return
    if (!form.company_name.trim()) {
      toast.error('Укажите краткое наименование')
      return
    }
    updateMutation.mutate(formToPayload(form))
  }

  return (
    <div>
      <Link
        to="/clients"
        className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
      >
        <ArrowLeft size={16} /> К списку клиентов
      </Link>

      <PageHeader
        title={client.company_name}
        subtitle={
          client.is_archived
            ? 'Клиент в архиве — только просмотр'
            : !client.can_edit
              ? 'Только просмотр (чужой клиент)'
              : 'Заполните реквизиты и нажмите «Сохранить»'
        }
        actions={
          client.can_edit ? (
            <>
              {client.is_archived ? (
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => unarchiveMutation.mutate()}
                  disabled={unarchiveMutation.isPending}
                >
                  <ArchiveRestore size={16} />
                  {unarchiveMutation.isPending ? 'Восстановление…' : 'Восстановить'}
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => setArchiveModalOpen(true)}
                  >
                    <Archive size={16} /> В архив
                  </button>
                  <button
                    type="button"
                    className="btn-ghost text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/40"
                    onClick={handleDelete}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 size={16} />
                    {deleteMutation.isPending ? 'Удаление...' : 'Удалить'}
                  </button>
                  <DocxImportButton
                    currentForm={form}
                    onImported={(next, meta) => {
                      setForm(next)
                      setParseMeta(meta)
                    }}
                  />
                  <button
                    type="submit"
                    form="client-form"
                    className="btn-primary"
                    disabled={updateMutation.isPending}
                  >
                    <Save size={16} />
                    {updateMutation.isPending ? 'Сохранение...' : 'Сохранить'}
                  </button>
                </>
              )}
            </>
          ) : undefined
        }
      />

      {client.is_archived && client.archive_comment && (
        <div className="mb-6 rounded-card border border-amber-500/30 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:bg-amber-950/30 dark:text-amber-100">
          <p className="font-medium">Комментарий при архивации</p>
          <p className="mt-1 whitespace-pre-wrap">{client.archive_comment}</p>
          {client.archived_at && (
            <p className="mt-2 text-xs opacity-80">
              {new Date(client.archived_at).toLocaleString('ru-RU')}
            </p>
          )}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_400px]">
        <form id="client-form" onSubmit={handleSave} className="card">
          <ParseHintsBanner meta={parseMeta} onDismiss={() => setParseMeta(null)} />
          <ClientForm form={form} onChange={setForm} disabled={!client.can_edit || !!client.is_archived} />
        </form>

        <div className="card xl:sticky xl:top-6 xl:self-start">
          <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
            История изменений
          </h2>
          <p className="mb-4 text-xs text-foreground-muted">Все правки реквизитов</p>
          {history.length === 0 ? (
            <p className="py-8 text-center text-sm text-foreground-muted">Пока нет изменений</p>
          ) : (
            <div className="max-h-[70vh] overflow-y-auto">
              <div className="table-wrap shadow-none">
                <table className="data-table text-xs">
                  <thead>
                    <tr>
                      <th>Поле</th>
                      <th>Изменение</th>
                      <th>Дата</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => (
                      <tr key={h.id}>
                        <td className="font-medium">
                          {h.field_name === 'archived'
                            ? 'Архив'
                            : clientFieldLabels[h.field_name as keyof ClientFormData] || h.field_name}
                        </td>
                        <td className="max-w-[140px]">
                          <span className="block truncate text-foreground-muted">{h.old_value || '—'}</span>
                          <span className="block truncate">→ {h.new_value || '—'}</span>
                        </td>
                        <td className="whitespace-nowrap text-foreground-muted">
                          {new Date(h.changed_at).toLocaleString('ru-RU')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      <Modal
        title="Перенести в архив"
        open={archiveModalOpen}
        onClose={() => {
          setArchiveModalOpen(false)
          setArchiveComment('')
        }}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (!archiveComment.trim()) {
              toast.error('Укажите комментарий')
              return
            }
            archiveMutation.mutate(archiveComment.trim())
          }}
        >
          <p className="mb-4 text-sm text-foreground-muted">
            Клиент исчезнет из списка активных, но останется в архиве вместе с договорами и документами.
          </p>
          <label className="mb-4 block text-sm">
            <span className="mb-1 block text-foreground-muted">Комментарий</span>
            <textarea
              className="input min-h-[100px]"
              value={archiveComment}
              onChange={(e) => setArchiveComment(e.target.value)}
              placeholder="Причина архивации..."
              required
            />
          </label>
          <div className="flex justify-end gap-2 border-t border-surface-border pt-4">
            <button
              type="button"
              className="btn-ghost"
              onClick={() => {
                setArchiveModalOpen(false)
                setArchiveComment('')
              }}
            >
              Отмена
            </button>
            <button type="submit" className="btn-primary" disabled={archiveMutation.isPending}>
              {archiveMutation.isPending ? 'Архивация…' : 'В архив'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
