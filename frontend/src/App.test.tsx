import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import { MOCK_VIEWER_USER_ID, createMockChatService } from './services/chatService'
import { createMockProfileService } from './services/profileService'

/** App defaults to the real API; these tests cover navigation, not the network. */
function renderApp() {
  return render(
    <App
      chatService={createMockChatService({ delayMs: 0 })}
      profileService={createMockProfileService({ delayMs: 0 })}
      viewerUserId={MOCK_VIEWER_USER_ID}
    />,
  )
}

describe('authentication and onboarding flow', () => {
  it('registers, completes the profile, and opens the protected area', async () => {
    const user = userEvent.setup()
    renderApp()

    await user.click(screen.getByRole('button', { name: 'Зарегистрироваться' }))
    await user.click(screen.getByRole('button', { name: 'Продолжить' }))
    expect(screen.getByText('Введите email')).toBeInTheDocument()
    expect(screen.getByText('Введите пароль')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Email'), 'marina@example.com')
    await user.type(screen.getByLabelText('Пароль'), 'long-password')
    await user.type(screen.getByLabelText('Повторите пароль'), 'long-password')
    await user.click(screen.getByRole('button', { name: 'Продолжить' }))

    expect(await screen.findByRole('heading', { name: 'Расскажи о себе' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Имя'), 'Марина')
    fireEvent.change(screen.getByLabelText('Дата рождения'), {
      target: { value: '1999-03-14' },
    })
    await user.click(screen.getByText('Женский'))
    await user.click(screen.getByRole('button', { name: 'Продолжить' }))

    expect(screen.getByRole('heading', { name: /Готово!/ })).toBeInTheDocument()
    expect(screen.getByText(/аккаунт и анкета готовы/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Перейти в приложение' }))
    expect(screen.getByRole('heading', { name: 'Чаты' })).toBeInTheDocument()
  })

  it('signs in and signs out without persisting credentials', async () => {
    const user = userEvent.setup()
    renderApp()

    await user.type(screen.getByLabelText('Email'), 'user@example.com')
    await user.type(screen.getByLabelText('Пароль'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Войти' }))

    expect(await screen.findByRole('heading', { name: 'Чаты' })).toBeInTheDocument()
    expect(localStorage.length).toBe(0)

    await user.click(screen.getByRole('button', { name: 'Профиль' }))
    await user.click(await screen.findByRole('button', { name: 'Выйти из аккаунта' }))
    expect(screen.getByRole('heading', { name: 'Вход' })).toBeInTheDocument()
  })
})
