import type { ButtonHTMLAttributes, ReactNode } from 'react'
import './components.css'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  isLoading?: boolean
  variant?: 'primary' | 'secondary' | 'text'
}

export function Button({
  children,
  className = '',
  disabled,
  isLoading = false,
  variant = 'primary',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button--${variant} ${className}`.trim()}
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? <span className="button__spinner" aria-hidden="true" /> : children}
      {isLoading && <span className="sr-only">Загрузка</span>}
    </button>
  )
}
