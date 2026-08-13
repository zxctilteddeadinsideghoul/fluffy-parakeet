import type { Meta, StoryObj } from '@storybook/react-vite'
import { MobileScreen } from '../../components/MobileScreen'
import { createMockProfileService } from '../../services/profileService'
import { ProfileScreen } from './ProfileScreen'

const VENUE_LABEL = 'Вы в заведении · 1 ч 10 мин'

const meta = {
  title: 'Screens/Profile',
  parameters: { layout: 'fullscreen' },
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const Visible: Story = {
  render: () => (
    <MobileScreen>
      <ProfileScreen
        profileService={createMockProfileService()}
        venueLabel={VENUE_LABEL}
        onNavigate={() => undefined}
        onSignOut={() => undefined}
        onEditProfile={() => undefined}
      />
    </MobileScreen>
  ),
}

export const Hidden: Story = {
  render: () => (
    <MobileScreen>
      <ProfileScreen
        profileService={createMockProfileService({ visibilityEnabled: false })}
        venueLabel={VENUE_LABEL}
        onNavigate={() => undefined}
        onSignOut={() => undefined}
        onEditProfile={() => undefined}
      />
    </MobileScreen>
  ),
}

export const LoadError: Story = {
  render: () => (
    <MobileScreen>
      <ProfileScreen
        profileService={createMockProfileService({ delayMs: 250, loadError: 'offline' })}
        venueLabel={VENUE_LABEL}
        onNavigate={() => undefined}
        onSignOut={() => undefined}
        onEditProfile={() => undefined}
      />
    </MobileScreen>
  ),
}
