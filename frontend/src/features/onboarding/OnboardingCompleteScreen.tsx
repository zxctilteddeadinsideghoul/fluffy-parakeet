import { SuccessMark } from '../../components/Brand'
import { Button } from '../../components/Button'
import './onboarding.css'

type OnboardingCompleteScreenProps = {
  displayName: string
  onContinue: () => void
}

export function OnboardingCompleteScreen({
  displayName,
  onContinue,
}: OnboardingCompleteScreenProps) {
  return (
    <div className="onboarding-complete">
      <div className="onboarding-complete__content">
        <SuccessMark />
        <div>
          <h1>Готово!<br />Найди заведение</h1>
          <p>
            {displayName}, аккаунт и анкета готовы. Теперь выберите место, где хотите
            познакомиться с людьми рядом.
          </p>
        </div>
      </div>
      <div className="onboarding-complete__action">
        <Button type="button" onClick={onContinue}>
          Перейти в приложение
        </Button>
      </div>
    </div>
  )
}
