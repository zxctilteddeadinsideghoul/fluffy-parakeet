import { useEffect, useId, useState } from 'react'
import './components.css'

type PhotoPickerProps = {
  value?: File
  onChange: (file?: File) => void
}

function CameraIcon() {
  return (
    <svg
      width="30"
      height="30"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M3 8.5h3.4L8 5.9h8l1.6 2.6H21V19H3z" />
      <circle cx="12" cy="13.4" r="3.9" />
    </svg>
  )
}

export function PhotoPicker({ onChange, value }: PhotoPickerProps) {
  const inputId = useId()
  const [previewUrl, setPreviewUrl] = useState<string>()

  useEffect(() => {
    if (!value) {
      setPreviewUrl(undefined)
      return
    }

    const objectUrl = URL.createObjectURL(value)
    setPreviewUrl(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [value])

  return (
    <div className="photo-picker">
      <input
        id={inputId}
        type="file"
        accept="image/*"
        onChange={(event) => onChange(event.target.files?.[0])}
      />
      <label htmlFor={inputId}>
        {previewUrl ? (
          <img src={previewUrl} alt="Предпросмотр выбранного фото" />
        ) : (
          <>
            <CameraIcon />
            <span>Добавить фото</span>
          </>
        )}
      </label>
      {value && (
        <button type="button" onClick={() => onChange(undefined)}>
          Удалить фото
        </button>
      )}
    </div>
  )
}
