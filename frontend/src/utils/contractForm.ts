import type { ContractKind } from '../types'

export const contractKindLabels: Record<ContractKind, string> = {
  FRAMEWORK: 'Рамочный договор',
  ADDENDUM: 'Приложение (доп.)',
}

export function defaultAddendumTitle(n: number) {
  return `Приложение №${n}`
}

export function todayInputDate() {
  return new Date().toISOString().slice(0, 10)
}

/** Пример номера для подписи поля */
export function frameworkNumberExample(prefix: string) {
  const y = new Date().getFullYear()
  return `${prefix}-000-${y}`
}
