export type UserRole = 'ADMIN' | 'MANAGER' | 'VIEWER'
export type ContractKind = 'FRAMEWORK' | 'ADDENDUM'
export type ContractStatus = 'OPEN' | 'CLOSED'
export type PaymentStatus = 'NOT_PAID' | 'PARTIALLY_PAID' | 'PAID'
export type ProductionStatus = 'REQUEST' | 'LAYOUT' | 'SCAN' | 'READY'
export type PaymentRecordStatus = 'PENDING' | 'PAID' | 'CANCELED'
export type DocumentType = 'CONTRACT' | 'INVOICE' | 'ACT' | 'SCAN' | 'OTHER'
export type InvoiceKind = 'ADVANCE' | 'BALANCE' | 'FULL'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
}

export interface Client {
  id: number
  owner_id: number
  company_name: string
  full_company_name?: string
  inn?: string
  kpp?: string
  ogrn?: string
  legal_address?: string
  actual_address?: string
  bank_name?: string
  bik?: string
  correspondent_account?: string
  settlement_account?: string
  director_name?: string
  director_name_genitive?: string
  signer_position?: string
  signer_basis?: string
  contact_person?: string
  phone?: string
  email?: string
  notes?: string
  is_archived?: boolean
  archive_comment?: string | null
  archived_at?: string | null
  created_at: string
  updated_at: string
  can_edit: boolean
}

export interface ClientHistory {
  id: number
  client_id: number
  changed_by: number
  field_name: string
  old_value?: string
  new_value?: string
  changed_at: string
}

export interface ContractLineItem {
  id: number
  contract_id: number
  position: number
  document_name: string
  product_name: string
  price: number
  vat_exempt: boolean
}

export interface Contract {
  id: number
  kind: ContractKind
  parent_contract_id?: number | null
  addendum_number?: number | null
  number_prefix?: string | null
  client_id: number
  responsible_manager_id: number
  contract_number: string
  title: string
  display_label?: string
  parent_contract_number?: string | null
  amount: number
  contract_status: ContractStatus
  payment_status: PaymentStatus
  production_status: ProductionStatus
  comment?: string
  work_days?: number | null
  advance_percent?: number | null
  line_items?: ContractLineItem[]
  start_date?: string
  end_date?: string
  created_at: string
  updated_at: string
  can_edit: boolean
  client_name?: string
  manager_name?: string
}

export interface Payment {
  id: number
  contract_id: number
  amount: number
  payment_date?: string
  status: PaymentRecordStatus
  comment?: string
  created_at: string
  can_edit: boolean
  contract_number?: string
}

export interface Act {
  id: number
  contract_id: number
  amount: number
  act_date: string
  generated_at: string
  contract_number?: string
  client_name?: string
  addendum_number?: number | null
  production_status?: ProductionStatus
  can_edit?: boolean
  can_download?: boolean
}

export interface Invoice {
  id: number
  contract_id: number
  kind: InvoiceKind
  amount: number
  invoice_date: string
  status: PaymentRecordStatus
  created_at: string
  created_by?: number | null
  contract_number?: string
  client_name?: string
  addendum_number?: number | null
  can_edit?: boolean
}

export interface Document {
  id: number
  contract_id: number
  client_id: number
  type: DocumentType
  file_path: string
  generated_at: string
  generated_by?: number
}

export interface DashboardData {
  stats: {
    clients_count: number
    active_contracts: number
    unpaid_contracts: number
  }
  recent_activity: Array<{
    id: number
    action: string
    entity_type: string
    entity_id: number
    user_id?: number
    created_at: string
  }>
}
