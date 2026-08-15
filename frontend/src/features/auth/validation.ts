const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateEmail(email: string) {
  if (!email.trim()) return 'Введите email'
  if (!emailPattern.test(email)) return 'Проверьте формат email'
  return undefined
}

export function validatePassword(password: string) {
  if (!password) return 'Введите пароль'
  if (password.length < 8) return 'Минимум 8 символов'
  return undefined
}

export function getServiceError(error: unknown) {
  if (error instanceof Error && error.message) return error.message
  return 'Не удалось выполнить запрос. Попробуйте ещё раз'
}
