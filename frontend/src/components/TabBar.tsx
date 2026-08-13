import { ChatsIcon, PeopleIcon, ProfileIcon, VenueIcon } from './icons'
import './components.css'

export type TabKey = 'venue' | 'people' | 'chats' | 'profile'

type TabBarProps = {
  active: TabKey
  onNavigate: (tab: TabKey) => void
}

const TABS: Array<{ key: TabKey; label: string; Icon: typeof VenueIcon }> = [
  { key: 'venue', label: 'Заведение', Icon: VenueIcon },
  { key: 'people', label: 'Люди', Icon: PeopleIcon },
  { key: 'chats', label: 'Чаты', Icon: ChatsIcon },
  { key: 'profile', label: 'Профиль', Icon: ProfileIcon },
]

export function TabBar({ active, onNavigate }: TabBarProps) {
  return (
    <nav className="tab-bar" aria-label="Основные разделы">
      {TABS.map(({ key, label, Icon }) => {
        const isActive = key === active
        return (
          <button
            key={key}
            type="button"
            className={`tab-bar__tab ${isActive ? 'tab-bar__tab--active' : ''}`.trim()}
            aria-current={isActive ? 'page' : undefined}
            onClick={() => onNavigate(key)}
          >
            <Icon strokeWidth={isActive ? 2.1 : 1.8} />
            <span>{label}</span>
          </button>
        )
      })}
    </nav>
  )
}
