import type { ContractLineItem } from '../types'

export type LineItemDraft = {
  document_name: string
  product_name: string
  price: string
  vat_exempt: boolean
}

export const emptyLineItem = (): LineItemDraft => ({
  document_name: '',
  product_name: '',
  price: '',
  vat_exempt: true,
})

export function lineItemsFromContract(items: ContractLineItem[] | undefined): LineItemDraft[] {
  if (!items?.length) return [emptyLineItem()]
  return items.map((item) => ({
    document_name: item.document_name,
    product_name: item.product_name,
    price: String(item.price),
    vat_exempt: item.vat_exempt !== false,
  }))
}

export function sumLineItems(lines: LineItemDraft[]): number {
  return lines.reduce((total, line) => total + (parseFloat(line.price.replace(',', '.')) || 0), 0)
}

export function formatLinePrice(price: number, vatExempt: boolean): string {
  const rub = `${price.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} руб.`
  return vatExempt ? `${rub} (НДС не облагается)` : rub
}

export function linesToPayload(lines: LineItemDraft[]) {
  return lines
    .map((line) => ({
      document_name: line.document_name.trim(),
      product_name: line.product_name.trim(),
      price: parseFloat(line.price.replace(',', '.')) || 0,
      vat_exempt: line.vat_exempt,
    }))
    .filter((line) => line.document_name && line.product_name)
}
