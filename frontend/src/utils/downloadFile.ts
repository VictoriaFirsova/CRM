import api from '../api/client'

export async function downloadContractDocx(contractId: number) {
  const response = await api.get(`/contracts/${contractId}/download-docx`, {
    responseType: 'blob',
  })
  const disposition = response.headers['content-disposition'] as string | undefined
  let filename = 'договор.docx'
  if (disposition) {
    const match = /filename\*?=(?:UTF-8'')?["']?([^"';]+)/i.exec(disposition)
    if (match?.[1]) filename = decodeURIComponent(match[1])
  }
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export async function downloadDocument(docId: number, fallbackName = 'document') {
  const response = await api.get(`/documents/${docId}`, { responseType: 'blob' })
  const disposition = response.headers['content-disposition'] as string | undefined
  let filename = fallbackName
  if (disposition) {
    const match = /filename\*?=(?:UTF-8'')?["']?([^"';]+)/i.exec(disposition)
    if (match?.[1]) filename = decodeURIComponent(match[1])
  }
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export async function downloadAct(actId: number) {
  const response = await api.get(`/acts/${actId}/download`, { responseType: 'blob' })
  const disposition = response.headers['content-disposition'] as string | undefined
  let filename = 'akt.xlsx'
  if (disposition) {
    const match = /filename\*?=(?:UTF-8'')?["']?([^"';]+)/i.exec(disposition)
    if (match?.[1]) filename = decodeURIComponent(match[1])
  }
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export async function downloadInvoice(invoiceId: number) {
  const response = await api.get(`/invoices/${invoiceId}/download`, { responseType: 'blob' })
  const disposition = response.headers['content-disposition'] as string | undefined
  let filename = 'счет.xls'
  if (disposition) {
    const match = /filename\*?=(?:UTF-8'')?["']?([^"';]+)/i.exec(disposition)
    if (match?.[1]) filename = decodeURIComponent(match[1])
  }
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}
