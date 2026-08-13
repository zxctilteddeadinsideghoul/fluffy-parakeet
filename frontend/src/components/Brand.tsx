import { CheersIcon } from './icons'
import './components.css'

export function Brand() {
  return (
    <div className="brand" aria-label="Чокнемся">
      <span className="brand__mark">
        <CheersIcon />
      </span>
      <span className="brand__name">Чокнемся</span>
    </div>
  )
}

export function SuccessMark() {
  return (
    <span className="success-mark" aria-hidden="true">
      <CheersIcon size={62} />
    </span>
  )
}
