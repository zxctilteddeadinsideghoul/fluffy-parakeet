import type { Meta, StoryObj } from '@storybook/react-vite'
import { MobileScreen } from '../../components/MobileScreen'
import { OnboardingCompleteScreen } from './OnboardingCompleteScreen'
import { ProfileSetupScreen } from './ProfileSetupScreen'
import { ProtectedPlaceholder } from './ProtectedPlaceholder'

const meta = {
  title: 'Screens/Onboarding',
  parameters: { layout: 'fullscreen' },
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const ProfileSetup: Story = {
  render: () => (
    <MobileScreen>
      <ProfileSetupScreen onSuccess={() => undefined} />
    </MobileScreen>
  ),
}

export const Complete: Story = {
  render: () => (
    <MobileScreen>
      <OnboardingCompleteScreen displayName="Марина" onContinue={() => undefined} />
    </MobileScreen>
  ),
}

export const ProtectedArea: Story = {
  render: () => (
    <MobileScreen>
      <ProtectedPlaceholder displayName="Марина" onSignOut={() => undefined} />
    </MobileScreen>
  ),
}
