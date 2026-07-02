/** Шаблоны наименования документа для таблицы №1 (можно дописать детали вручную). */
export interface DocumentPreset {
  /** Короткая подпись на кнопке */
  label: string
  /** Текст в поле «Наименование документа» */
  document_name: string
}

export const documentPresets: DocumentPreset[] = [
  {
    label: 'ГОСТ',
    document_name: 'Добровольный сертификат соответствия ГОСТ Р',
  },
  {
    label: 'Пожарная безопасность',
    document_name:
      'Добровольный сертификат соответствия требованиям пожарной безопасности',
  },
  {
    label: 'ИСО',
    document_name: 'Сертификат соответствия требованиям ИСО',
  },
  {
    label: 'Экспертное заключение',
    document_name: 'Экспертное заключение',
  },
  {
    label: 'Декларация ТР ТС',
    document_name: 'Декларация о соответствии требованиям ТР ТС',
  },
  {
    label: 'Сертификат ТР ТС',
    document_name: 'Сертификат соответствия требованиям ТР ТС',
  },
]

/** @deprecated используйте documentPresets */
export const documentNamePresets = documentPresets.map((p) => p.document_name)
