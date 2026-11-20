import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, UserCog } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Navigate } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { useAuth } from '../context/AuthContext'
import type { User, UserRole } from '../types'
import { getApiErrorMessage } from '../utils/apiError'

const roleLabels: Record<UserRole, string> = {
  ADMIN: 'Администратор',
  MANAGER: 'Менеджер',
  VIEWER: 'Только просмотр',
}

const emptyForm = () => ({
  email: '',
  full_name: '',
  password: '',
  role: 'MANAGER' as UserRole,
})

export default function UsersPage() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const isAdmin = user?.role === 'ADMIN'

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => (await api.get<User[]>('/users')).data,
    enabled: isAdmin,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.post<User>('/users', {
        email: form.email.trim(),
        full_name: form.full_name.trim(),
        password: form.password,
        role: form.role,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      setModalOpen(false)
      setForm(emptyForm())
      toast.success('Пользователь создан')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось создать')),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<User> & { password?: string } }) =>
      api.put<User>(`/users/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      toast.success('Сохранено')
    },
    onError: (err) => toast.error(getApiErrorMessage(err, 'Не удалось обновить')),
  })

  if (user && !isAdmin) {
    return <Navigate to="/" replace />
  }

  return (
    <div>
      <PageHeader
        title="Пользователи"
        subtitle="Создание учёток сотрудников. Публичная регистрация отключена."
        actions={
          <button
            type="button"
            className="btn-primary"
            onClick={() => {
              setForm(emptyForm())
              setModalOpen(true)
            }}
          >
            <Plus size={16} /> Добавить
          </button>
        }
      />

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>ФИО</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-foreground-muted">
                  Загрузка...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-foreground-muted">
                  Нет пользователей
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className={!u.is_active ? 'opacity-60' : undefined}>
                  <td className="font-medium">{u.full_name}</td>
                  <td className="font-mono text-sm text-foreground-muted">{u.email}</td>
                  <td>
                    <select
                      className="select-input w-auto min-w-[10rem]"
                      value={u.role}
                      disabled={updateMutation.isPending || u.id === user?.id}
                      onChange={(e) =>
                        updateMutation.mutate({
                          id: u.id,
                          data: { role: e.target.value as UserRole },
                        })
                      }
                    >
                      {(Object.keys(roleLabels) as UserRole[]).map((r) => (
                        <option key={r} value={r}>
                          {roleLabels[r]}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>{u.is_active ? 'Активен' : 'Отключён'}</td>
                  <td>
                    {u.id !== user?.id && (
                      <button
                        type="button"
                        className="text-sm text-primary hover:underline"
                        disabled={updateMutation.isPending}
                        onClick={() =>
                          updateMutation.mutate({
                            id: u.id,
                            data: { is_active: !u.is_active },
                          })
                        }
                      >
                        {u.is_active ? 'Отключить' : 'Включить'}
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        title="Новый пользователь"
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setForm(emptyForm())
        }}
      >
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault()
            if (!form.email.trim() || !form.full_name.trim() || form.password.length < 6) {
              toast.error('Заполните ФИО, email и пароль (от 6 символов)')
              return
            }
            createMutation.mutate()
          }}
        >
          <label className="block text-sm">
            <span className="mb-1 block text-foreground-muted">ФИО</span>
            <input
              className="input"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-foreground-muted">Email</span>
            <input
              className="input"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-foreground-muted">Временный пароль</span>
            <input
              className="input"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              minLength={6}
              required
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-foreground-muted">Роль</span>
            <select
              className="select-input w-full"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
            >
              {(Object.keys(roleLabels) as UserRole[]).map((r) => (
                <option key={r} value={r}>
                  {roleLabels[r]}
                </option>
              ))}
            </select>
          </label>
          <div className="flex justify-end gap-2 border-t border-surface-border pt-4">
            <button type="button" className="btn-ghost" onClick={() => setModalOpen(false)}>
              Отмена
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              <UserCog size={16} />
              {createMutation.isPending ? 'Создание…' : 'Создать'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
