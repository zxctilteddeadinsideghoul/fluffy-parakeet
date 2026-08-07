import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '../../components/Button'
import { GenderSelect } from '../../components/GenderSelect'
import type { GenderOption } from '../../components/GenderSelect'
import { PhotoPicker } from '../../components/PhotoPicker'
import { TextField } from '../../components/TextField'
import type { ProfileDraft } from '../../services/authService'
import './onboarding.css'

type ProfileSetupScreenProps = {
  onSuccess: (profile: ProfileDraft) => void
}

export function ProfileSetupScreen({ onSuccess }: ProfileSetupScreenProps) {
  const [displayName, setDisplayName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [gender, setGender] = useState<GenderOption>('')
  const [bio, setBio] = useState('')
  const [photo, setPhoto] = useState<File>()
  const [errors, setErrors] = useState<{ displayName?: string; birthDate?: string }>({})

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const today = new Date().toISOString().slice(0, 10)
    const nextErrors = {
      displayName: displayName.trim() ? undefined : 'Введите имя',
      birthDate: !birthDate
        ? 'Укажите дату рождения'
        : birthDate >= today
          ? 'Дата должна быть в прошлом'
          : undefined,
    }
    setErrors(nextErrors)
    if (nextErrors.displayName || nextErrors.birthDate) return

    onSuccess({
      displayName: displayName.trim(),
      birthDate,
      gender: gender || undefined,
      bio: bio.trim() || undefined,
      photo,
    })
  }

  return (
    <div className="profile-setup">
      <header className="profile-setup__heading">
        <h1>Расскажи о себе</h1>
        <p>Займёт меньше минуты</p>
      </header>
      <form onSubmit={handleSubmit} noValidate>
        <PhotoPicker value={photo} onChange={setPhoto} />
        <div className="profile-setup__fields">
          <TextField
            label="Имя"
            autoComplete="name"
            placeholder="Как вас зовут"
            value={displayName}
            error={errors.displayName}
            onChange={(event) => setDisplayName(event.target.value)}
          />
          <TextField
            label="Дата рождения"
            type="date"
            autoComplete="bday"
            value={birthDate}
            error={errors.birthDate}
            onChange={(event) => setBirthDate(event.target.value)}
          />
          <GenderSelect value={gender} onChange={setGender} />
          <label className="textarea-field">
            <span>
              О себе <small>по желанию</small>
            </span>
            <textarea
              rows={3}
              value={bio}
              onChange={(event) => setBio(event.target.value)}
              placeholder="Пара слов — что вы любите и о чём с вами легко заговорить"
            />
          </label>
        </div>
        <Button type="submit">Продолжить</Button>
      </form>
    </div>
  )
}
