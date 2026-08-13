import { useState } from 'react'
import { MobileScreen } from './components/MobileScreen'
import { TabPlaceholder } from './components/TabPlaceholder'
import type { TabKey } from './components/TabBar'
import { SignInScreen } from './features/auth/SignInScreen'
import { SignUpScreen } from './features/auth/SignUpScreen'
import { ChatScreen } from './features/chats/ChatScreen'
import { ChatsScreen } from './features/chats/ChatsScreen'
import { OnboardingCompleteScreen } from './features/onboarding/OnboardingCompleteScreen'
import { ProfileSetupScreen } from './features/onboarding/ProfileSetupScreen'
import { ProfileEditScreen } from './features/profile/ProfileEditScreen'
import { ProfileScreen } from './features/profile/ProfileScreen'
import { DEV_USER_ID } from './services/apiClient'
import { mockAuthService } from './services/authService'
import type { ProfileDraft } from './services/authService'
import { httpChatService } from './services/chatService'
import type { ChatService, ConversationSummary } from './services/chatService'
import { httpProfileService } from './services/profileService'
import type { MyProfileView, ProfileService } from './services/profileService'

type AppView =
  | 'sign-in'
  | 'sign-up'
  | 'profile-setup'
  | 'complete'
  | 'venue'
  | 'people'
  | 'chats'
  | 'chat'
  | 'profile'
  | 'profile-edit'

const VENUE_LABEL = 'Вы в заведении · 1 ч 10 мин'

/** Services default to the real API; tests and stories inject their own. */
type AppProps = {
  chatService?: ChatService
  profileService?: ProfileService
  viewerUserId?: string
}

function App({
  chatService = httpChatService,
  profileService = httpProfileService,
  viewerUserId = DEV_USER_ID,
}: AppProps = {}) {
  const [view, setView] = useState<AppView>('sign-in')
  const [profile, setProfile] = useState<ProfileDraft>()
  const [conversation, setConversation] = useState<ConversationSummary>()
  const [profileView, setProfileView] = useState<MyProfileView>()

  function handleProfileComplete(nextProfile: ProfileDraft) {
    setProfile(nextProfile)
    setView('complete')
  }

  function handleSignOut() {
    setProfile(undefined)
    setConversation(undefined)
    setView('sign-in')
  }

  function handleNavigate(tab: TabKey) {
    setView(tab)
  }

  function handleOpenConversation(next: ConversationSummary) {
    setConversation(next)
    setView('chat')
  }

  return (
    <MobileScreen>
      {view === 'sign-in' && (
        <SignInScreen
          authService={mockAuthService}
          onCreateAccount={() => setView('sign-up')}
          onSuccess={() => setView('chats')}
        />
      )}
      {view === 'sign-up' && (
        <SignUpScreen
          authService={mockAuthService}
          onSignIn={() => setView('sign-in')}
          onSuccess={() => setView('profile-setup')}
        />
      )}
      {view === 'profile-setup' && <ProfileSetupScreen onSuccess={handleProfileComplete} />}
      {view === 'complete' && (
        <OnboardingCompleteScreen
          displayName={profile?.displayName ?? 'Ваш профиль'}
          onContinue={() => setView('chats')}
        />
      )}
      {view === 'venue' && (
        <TabPlaceholder title="Заведение" active="venue" onNavigate={handleNavigate} />
      )}
      {view === 'people' && (
        <TabPlaceholder title="Люди" active="people" onNavigate={handleNavigate} />
      )}
      {view === 'chats' && (
        <ChatsScreen
          chatService={chatService}
          viewerUserId={viewerUserId}
          venueLabel={VENUE_LABEL}
          onOpenConversation={handleOpenConversation}
          onOpenDrinkOffer={() => undefined}
          onNavigate={handleNavigate}
        />
      )}
      {view === 'chat' && conversation && (
        <ChatScreen
          chatService={chatService}
          conversation={conversation}
          viewerUserId={viewerUserId}
          onBack={() => setView('chats')}
        />
      )}
      {view === 'profile' && (
        <ProfileScreen
          profileService={profileService}
          venueLabel={VENUE_LABEL}
          onNavigate={handleNavigate}
          onSignOut={handleSignOut}
          onEditProfile={(next) => {
            setProfileView(next)
            setView('profile-edit')
          }}
          initialView={profileView}
        />
      )}
      {view === 'profile-edit' && profileView && (
        <ProfileEditScreen
          profileService={profileService}
          view={profileView}
          onCancel={() => setView('profile')}
          onPhotosChanged={setProfileView}
          onSaved={(next) => {
            setProfileView(next)
            setView('profile')
          }}
        />
      )}
    </MobileScreen>
  )
}

export default App
