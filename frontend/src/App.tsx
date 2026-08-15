import { useState } from 'react'
import { MobileScreen } from './components/MobileScreen'
import { SignInScreen } from './features/auth/SignInScreen'
import { SignUpScreen } from './features/auth/SignUpScreen'
import { OnboardingCompleteScreen } from './features/onboarding/OnboardingCompleteScreen'
import { ProfileSetupScreen } from './features/onboarding/ProfileSetupScreen'
import { ProtectedPlaceholder } from './features/onboarding/ProtectedPlaceholder'
import { mockAuthService } from './services/authService'
import type { ProfileDraft } from './services/authService'

type AppView = 'sign-in' | 'sign-up' | 'profile' | 'complete' | 'protected'

function App() {
  const [view, setView] = useState<AppView>('sign-in')
  const [profile, setProfile] = useState<ProfileDraft>()

  function handleProfileComplete(nextProfile: ProfileDraft) {
    setProfile(nextProfile)
    setView('complete')
  }

  function handleSignOut() {
    setProfile(undefined)
    setView('sign-in')
  }

  return (
    <MobileScreen>
      {view === 'sign-in' && (
        <SignInScreen
          authService={mockAuthService}
          onCreateAccount={() => setView('sign-up')}
          onSuccess={() => setView('protected')}
        />
      )}
      {view === 'sign-up' && (
        <SignUpScreen
          authService={mockAuthService}
          onSignIn={() => setView('sign-in')}
          onSuccess={() => setView('profile')}
        />
      )}
      {view === 'profile' && <ProfileSetupScreen onSuccess={handleProfileComplete} />}
      {view === 'complete' && (
        <OnboardingCompleteScreen
          displayName={profile?.displayName ?? 'Ваш профиль'}
          onContinue={() => setView('protected')}
        />
      )}
      {view === 'protected' && (
        <ProtectedPlaceholder displayName={profile?.displayName} onSignOut={handleSignOut} />
      )}
    </MobileScreen>
  )
}

export default App
