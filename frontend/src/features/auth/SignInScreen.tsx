import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '../../components/Button'
import { FormMessage } from '../../components/FormMessage'
import { TextField } from '../../components/TextField'
import type { AuthService } from '../../services/authService'
import { AuthLayout, LegalNotice } from './AuthLayout'
import { getServiceError, validateEmail, validatePassword } from './validation'

type SignInScreenProps = {
  authService: AuthService
  onCreateAccount: () => void
  onSuccess: () => void
}

export function SignInScreen({ authService, onCreateAccount, onSuccess }: SignInScreenProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({})
  const [serviceError, setServiceError] = useState<string>()
  const [isLoading, setIsLoading] = useState(false)
  const [recoveryNotice, setRecoveryNotice] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = {
      email: validateEmail(email),
      password: validatePassword(password),
    }
    setErrors(nextErrors)
    setServiceError(undefined)
    if (nextErrors.email || nextErrors.password) return

    setIsLoading(true)
    try {
      await authService.signIn({ email: email.trim(), password })
      onSuccess()
    } catch (error) {
      setServiceError(getServiceError(error))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Вход"
      subtitle="Войдите в аккаунт — и продолжим вечер"
      footer={
        <>
          <p className="auth-switch">
            Нет аккаунта?{' '}
            <button type="button" onClick={onCreateAccount}>
              Зарегистрироваться
            </button>
          </p>
          <LegalNotice />
        </>
      }
    >
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {serviceError && <FormMessage>{serviceError}</FormMessage>}
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          error={errors.email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <TextField
          label="Пароль"
          type="password"
          autoComplete="current-password"
          placeholder="Введите пароль"
          value={password}
          error={errors.password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" isLoading={isLoading}>
          Войти
        </Button>
        <Button
          type="button"
          variant="text"
          onClick={() => setRecoveryNotice(true)}
        >
          Забыли пароль?
        </Button>
        {recoveryNotice && (
          <p className="inline-notice" role="status">
            Восстановление пароля пока не подключено
          </p>
        )}
      </form>
    </AuthLayout>
  )
}
