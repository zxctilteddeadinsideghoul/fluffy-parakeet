import { TabBar } from './TabBar'
import type { TabKey } from './TabBar'
import './components.css'

type TabPlaceholderProps = {
  title: string
  active: TabKey
  onNavigate: (tab: TabKey) => void
}

/** Stands in for the tabs owned by the venue and discovery branches. */
export function TabPlaceholder({ title, active, onNavigate }: TabPlaceholderProps) {
  return (
    <div className="tab-placeholder accent-red">
      <div className="tab-placeholder__content">
        <h1>{title}</h1>
        <p>Этот раздел появится в следующей итерации.</p>
      </div>
      <TabBar active={active} onNavigate={onNavigate} />
    </div>
  )
}
