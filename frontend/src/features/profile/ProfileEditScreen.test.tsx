import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { createMockProfileService } from '../../services/profileService'
import type { MyProfileView, ProfileService } from '../../services/profileService'
import { ProfileEditScreen } from './ProfileEditScreen'

const view: MyProfileView = {
  profile: {
    id: 'user-me',
    displayName: 'Марина',
    age: 27,
    gender: 'female',
    bio: 'Здесь с подругой',
    communicationGoals: ['dating'],
    defaultApproachMode: 'ask_before_approach',
    photos: [
      { id: 'photo-1', url: 'blob:one', position: 1, moderationStatus: 'approved' },
    ],
    verification: { isVerified: true },
  },
  visibilityEnabled: true,
  isVisibilityStub: true,
}

function renderEdit(service: ProfileService = createMockProfileService({ delayMs: 0 })) {
  const onSaved = vi.fn()
  const onCancel = vi.fn()
  const onPhotosChanged = vi.fn()
  render(
    <ProfileEditScreen
      profileService={service}
      view={view}
      onSaved={onSaved}
      onCancel={onCancel}
      onPhotosChanged={onPhotosChanged}
    />,
  )
  return { onSaved, onCancel, onPhotosChanged }
}

describe('ProfileEditScreen', () => {
  it('prefills everything the profile DTO returns', () => {
    renderEdit()

    expect(screen.getByLabelText('Имя')).toHaveValue('Марина')
    expect(screen.getByLabelText(/О себе/)).toHaveValue('Здесь с подругой')
    expect(screen.getByRole('checkbox', { name: 'Знакомства' })).toBeChecked()
    expect(screen.getByRole('radio', { name: /Сначала спросить/ })).toBeChecked()
  })

  it('refuses to save without a birth date, because PUT would wipe the stored one', async () => {
    const user = userEvent.setup()
    const { onSaved } = renderEdit()

    expect(screen.getByLabelText('Дата рождения')).toHaveValue('')
    await user.click(screen.getByRole('button', { name: 'Сохранить' }))

    expect(screen.getByText('Укажите дату рождения')).toBeInTheDocument()
    expect(onSaved).not.toHaveBeenCalled()
  })

  it('sends the whole command and reports the saved view', async () => {
    const user = userEvent.setup()
    const service = createMockProfileService({ delayMs: 0 })
    const updateMyProfile = vi.spyOn(service, 'updateMyProfile')
    const { onSaved } = renderEdit(service)

    await user.clear(screen.getByLabelText('Имя'))
    await user.type(screen.getByLabelText('Имя'), 'Марина К.')
    fireEvent.change(screen.getByLabelText('Дата рождения'), {
      target: { value: '1999-03-14' },
    })
    await user.click(screen.getByText('Нетворкинг'))
    await user.click(screen.getByText('Можно подойти'))
    await user.click(screen.getByRole('button', { name: 'Сохранить' }))

    expect(updateMyProfile).toHaveBeenCalledWith({
      displayName: 'Марина К.',
      gender: 'female',
      bio: 'Здесь с подругой',
      birthDate: '1999-03-14',
      communicationGoals: ['dating', 'networking'],
      defaultApproachMode: 'may_approach',
      visibilityEnabled: true,
    })
    expect(onSaved).toHaveBeenCalled()
  })

  it('keeps the user on the form when saving fails', async () => {
    const user = userEvent.setup()
    const { onSaved } = renderEdit(
      createMockProfileService({ delayMs: 0, updateError: 'offline' }),
    )

    fireEvent.change(screen.getByLabelText('Дата рождения'), {
      target: { value: '1999-03-14' },
    })
    await user.click(screen.getByRole('button', { name: 'Сохранить' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Не удалось сохранить профиль')
    expect(onSaved).not.toHaveBeenCalled()
  })

  it('deletes a photo straight away, without waiting for the form', async () => {
    const user = userEvent.setup()
    const service = createMockProfileService({ delayMs: 0 })
    const deletePhoto = vi.spyOn(service, 'deletePhoto')
    const { onPhotosChanged, onSaved } = renderEdit(service)

    await user.click(screen.getByRole('button', { name: 'Удалить фото' }))

    expect(deletePhoto).toHaveBeenCalledWith('photo-1')
    expect(onPhotosChanged).toHaveBeenCalled()
    expect(onSaved).not.toHaveBeenCalled()
  })
})
