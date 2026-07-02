import { useState } from 'react'
import { Building2, Landmark, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'
import { getApiErrorMessage } from '../utils/apiError'
import type { ClientFormData } from '../utils/clientFields'
import { clientFieldLabels, clientFieldSections } from '../utils/clientFields'

interface BankLookupResult {
  bik: string
  bank_name?: string
  correspondent_account?: string
  found: boolean
  message?: string
}

interface PartyLookupResult {
  query?: string
  inn: string
  company_name?: string
  full_company_name?: string
  kpp?: string
  ogrn?: string
  legal_address?: string
  director_name?: string
  director_name_genitive?: string
  signer_position?: string
  signer_basis?: string
  phone?: string
  email?: string
  found: boolean
  message?: string
}

interface ClientFormProps {
  form: ClientFormData
  onChange: (form: ClientFormData) => void
  disabled?: boolean
  compact?: boolean
}

function buildPartyQuery(form: ClientFormData): string | null {
  const inn = (form.inn ?? '').replace(/\D/g, '')
  if (inn.length === 10 || inn.length === 12) {
    const kpp = (form.kpp ?? '').replace(/\D/g, '')
    return kpp ? `${inn}/${kpp}` : inn
  }
  const ogrn = (form.ogrn ?? '').replace(/\D/g, '')
  if (ogrn.length === 13 || ogrn.length === 15) return ogrn
  return null
}

function mergeParty(form: ClientFormData, data: PartyLookupResult): ClientFormData {
  return {
    ...form,
    inn: data.inn || form.inn,
    company_name: data.company_name || form.company_name,
    full_company_name: data.full_company_name || form.full_company_name,
    kpp: data.kpp || form.kpp,
    ogrn: data.ogrn || form.ogrn,
    legal_address: data.legal_address || form.legal_address,
    director_name: data.director_name || form.director_name,
    director_name_genitive: data.director_name_genitive || form.director_name_genitive,
    signer_position: data.signer_position || form.signer_position,
    signer_basis: data.signer_basis || form.signer_basis,
    phone: data.phone || form.phone,
    email: data.email || form.email,
  }
}

function mergeBank(form: ClientFormData, data: BankLookupResult): ClientFormData {
  return {
    ...form,
    bik: data.bik,
    bank_name: data.bank_name || form.bank_name,
    correspondent_account: data.correspondent_account || form.correspondent_account,
  }
}

export default function ClientForm({ form, onChange, disabled, compact }: ClientFormProps) {
  const [partyLoading, setPartyLoading] = useState(false)
  const [bankLoading, setBankLoading] = useState(false)
  const set = (key: keyof ClientFormData, value: string) => onChange({ ...form, [key]: value })
  const setWithAutofill = (key: keyof ClientFormData, value: string) => {
    const next: ClientFormData = { ...form, [key]: value }
    if (
      key === 'director_name' &&
      (!form.director_name_genitive || form.director_name_genitive === form.director_name)
    ) {
      next.director_name_genitive = value
    }
    if (key === 'signer_position' && !form.signer_position) {
      next.signer_position = value
    }
    if (key === 'signer_basis' && !form.signer_basis) {
      next.signer_basis = value
    }
    onChange(next)
  }

  const lookupParty = async (queryOverride?: string) => {
    const query = queryOverride ?? buildPartyQuery(form)
    if (!query) {
      toast.error('ИНН (10/12), ОГРН (13/15) или ИНН и КПП')
      return
    }
    setPartyLoading(true)
    try {
      const { data } = await api.get<PartyLookupResult>(
        `/clients/lookup-party/${encodeURIComponent(query)}`,
      )
      if (!data.found) {
        toast.error(data.message || 'Организация не найдена')
        return
      }
      onChange(mergeParty(form, data))
      toast.success(data.message || 'Организация загружена')
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Ошибка DaData'))
    } finally {
      setPartyLoading(false)
    }
  }

  const lookupBank = async (bikOverride?: string) => {
    const bik = (bikOverride ?? form.bik ?? '').replace(/\D/g, '')
    if (bik.length !== 9) {
      toast.error('БИК: 9 цифр')
      return
    }
    setBankLoading(true)
    try {
      const { data } = await api.get<BankLookupResult>(`/clients/lookup-bank/${bik}`)
      if (!data.found) {
        toast.error(data.message || 'Банк не найден')
        return
      }
      onChange(mergeBank(form, data))
      toast.success(data.message || 'Банк загружен')
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Ошибка DaData'))
    } finally {
      setBankLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {!disabled && (
        <div className="rounded-card border border-primary/20 bg-primary-light/40 p-4">
          <p className="mb-3 text-sm font-medium text-foreground">
            Подгрузка из DaData при ручном вводе
          </p>
          <p className="mb-4 text-xs text-foreground-muted">
            ИНН, ОГРН (или ИНН с КПП для филиала) и БИК — подгрузка через DaData find-party /
            find-bank. Проверьте данные перед сохранением.
          </p>
          <div className={`grid gap-3 ${compact ? '' : 'sm:grid-cols-2'}`}>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground-muted">ИНН организации</label>
              <div className="flex gap-2">
                <input
                  className="input font-mono"
                  value={form.inn}
                  onChange={(e) => set('inn', e.target.value)}
                  placeholder="7707083893"
                  maxLength={12}
                  onBlur={() => {
                    const inn = (form.inn ?? '').replace(/\D/g, '')
                    if ((inn.length === 10 || inn.length === 12) && !partyLoading) void lookupParty()
                  }}
                />
                <button
                  type="button"
                  className="btn-ghost shrink-0"
                  onClick={() => void lookupParty()}
                  disabled={partyLoading}
                  title="Загрузить организацию"
                >
                  {partyLoading ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Building2 size={16} />
                  )}
                  <span className="hidden sm:inline">Организация</span>
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground-muted">БИК банка</label>
              <div className="flex gap-2">
                <input
                  className="input font-mono"
                  value={form.bik}
                  onChange={(e) => set('bik', e.target.value)}
                  placeholder="044525225"
                  maxLength={11}
                  onBlur={(e) => {
                    const bik = e.target.value.replace(/\D/g, '')
                    if (bik.length === 9 && !bankLoading) {
                      void lookupBank(bik)
                    }
                  }}
                />
                <button
                  type="button"
                  className="btn-ghost shrink-0"
                  onClick={() => void lookupBank()}
                  disabled={bankLoading}
                  title="Загрузить банк"
                >
                  {bankLoading ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Landmark size={16} />
                  )}
                  <span className="hidden sm:inline">Банк</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {clientFieldSections.map((section) => (
        <div key={section.title}>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground-faint">
            {section.title}
          </h3>
          <div className={`grid gap-3 ${compact ? 'sm:grid-cols-2' : ''}`}>
            {section.fields.map((key) => {
              if (key === 'inn' || key === 'bik') return null
              const isWide = ['legal_address', 'actual_address', 'full_company_name', 'notes', 'bank_name'].includes(key)
              const isTextarea = ['legal_address', 'actual_address', 'notes'].includes(key)
              return (
                <div key={key} className={isWide && !compact ? 'sm:col-span-2' : compact && isWide ? 'sm:col-span-2' : ''}>
                  <label className="mb-1.5 block text-xs font-medium text-foreground-muted">
                    {clientFieldLabels[key]}
                  </label>
                  {isTextarea ? (
                    <textarea
                      className="input min-h-[72px]"
                      disabled={disabled}
                      value={form[key]}
                      onChange={(e) => setWithAutofill(key, e.target.value)}
                      rows={2}
                    />
                  ) : (
                    <input
                      className={`input ${key === 'settlement_account' || key === 'correspondent_account' || key === 'ogrn' ? 'font-mono' : ''}`}
                      disabled={disabled}
                      value={form[key]}
                      onChange={(e) => setWithAutofill(key, e.target.value)}
                      onBlur={
                        key === 'ogrn' && !disabled
                          ? () => {
                              const ogrn = (form.ogrn ?? '').replace(/\D/g, '')
                              const inn = (form.inn ?? '').replace(/\D/g, '')
                              if (
                                (ogrn.length === 13 || ogrn.length === 15) &&
                                inn.length !== 10 &&
                                inn.length !== 12 &&
                                !partyLoading
                              ) {
                                void lookupParty(ogrn)
                              }
                            }
                          : undefined
                      }
                      required={key === 'company_name'}
                    />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
