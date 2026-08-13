const WEEKDAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']

const startOfDay = (date: Date) =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()

/** Short timestamp for a chat list row: «2 мин», «3 ч», «Вчера», «Пт», «14.03». */
export function formatChatTime(iso: string, now: Date = new Date()): string {
  const value = new Date(iso)
  if (Number.isNaN(value.getTime())) return ''

  const minutes = Math.floor((now.getTime() - value.getTime()) / 60_000)
  if (minutes < 1) return 'сейчас'
  if (minutes < 60) return `${minutes} мин`

  const days = Math.round((startOfDay(now) - startOfDay(value)) / 86_400_000)
  if (days === 0) return `${Math.floor(minutes / 60)} ч`
  if (days === 1) return 'Вчера'
  if (days < 7) return WEEKDAYS[value.getDay()]

  return value.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
}
