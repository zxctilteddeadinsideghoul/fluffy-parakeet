import './components.css'

type AvatarProps = {
  name: string
  photoUrl?: string
  size?: 'sm' | 'md' | 'lg'
  muted?: boolean
}

export function Avatar({ name, photoUrl, size = 'md', muted = false }: AvatarProps) {
  const className = `avatar avatar--${size} ${muted ? 'avatar--muted' : ''}`.trim()

  if (photoUrl) {
    return <img className={className} src={photoUrl} alt="" />
  }

  return (
    <span className={className} aria-hidden="true">
      {name.trim().slice(0, 1).toUpperCase()}
    </span>
  )
}
