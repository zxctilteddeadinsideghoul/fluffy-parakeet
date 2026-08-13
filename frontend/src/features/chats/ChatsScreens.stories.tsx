import type { Meta, StoryObj } from '@storybook/react-vite'
import { MobileScreen } from '../../components/MobileScreen'
import { MOCK_VIEWER_USER_ID, createMockChatService } from '../../services/chatService'
import type { ConversationSummary } from '../../services/chatService'
import { ChatScreen } from './ChatScreen'
import { ChatsScreen } from './ChatsScreen'

const VENUE_LABEL = 'Вы в заведении · 1 ч 10 мин'

const marinaConversation: ConversationSummary = {
  conversation: {
    id: 'conv-marina',
    connectionId: 'conn-marina',
    status: 'active',
    peerUserId: 'user-marina',
    createdAt: new Date().toISOString(),
    lastMessageBody: 'Подходите',
    lastMessageAt: new Date().toISOString(),
    unreadCount: 2,
  },
  peer: { userId: 'user-marina', displayName: 'Марина', age: 27, isVerified: true },
  venueName: 'Гранёный',
}

const meta = {
  title: 'Screens/Chats',
  parameters: { layout: 'fullscreen' },
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const ChatList: Story = {
  render: () => (
    <MobileScreen>
      <ChatsScreen
        chatService={createMockChatService()}
        viewerUserId={MOCK_VIEWER_USER_ID}
        venueLabel={VENUE_LABEL}
        onOpenConversation={() => undefined}
        onOpenDrinkOffer={() => undefined}
        onNavigate={() => undefined}
      />
    </MobileScreen>
  ),
}

export const ChatListEmpty: Story = {
  render: () => (
    <MobileScreen>
      <ChatsScreen
        chatService={createMockChatService({ conversations: [], drinkOffers: [] })}
        viewerUserId={MOCK_VIEWER_USER_ID}
        venueLabel={VENUE_LABEL}
        onOpenConversation={() => undefined}
        onOpenDrinkOffer={() => undefined}
        onNavigate={() => undefined}
      />
    </MobileScreen>
  ),
}

export const ChatListError: Story = {
  render: () => (
    <MobileScreen>
      <ChatsScreen
        chatService={createMockChatService({ delayMs: 250, listError: 'offline' })}
        viewerUserId={MOCK_VIEWER_USER_ID}
        venueLabel={VENUE_LABEL}
        onOpenConversation={() => undefined}
        onOpenDrinkOffer={() => undefined}
        onNavigate={() => undefined}
      />
    </MobileScreen>
  ),
}

export const Conversation: Story = {
  render: () => (
    <MobileScreen>
      <ChatScreen
        chatService={createMockChatService()}
        conversation={marinaConversation}
        viewerUserId={MOCK_VIEWER_USER_ID}
        onBack={() => undefined}
      />
    </MobileScreen>
  ),
}

export const ConversationSendError: Story = {
  render: () => (
    <MobileScreen>
      <ChatScreen
        chatService={createMockChatService({ delayMs: 250, sendError: 'offline' })}
        conversation={marinaConversation}
        viewerUserId={MOCK_VIEWER_USER_ID}
        onBack={() => undefined}
      />
    </MobileScreen>
  ),
}
