import { useId, useState } from 'react'
import type { InputHTMLAttributes } from 'react'
import './components.css'

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> & {
  label: string
  error?: string
  hint?: string
}

function EyeIcon({ crossed }: { crossed: boolean }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M3.5 12S7 6.5 12 6.5 20.5 12 20.5 12 17 17.5 12 17.5 3.5 12 3.5 12z" />
      <circle cx="12" cy="12" r="2.6" />
      {crossed && <path d="M4 4l16 16" />}
    </svg>
  )
}

export function TextField({
  error,
  hint,
  id,
  label,
  type = 'text',
  className = '',
  ...props
}: TextFieldProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const descriptionId = `${inputId}-description`
  const isPassword = type === 'password'
  const [passwordVisible, setPasswordVisible] = useState(false)

  return (
    <div className={`field ${error ? 'field--error' : ''} ${className}`.trim()}>
      <label className="field__label" htmlFor={inputId}>
        {label}
      </label>
      <div className="field__control">
        <input
          id={inputId}
          type={isPassword && passwordVisible ? 'text' : type}
          aria-invalid={Boolean(error)}
          aria-describedby={error || hint ? descriptionId : undefined}
          {...props}
        />
        {isPassword && (
          <button
            className="field__reveal"
            type="button"
            onClick={() => setPasswordVisible((visible) => !visible)}
            aria-label={passwordVisible ? 'Скрыть пароль' : 'Показать пароль'}
          >
            <EyeIcon crossed={passwordVisible} />
          </button>
        )}
      </div>
      {(error || hint) && (
        <span className="field__message" id={descriptionId}>
          {error ?? hint}
        </span>
      )}
    </div>
  )
}
