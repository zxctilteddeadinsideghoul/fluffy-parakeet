import './components.css'

export type GenderOption = '' | 'female' | 'male'

type GenderSelectProps = {
  value: GenderOption
  onChange: (value: GenderOption) => void
}

const options: Array<{ value: Exclude<GenderOption, ''>; label: string }> = [
  { value: 'female', label: 'Женский' },
  { value: 'male', label: 'Мужской' },
]

export function GenderSelect({ onChange, value }: GenderSelectProps) {
  return (
    <fieldset className="gender-select">
      <legend>Пол</legend>
      <div className="gender-select__options">
        {options.map((option) => (
          <label key={option.value}>
            <input
              type="radio"
              name="gender"
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
