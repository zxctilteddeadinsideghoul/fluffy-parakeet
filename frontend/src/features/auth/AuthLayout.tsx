import type { ReactNode } from 'react'
import { Brand } from '../../components/Brand'
import './auth.css'

type AuthLayoutProps = {
  title: string
  subtitle: string
  children: ReactNode
  footer?: ReactNode
}

export function AuthLayout({ children, footer, subtitle, title }: AuthLayoutProps) {
  return (
    <div className="auth-layout">
      <header className="auth-layout__brand">
        <Brand />
      </header>
      <div className="auth-layout__heading">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <div className="auth-layout__body">{children}</div>
      {footer && <footer className="auth-layout__footer">{footer}</footer>}
    </div>
  )
}

export function LegalNotice() {
  return (
    <p className="legal-notice">
      Продолжая, вы соглашаетесь с условиями использования и политикой конфиденциальности
    </p>
  )
}
