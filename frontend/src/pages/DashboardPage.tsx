import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import KpiCard from '../components/KpiCard'
import PageHeader from '../components/PageHeader'
import { useAuth } from '../context/AuthContext'
import type { DashboardData } from '../types'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<DashboardData>('/dashboard')).data,
  })

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center text-foreground-muted">Загрузка...</div>
    )
  }

  const stats = [
    {
      label: 'Клиентов',
      value: data?.stats.clients_count ?? 0,
      trend: { value: 'всего в системе', positive: true },
      sparkline: [2, 4, 3, 6, 5, 7, 8, 9, 10, 12],
    },
    {
      label: 'Активных договоров',
      value: data?.stats.active_contracts ?? 0,
      trend: { value: 'в работе', positive: true },
      sparkline: [5, 6, 5, 8, 7, 9, 8, 10, 11, 12],
    },
    {
      label: 'Неоплаченных',
      value: data?.stats.unpaid_contracts ?? 0,
      trend: {
        value: 'требуют внимания',
        positive: (data?.stats.unpaid_contracts ?? 0) === 0,
      },
      sparkline: [8, 7, 6, 5, 6, 4, 5, 3, 4, 3],
    },
  ]

  return (
    <div>
      <PageHeader
        title="Дашборд"
        subtitle={`Добро пожаловать, ${user?.full_name ?? 'пользователь'}!`}
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((s) => (
          <KpiCard
            key={s.label}
            label={s.label}
            value={s.value}
            trend={s.trend}
            sparkline={s.sparkline}
          />
        ))}
      </div>

      <div className="card">
        <h2 className="mb-1 text-sm font-semibold uppercase tracking-wider text-foreground-faint">
          Последние изменения
        </h2>
        <p className="mb-4 text-xs text-foreground-muted">Активность в системе</p>
        {data?.recent_activity.length === 0 ? (
          <p className="py-8 text-center text-sm text-foreground-muted">Нет записей</p>
        ) : (
          <div className="table-wrap shadow-none">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Действие</th>
                  <th>Сущность</th>
                  <th>ID</th>
                  <th>Дата</th>
                </tr>
              </thead>
              <tbody>
                {data?.recent_activity.map((a) => (
                  <tr key={a.id}>
                    <td className="font-medium">{a.action}</td>
                    <td className="text-foreground-muted">{a.entity_type}</td>
                    <td>#{a.entity_id}</td>
                    <td className="text-foreground-muted">
                      {new Date(a.created_at).toLocaleString('ru-RU')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
