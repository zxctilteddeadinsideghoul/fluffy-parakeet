import type { Meta, StoryObj } from '@storybook/react-vite'
import { MobileScreen } from '../../components/MobileScreen'
import { createMockAuthService } from '../../services/authService'
import { SignInScreen } from './SignInScreen'
import { SignUpScreen } from './SignUpScreen'

const meta = {
  title: 'Screens/Authentication',
  parameters: { layout: 'fullscreen' },
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const SignIn: Story = {
  render: () => (
    <MobileScreen>
      <SignInScreen
        authService={createMockAuthService()}
        onCreateAccount={() => undefined}
        onSuccess={() => undefined}
      />
    </MobileScreen>
  ),
}

export const SignInServiceError: Story = {
  render: () => (
    <MobileScreen>
      <SignInScreen
        authService={createMockAuthService({ delayMs: 250, signInError: 'Неверный email или пароль' })}
        onCreateAccount={() => undefined}
        onSuccess={() => undefined}
      />
    </MobileScreen>
  ),
}

export const SignUp: Story = {
  render: () => (
    <MobileScreen>
      <SignUpScreen
        authService={createMockAuthService()}
        onSignIn={() => undefined}
        onSuccess={() => undefined}
      />
    </MobileScreen>
  ),
}
