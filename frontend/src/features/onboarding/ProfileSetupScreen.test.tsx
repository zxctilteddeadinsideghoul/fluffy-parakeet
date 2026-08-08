import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { ProfileSetupScreen } from './ProfileSetupScreen'

describe('ProfileSetupScreen', () => {
  it('requires gender before completing the profile', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()
    render(<ProfileSetupScreen onSuccess={onSuccess} />)

    await user.type(screen.getByLabelText('Имя'), 'Марина')
    fireEvent.change(screen.getByLabelText('Дата рождения'), {
      target: { value: '1999-03-14' },
    })
    await user.click(screen.getByRole('button', { name: 'Продолжить' }))

    expect(screen.getByText('Укажите пол')).toBeInTheDocument()
    expect(onSuccess).not.toHaveBeenCalled()

    await user.click(screen.getByText('Женский'))
    await user.click(screen.getByRole('button', { name: 'Продолжить' }))

    expect(onSuccess).toHaveBeenCalledWith(
      expect.objectContaining({ gender: 'female' }),
    )
  })
})
