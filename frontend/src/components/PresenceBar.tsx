import { CheersIcon } from './icons'
import './components.css'

type PresenceBarProps = {
  venueLabel: string
  /**
   * The backend cannot answer «am I in a venue, and for how long» yet: there is
   * no GET for the viewer's own session, `PresenceSessionResponse` omits
   * `checkedInAt`, and no endpoint returns a venue name. Until then the label is
   * hardcoded and the bar says so.
   */
  isStub?: boolean
}

export function PresenceBar({ venueLabel, isStub = false }: PresenceBarProps) {
  return (
    <div className="presence-bar">
      <span className="presence-bar__pill">
        <span className="presence-bar__dot" aria-hidden="true" />
        {venueLabel}
        {isStub && <span className="stub-tag">заглушка</span>}
      </span>
      <span className="presence-bar__mark">
        <CheersIcon size={22} strokeWidth={1.7} />
      </span>
    </div>
  )
}
