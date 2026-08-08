import { useId } from 'react'
import './components.css'

export type GenderOption = '' | 'female' | 'male'

type GenderSelectProps = {
  value: GenderOption
  onChange: (value: GenderOption) => void
  error?: string
}

const options: Array<{ value: Exclude<GenderOption, ''>; label: string }> = [
  { value: 'female', label: 'Женский' },
  { value: 'male', label: 'Мужской' },
]

export function GenderSelect({ error, onChange, value }: GenderSelectProps) {
  const errorId = useId()

  return (
    <fieldset
      className={`gender-select ${error ? 'gender-select--error' : ''}`}
      aria-describedby={error ? errorId : undefined}
      aria-invalid={Boolean(error)}
    >
      <legend>Пол</legend>
      <div className="gender-select__options">
        {options.map((option) => (
          <label key={option.value}>
            <input
              type="radio"
              name="gender"
              value={option.value}
              checked={value === option.value}
              required
              onChange={() => onChange(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
      {error && (
        <span className="gender-select__message" id={errorId}>
          {error}
        </span>
      )}
    </fieldset>
  )
}
