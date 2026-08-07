import type { ReactNode } from 'react'
import './components.css'

export function MobileScreen({ children }: { children: ReactNode }) {
  return (
    <main className="app-canvas">
      <section className="mobile-screen">{children}</section>
    </main>
  )
}
