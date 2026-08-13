import { useEffect, useState } from 'react'
import { Avatar } from '../../components/Avatar'
import { FormMessage } from '../../components/FormMessage'
import { PresenceBar } from '../../components/PresenceBar'
import { TabBar } from '../../components/TabBar'
import type { TabKey } from '../../components/TabBar'
import { ChevronRightIcon, PencilIcon, VerifiedIcon } from '../../components/icons'
import type { MyProfileView, ProfileService } from '../../services/profileService'
import './profile.css'

type ProfileScreenProps = {
  profileService: ProfileService
  venueLabel: string
  onNavigate: (tab: TabKey) => void
  onSignOut: () => void
  onEditProfile: (view: MyProfileView) => void
  /** Lets the parent hand back a view already refreshed by the edit screen. */
  initialView?: MyProfileView
}

const SETTINGS = [
  'Уведомления',
  'Кто может меня видеть',
  'Условия и конфиденциальность',
  'Связаться с нами',
]

function formatVerifiedAt(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return undefined
  return `Селфи подтверждено ${date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
  })}`
}

export function ProfileScreen({
  profileService,
  venueLabel,
  onNavigate,
  onSignOut,
  onEditProfile,
  initialView,
}: ProfileScreenProps) {
  const [view, setView] = useState<MyProfileView | undefined>(initialView)
  const [loadError, setLoadError] = useState<string>()
  const [updateError, setUpdateError] = useState<string>()
  const [isUpdating, setIsUpdating] = useState(false)
  const [comingSoon, setComingSoon] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoadError(undefined)
      try {
        const nextView = await profileService.getMyProfile()
        if (!cancelled) setView(nextView)
      } catch {
        if (!cancelled) setLoadError('Не удалось загрузить профиль')
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [profileService])

  async function handleHiddenChange(hidden: boolean) {
    if (!view || isUpdating) return
    setIsUpdating(true)
    setUpdateError(undefined)
    const previous = view
    setView({ ...view, visibilityEnabled: !hidden })
    try {
      setView(await profileService.setVisibilityEnabled(!hidden))
    } catch {
      setView(previous)
      setUpdateError('Не удалось изменить видимость')
    } finally {
      setIsUpdating(false)
    }
  }

  if (loadError) {
    return (
      <div className="profile-screen accent-red">
        <PresenceBar venueLabel={venueLabel} isStub />
        <div className="profile-screen__content">
          <FormMessage>{loadError}</FormMessage>
        </div>
        <TabBar active="profile" onNavigate={onNavigate} />
      </div>
    )
  }

  if (!view) {
    return (
      <div className="profile-screen accent-red">
        <PresenceBar venueLabel={venueLabel} isStub />
        <div className="profile-screen__content">
          <p className="profile-screen__status" role="status">
            Загружаем профиль…
          </p>
        </div>
        <TabBar active="profile" onNavigate={onNavigate} />
      </div>
    )
  }

  const { profile, visibilityEnabled, isVisibilityStub, verifiedAt } = view
  const verifiedNote = verifiedAt ? formatVerifiedAt(verifiedAt) : undefined

  return (
    <div className="profile-screen accent-red">
      <PresenceBar venueLabel={venueLabel} isStub />

      <div className="profile-screen__content">
        <section className="profile-identity">
          <div className="profile-identity__top">
            <Avatar
              name={profile.displayName}
              photoUrl={profile.photos[0]?.url}
              size="lg"
              muted
            />
            <div className="profile-identity__meta">
              <h1 className="profile-identity__name">
                {profile.displayName}
                {profile.age != null && (
                  <span className="profile-identity__age">{profile.age}</span>
                )}
                {profile.verification.isVerified && (
                  <span className="profile-identity__verified">
                    <VerifiedIcon size={17} />
                    <span className="sr-only">Профиль верифицирован</span>
                  </span>
                )}
              </h1>
              <button
                type="button"
                className="profile-identity__edit"
                onClick={() => onEditProfile(view)}
              >
                <PencilIcon />
                Редактировать
              </button>
            </div>
          </div>
          {profile.bio && <p className="profile-identity__bio">{profile.bio}</p>}
        </section>

        <section className="profile-section">
          <span className="section-label">Приватность и видимость</span>

          {updateError && <FormMessage>{updateError}</FormMessage>}

          <label className="profile-toggle">
            <span className="profile-toggle__text">
              <span className="profile-toggle__heading">
                <span className="profile-toggle__title">Скрыться из списка</span>
                {isVisibilityStub && <span className="stub-tag">заглушка</span>}
              </span>
              <span className="profile-toggle__hint">
                {isVisibilityStub
                  ? 'Переключатель не сохраняется: GET /me/profile не возвращает visibilityEnabled'
                  : 'Вас не будет видно, даже если вы в заведении'}
              </span>
            </span>
            <input
              type="checkbox"
              role="switch"
              checked={!visibilityEnabled}
              disabled={isUpdating}
              onChange={(event) => handleHiddenChange(event.target.checked)}
            />
            <span className="profile-toggle__track" aria-hidden="true">
              <span className="profile-toggle__thumb" />
            </span>
          </label>

          {profile.verification.isVerified && (
            <div className="profile-card">
              <span className="profile-card__icon">
                <VerifiedIcon size={22} />
              </span>
              <span className="profile-card__text">
                <span className="profile-card__title">Верифицировано</span>
                {verifiedNote && <span className="profile-card__hint">{verifiedNote}</span>}
              </span>
            </div>
          )}
        </section>

        <section className="profile-section profile-section--tight">
          <span className="section-label">Настройки</span>
          {SETTINGS.map((label) => (
            <button
              key={label}
              type="button"
              className="profile-link"
              onClick={() => setComingSoon(true)}
            >
              <span>{label}</span>
              <ChevronRightIcon />
            </button>
          ))}
        </section>

        {comingSoon && (
          <p className="profile-screen__notice" role="status">
            Раздел пока не подключён
          </p>
        )}

        <button type="button" className="profile-signout" onClick={onSignOut}>
          Выйти из аккаунта
        </button>
      </div>

      <TabBar active="profile" onNavigate={onNavigate} />
    </div>
  )
}
