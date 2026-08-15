import { Brand } from '../../components/Brand'
import { Button } from '../../components/Button'
import './onboarding.css'

type ProtectedPlaceholderProps = {
  displayName?: string
  onSignOut: () => void
}

export function ProtectedPlaceholder({ displayName, onSignOut }: ProtectedPlaceholderProps) {
  return (
    <div className="protected-placeholder">
      <Brand />
      <div className="protected-placeholder__content">
        <span className="protected-placeholder__eyebrow">Вы вошли</span>
        <h1>{displayName ? `${displayName}, всё готово` : 'Добро пожаловать'}</h1>
        <p>Основной экран приложения появится здесь в следующей итерации.</p>
      </div>
      <Button type="button" variant="secondary" onClick={onSignOut}>
        Выйти
      </Button>
    </div>
  )
}
