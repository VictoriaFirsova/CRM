import { isAxiosError } from 'axios'

export function getApiErrorMessage(error: unknown, fallback = 'Произошла ошибка'): string {
  if (isAxiosError(error)) {
    if (!error.response) {
      return 'Сервер недоступен. Запустите backend: cd backend && uvicorn app.main:app --reload --port 8000'
    }
    const detail = error.response.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(', ') || fallback
    }
    if (error.response.status === 401) return 'Неверный email или пароль'
  }
  return fallback
}
