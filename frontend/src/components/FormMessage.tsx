import './components.css'

export function FormMessage({ children }: { children: string }) {
  return (
    <div className="form-message" role="alert">
      {children}
    </div>
  )
}
