import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '../../components/Button'
import { FormMessage } from '../../components/FormMessage'
import { GenderSelect } from '../../components/GenderSelect'
import type { GenderOption } from '../../components/GenderSelect'
import { TextField } from '../../components/TextField'
import { ChevronLeftIcon } from '../../components/icons'
import { PhotoManager } from './PhotoManager'
import type {
  ApproachMode,
  CommunicationGoal,
  MyProfileView,
  ProfileService,
} from '../../services/profileService'
import './profile.css'

type ProfileEditScreenProps = {
  profileService: ProfileService
  view: MyProfileView
  onCancel: () => void
  onSaved: (next: MyProfileView) => void
  /** Photos persist immediately, so the parent stays in sync without saving. */
  onPhotosChanged: (next: MyProfileView) => void
}

const GOALS: Array<{ value: CommunicationGoal; label: string }> = [
  { value: 'dating', label: 'Знакомства' },
  { value: 'friends', label: 'Дружба' },
  { value: 'company_tonight', label: 'Компания на вечер' },
  { value: 'networking', label: 'Нетворкинг' },
  { value: 'casual_chat', label: 'Просто поболтать' },
]

const APPROACH_MODES: Array<{ value: ApproachMode; label: string; hint: string }> = [
  { value: 'chat_only', label: 'Только переписка', hint: 'Подходить лично нельзя' },
  {
    value: 'ask_before_approach',
    label: 'Сначала спросить',
    hint: 'Нужно отдельное разрешение подойти',
  },
  { value: 'may_approach', label: 'Можно подойти', hint: 'Разрешение на текущий визит' },
]

const isGenderOption = (value: string | undefined): value is GenderOption =>
  value === 'female' || value === 'male'

export function ProfileEditScreen({
  profileService,
  view,
  onCancel,
  onSaved,
  onPhotosChanged,
}: ProfileEditScreenProps) {
  const { profile } = view
  const [displayName, setDisplayName] = useState(profile.displayName)
  // MyProfileDto returns `age`, never `birthDate`, so this cannot be prefilled.
  // PUT overwrites it unconditionally, hence it is required here.
  const [birthDate, setBirthDate] = useState('')
  const [gender, setGender] = useState<GenderOption>(
    isGenderOption(profile.gender) ? profile.gender : '',
  )
  const [bio, setBio] = useState(profile.bio ?? '')
  const [goals, setGoals] = useState<CommunicationGoal[]>(profile.communicationGoals)
  const [approachMode, setApproachMode] = useState<ApproachMode>(profile.defaultApproachMode)
  const [visible, setVisible] = useState(view.visibilityEnabled)
  const [errors, setErrors] = useState<{ displayName?: string; birthDate?: string }>({})
  const [saveError, setSaveError] = useState<string>()
  const [isSaving, setIsSaving] = useState(false)

  function toggleGoal(goal: CommunicationGoal) {
    setGoals((current) =>
      current.includes(goal) ? current.filter((item) => item !== goal) : [...current, goal],
    )
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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
    setSaveError(undefined)
    if (nextErrors.displayName || nextErrors.birthDate) return

    setIsSaving(true)
    try {
      onSaved(
        await profileService.updateMyProfile({
          displayName: displayName.trim(),
          gender: gender || undefined,
          bio: bio.trim() || undefined,
          birthDate,
          communicationGoals: goals,
          defaultApproachMode: approachMode,
          visibilityEnabled: visible,
        }),
      )
    } catch {
      setSaveError('Не удалось сохранить профиль')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="profile-edit accent-red">
      <header className="profile-edit__header">
        <button
          type="button"
          className="profile-edit__back"
          onClick={onCancel}
          aria-label="Назад к профилю"
        >
          <ChevronLeftIcon />
        </button>
        <h1>Редактирование</h1>
      </header>

      <PhotoManager profileService={profileService} view={view} onChanged={onPhotosChanged} />

      <form className="profile-edit__form" onSubmit={handleSubmit} noValidate>
        {saveError && <FormMessage>{saveError}</FormMessage>}

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
          hint="Профиль отдаёт только возраст, поэтому дату нужно ввести заново — иначе она сотрётся"
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
            maxLength={1000}
            onChange={(event) => setBio(event.target.value)}
            placeholder="Пара слов — что вы любите и о чём с вами легко заговорить"
          />
        </label>

        <fieldset className="chip-group">
          <legend>Цели общения</legend>
          <div className="chip-group__options">
            {GOALS.map(({ value, label }) => (
              <label key={value}>
                <input
                  type="checkbox"
                  checked={goals.includes(value)}
                  onChange={() => toggleGoal(value)}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="option-list">
          <legend>Личный подход</legend>
          {APPROACH_MODES.map(({ value, label, hint }) => (
            <label key={value}>
              <input
                type="radio"
                name="approach-mode"
                checked={approachMode === value}
                onChange={() => setApproachMode(value)}
              />
              <span className="option-list__text">
                <span className="option-list__label">{label}</span>
                <span className="option-list__hint">{hint}</span>
              </span>
            </label>
          ))}
        </fieldset>

        <label className="profile-toggle">
          <span className="profile-toggle__text">
            <span className="profile-toggle__heading">
              <span className="profile-toggle__title">Показывать меня в списке</span>
            </span>
            <span className="profile-toggle__hint">
              Текущее значение не приходит из API — выберите заново, оно сохранится вместе с
              профилем
            </span>
          </span>
          <input
            type="checkbox"
            role="switch"
            checked={visible}
            onChange={(event) => setVisible(event.target.checked)}
          />
          <span className="profile-toggle__track" aria-hidden="true">
            <span className="profile-toggle__thumb" />
          </span>
        </label>

        <div className="profile-edit__actions">
          <Button type="submit" isLoading={isSaving}>
            Сохранить
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSaving}>
            Отмена
          </Button>
        </div>
      </form>
    </div>
  )
}
