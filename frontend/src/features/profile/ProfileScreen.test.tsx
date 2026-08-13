import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { createMockProfileService } from '../../services/profileService'
import { ProfileScreen } from './ProfileScreen'

const VENUE_LABEL = 'Вы в заведении · 1 ч 10 мин'

function renderProfile(overrides: Partial<Parameters<typeof ProfileScreen>[0]> = {}) {
  const onSignOut = vi.fn()
  render(
    <ProfileScreen
      profileService={createMockProfileService({ delayMs: 0 })}
      venueLabel={VENUE_LABEL}
      onNavigate={() => undefined}
      onSignOut={onSignOut}
      onEditProfile={() => undefined}
      {...overrides}
    />,
  )
  return { onSignOut }
}

describe('ProfileScreen', () => {
  it('shows the profile with its verification state', async () => {
    renderProfile()

    expect(await screen.findByRole('heading', { name: /Марина/ })).toBeInTheDocument()
    expect(screen.getByText('Верифицировано')).toBeInTheDocument()
    expect(screen.getByText('Селфи подтверждено 12 марта')).toBeInTheDocument()
  })

  it('treats the hide switch as the inverse of visibility', async () => {
    const user = userEvent.setup()
    renderProfile()

    const hideSwitch = await screen.findByRole('switch', { name: /Скрыться из списка/ })
    expect(hideSwitch).not.toBeChecked()

    await user.click(screen.getByText('Скрыться из списка'))
    expect(hideSwitch).toBeChecked()
  })

  it('restores the switch when the update fails', async () => {
    const user = userEvent.setup()
    renderProfile({
      profileService: createMockProfileService({ delayMs: 0, updateError: 'offline' }),
    })

    const hideSwitch = await screen.findByRole('switch', { name: /Скрыться из списка/ })
    await user.click(screen.getByText('Скрыться из списка'))

    expect(await screen.findByRole('alert')).toHaveTextContent('Не удалось изменить видимость')
    expect(hideSwitch).not.toBeChecked()
  })

  it('marks the visibility switch as a stub when the value is not server state', async () => {
    const service = createMockProfileService({ delayMs: 0 })
    const getMyProfile = service.getMyProfile.bind(service)
    renderProfile({
      profileService: {
        ...service,
        getMyProfile: async () => ({ ...(await getMyProfile()), isVisibilityStub: true }),
      },
    })

    // Scoped to the switch: the presence bar carries a stub tag of its own.
    const hideSwitch = await screen.findByRole('switch', { name: /Скрыться из списка/ })
    expect(hideSwitch.closest('label')).toHaveTextContent('заглушка')
    expect(screen.getByText(/не возвращает visibilityEnabled/)).toBeInTheDocument()
  })

  it('signs the user out', async () => {
    const user = userEvent.setup()
    const { onSignOut } = renderProfile()

    await user.click(await screen.findByRole('button', { name: 'Выйти из аккаунта' }))

    expect(onSignOut).toHaveBeenCalled()
  })

  it('reports a load failure', async () => {
    renderProfile({ profileService: createMockProfileService({ delayMs: 0, loadError: 'offline' }) })

    expect(await screen.findByRole('alert')).toHaveTextContent('Не удалось загрузить профиль')
  })
})
