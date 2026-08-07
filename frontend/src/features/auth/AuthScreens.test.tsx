import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMockAuthService } from '../../services/authService'
import { SignInScreen } from './SignInScreen'

it('shows an injected authentication service error', async () => {
  const user = userEvent.setup()
  render(
    <SignInScreen
      authService={createMockAuthService({ delayMs: 0, signInError: 'Неверный email или пароль' })}
      onCreateAccount={() => undefined}
      onSuccess={() => undefined}
    />,
  )

  await user.type(screen.getByLabelText('Email'), 'user@example.com')
  await user.type(screen.getByLabelText('Пароль'), 'password123')
  await user.click(screen.getByRole('button', { name: 'Войти' }))

  expect(await screen.findByRole('alert')).toHaveTextContent('Неверный email или пароль')
})
