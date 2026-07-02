import type { Client } from '../types'

export type ClientFormData = Omit<
  Client,
  | 'id'
  | 'owner_id'
  | 'created_at'
  | 'updated_at'
  | 'can_edit'
  | 'is_archived'
  | 'archive_comment'
  | 'archived_at'
>

export const emptyClientForm: ClientFormData = {
  company_name: '',
  full_company_name: '',
  inn: '',
  kpp: '',
  ogrn: '',
  legal_address: '',
  actual_address: '',
  bank_name: '',
  bik: '',
  correspondent_account: '',
  settlement_account: '',
  director_name: '',
  director_name_genitive: '',
  signer_position: '',
  signer_basis: '',
  contact_person: '',
  phone: '',
  email: '',
  notes: '',
}

export const clientFieldLabels: Record<keyof ClientFormData, string> = {
  company_name: 'Краткое наименование',
  full_company_name: 'Полное наименование',
  inn: 'ИНН',
  kpp: 'КПП',
  ogrn: 'ОГРН',
  legal_address: 'Юридический адрес',
  actual_address: 'Фактический адрес',
  bank_name: 'Наименование банка',
  bik: 'БИК',
  correspondent_account: 'Корреспондентский счёт (к/с)',
  settlement_account: 'Расчётный счёт (р/с)',
  director_name: 'ФИО подписанта',
  director_name_genitive: 'ФИО подписанта в родительном падеже',
  signer_position: 'Должность подписанта (в родительном падеже)',
  signer_basis: 'Действует на основании (в родительном падеже)',
  contact_person: 'Контактное лицо',
  phone: 'Телефон',
  email: 'Email',
  notes: 'Заметки',
}

export const clientFieldSections: { title: string; fields: (keyof ClientFormData)[] }[] = [
  {
    title: 'Организация',
    fields: [
      'company_name',
      'full_company_name',
      'director_name',
      'director_name_genitive',
      'signer_position',
      'signer_basis',
    ],
  },
  {
    title: 'Реквизиты',
    fields: ['inn', 'kpp', 'ogrn'],
  },
  {
    title: 'Адреса',
    fields: ['legal_address', 'actual_address'],
  },
  {
    title: 'Банковские реквизиты',
    fields: ['bik', 'bank_name', 'correspondent_account', 'settlement_account'],
  },
  {
    title: 'Контакты',
    fields: ['contact_person', 'phone', 'email'],
  },
  {
    title: 'Прочее',
    fields: ['notes'],
  },
]

export function clientToForm(client: Client): ClientFormData {
  const form = { ...emptyClientForm }
  for (const key of Object.keys(emptyClientForm) as (keyof ClientFormData)[]) {
    form[key] = (client[key] as string) ?? ''
  }
  return form
}

export function formToPayload(form: ClientFormData): Record<string, string | null> {
  const payload: Record<string, string | null> = {}
  for (const [key, value] of Object.entries(form)) {
    payload[key] = value?.trim() ? value.trim() : null
  }
  payload.company_name = form.company_name.trim()
  return payload
}
