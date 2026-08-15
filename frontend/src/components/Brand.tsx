import './components.css'

function CheersIcon({ size = 24 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <g transform="rotate(-16 10 12)">
        <path d="M6 7h8l-1 5.6a3 3 0 0 1-6 0z" />
        <path d="M10 13v5M7.6 18.4h4.8" />
      </g>
      <g transform="rotate(16 19 12)">
        <path d="M15 7h8l-1 5.6a3 3 0 0 1-6 0z" />
        <path d="M19 13v5M16.6 18.4h4.8" />
      </g>
    </svg>
  )
}

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
