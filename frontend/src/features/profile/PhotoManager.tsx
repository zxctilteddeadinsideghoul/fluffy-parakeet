import { useId, useState } from 'react'
import type { ChangeEvent } from 'react'
import type { MyProfileView, ProfileService } from '../../services/profileService'
import './profile.css'

type PhotoManagerProps = {
  profileService: ProfileService
  view: MyProfileView
  onChanged: (next: MyProfileView) => void
}

/**
 * Photos are their own command flow (docs/CONTRACTS_DATA.md section 6): upload
 * and delete hit the server immediately rather than waiting for the form.
 */
export function PhotoManager({ profileService, view, onChanged }: PhotoManagerProps) {
  const inputId = useId()
  const [error, setError] = useState<string>()
  const [isBusy, setIsBusy] = useState(false)

  async function run(action: () => Promise<MyProfileView>, message: string) {
    setIsBusy(true)
    setError(undefined)
    try {
      onChanged(await action())
    } catch {
      setError(message)
    } finally {
      setIsBusy(false)
    }
  }

  function handleSelect(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (file) void run(() => profileService.uploadPhoto(file), 'Не удалось загрузить фото')
  }

  return (
    <section className="photo-manager">
      <span className="section-label">Фото</span>
      <p className="photo-manager__note">Фото сохраняются сразу, отдельно от остальных полей</p>

      {error && (
        <p className="photo-manager__error" role="alert">
          {error}
        </p>
      )}

      <ul className="photo-manager__grid">
        {view.profile.photos.map((photo) => (
          <li key={photo.id}>
            <img src={photo.url} alt="" />
            {photo.moderationStatus !== 'approved' && (
              <span className="photo-manager__badge">на модерации</span>
            )}
            <button
              type="button"
              disabled={isBusy}
              aria-label="Удалить фото"
              onClick={() => void run(() => profileService.deletePhoto(photo.id), 'Не удалось удалить фото')}
            >
              ×
            </button>
          </li>
        ))}
        <li className="photo-manager__add">
          <input
            id={inputId}
            type="file"
            accept="image/*"
            disabled={isBusy}
            onChange={handleSelect}
          />
          <label htmlFor={inputId}>Добавить</label>
        </li>
      </ul>
    </section>
  )
}
