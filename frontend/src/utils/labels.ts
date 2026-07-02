import type {
  ContractStatus,
  DocumentType,
  InvoiceKind,
  PaymentRecordStatus,
  PaymentStatus,
  ProductionStatus,
} from '../types'

export const contractStatusLabels: Record<ContractStatus, string> = {
  OPEN: 'Открыт',
  CLOSED: 'Закрыт',
}

export const paymentStatusLabels: Record<PaymentStatus, string> = {
  NOT_PAID: 'Не оплачен',
  PARTIALLY_PAID: 'Частично',
  PAID: 'Оплачен',
}

export const productionStatusLabels: Record<ProductionStatus, string> = {
  REQUEST: 'Заявка',
  LAYOUT: 'Макет',
  SCAN: 'Скан',
  READY: 'Готов',
}

export const paymentRecordLabels: Record<PaymentRecordStatus, string> = {
  PENDING: 'Ожидает',
  PAID: 'Оплачен',
  CANCELED: 'Отменён',
}

export const invoiceKindLabels: Record<InvoiceKind, string> = {
  ADVANCE: 'Аванс',
  BALANCE: 'Остаток',
  FULL: '100%',
}

export const documentTypeLabels: Record<DocumentType, string> = {
  CONTRACT: 'Договор',
  INVOICE: 'Счёт',
  ACT: 'Акт',
  SCAN: 'Скан',
  OTHER: 'Прочее',
}
