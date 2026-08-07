import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '../../components/Button'
import { FormMessage } from '../../components/FormMessage'
import { TextField } from '../../components/TextField'
import type { AuthService, RegistrationDraft } from '../../services/authService'
import { AuthLayout, LegalNotice } from './AuthLayout'
import { getServiceError, validateEmail, validatePassword } from './validation'

type SignUpScreenProps = {
  authService: AuthService
  onSignIn: () => void
  onSuccess: (draft: RegistrationDraft) => void
}

export function SignUpScreen({ authService, onSignIn, onSuccess }: SignUpScreenProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = useState('')
  const [errors, setErrors] = useState<{
    email?: string
    password?: string
    passwordConfirmation?: string
  }>({})
  const [serviceError, setServiceError] = useState<string>()
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = {
      email: validateEmail(email),
      password: validatePassword(password),
      passwordConfirmation:
        passwordConfirmation === password ? undefined : 'Пароли не совпадают',
    }
    if (!passwordConfirmation) nextErrors.passwordConfirmation = 'Повторите пароль'
    setErrors(nextErrors)
    setServiceError(undefined)
    if (nextErrors.email || nextErrors.password || nextErrors.passwordConfirmation) return

    setIsLoading(true)
    try {
      const draft = { email: email.trim(), password, passwordConfirmation }
      await authService.register(draft)
      onSuccess(draft)
    } catch (error) {
      setServiceError(getServiceError(error))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Создайте аккаунт"
      subtitle="Один шаг — и можно рассказать о себе"
      footer={
        <>
          <p className="auth-switch">
            Уже есть аккаунт?{' '}
            <button type="button" onClick={onSignIn}>
              Войти
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
          autoComplete="new-password"
          placeholder="Минимум 8 символов"
          value={password}
          error={errors.password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <TextField
          label="Повторите пароль"
          type="password"
          autoComplete="new-password"
          placeholder="Ещё раз"
          value={passwordConfirmation}
          error={errors.passwordConfirmation}
          onChange={(event) => setPasswordConfirmation(event.target.value)}
        />
        <Button type="submit" isLoading={isLoading}>
          Продолжить
        </Button>
      </form>
    </AuthLayout>
  )
}
