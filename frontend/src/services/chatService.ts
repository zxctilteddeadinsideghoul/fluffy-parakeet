/**
 * Communication context client types (docs/CONTRACTS_DATA.md, sections 3–5).
 *
 * The DTOs below mirror the backend responses one-to-one. The `*Summary` types
 * are client-side view models: `ConversationDto` and `DrinkOfferDto` carry only
 * `peerUserId` / `senderUserId`, so the display name of the other person has to
 * be joined from the discovery DTO on the client. No field is added to a DTO.
 */

import { apiRequest } from './apiClient'

export type ConversationStatus = 'active' | 'closed' | 'blocked'
export type MessageType = 'text' | 'system'

export type DrinkOfferStatus =
  | 'payment_authorized'
  | 'pending'
  | 'accepted'
  | 'declined'
  | 'expired'
  | 'cancelled'
  | 'redeemed'

export type MoneyDto = {
  amountMinor: number
  currency: string
}

export type ConversationDto = {
  id: string
  connectionId: string
  status: ConversationStatus
  peerUserId: string
  createdAt: string
  lastMessageBody?: string | null
  lastMessageAt?: string | null
  unreadCount: number
}

export type MessageDto = {
  id: string
  conversationId: string
  senderUserId: string
  type: MessageType
  body: string
  createdAt: string
}

export type MessagesPageDto = {
  items: MessageDto[]
  nextCursor: string | null
}

export type DrinkOfferDto = {
  id: string
  senderUserId: string
  recipientUserId: string
  senderPresenceId: string
  recipientPresenceId: string
  venueId: string
  menuItemId: string
  connectionId?: string
  status: DrinkOfferStatus
  itemNameSnapshot: string
  priceSnapshot: MoneyDto
  createdAt: string
  respondedAt?: string | null
  expiresAt: string
}

/** Subset of `VisibleProfileDto` needed to render a row (contract section 5). */
export type ChatPeer = {
  userId: string
  displayName: string
  age: number | null
  isVerified: boolean
  photoUrl?: string
}

export type ConversationSummary = {
  conversation: ConversationDto
  peer: ChatPeer | null
  /**
   * Venue name for the «вы познакомились в …» strip. Not part of any current
   * DTO — the conversation only reaches the venue through its connection.
   */
  venueName?: string
}

export type DrinkOfferSummary = {
  offer: DrinkOfferDto
  peer: ChatPeer | null
}

export interface ChatService {
  listConversations(): Promise<ConversationSummary[]>
  listDrinkOffers(): Promise<DrinkOfferSummary[]>
  listMessages(conversationId: string): Promise<MessagesPageDto>
  sendMessage(conversationId: string, body: string): Promise<MessageDto>
}

export class ChatServiceError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ChatServiceError'
  }
}

/**
 * Talks to the real backend.
 *
 * `peer` is always `null`: neither `ConversationDto` nor `DrinkOfferDto` carries
 * the other person's display name, and the only endpoint that does
 * (`GET /venues/{venueId}/profiles`) needs an active presence session of your
 * own and lists only people who are in the venue right now — so it cannot name
 * the peers of older conversations. The UI renders a visible placeholder until
 * the contract gains `peerDisplayName`.
 */
export function createHttpChatService(): ChatService {
  return {
    async listConversations() {
      const items = await apiRequest<ConversationDto[]>('/me/conversations')
      return items.map((conversation) => ({ conversation, peer: null }))
    },
    async listDrinkOffers() {
      const items = await apiRequest<DrinkOfferDto[]>('/me/drink-offers')
      return items.map((offer) => ({ offer, peer: null }))
    },
    async listMessages(conversationId) {
      return apiRequest<MessagesPageDto>(
        `/me/conversations/${encodeURIComponent(conversationId)}/messages`,
      )
    },
    async sendMessage(conversationId, body) {
      return apiRequest<MessageDto>(
        `/me/conversations/${encodeURIComponent(conversationId)}/messages`,
        { method: 'POST', body: JSON.stringify({ body }) },
      )
    },
  }
}

export const httpChatService = createHttpChatService()

export const MOCK_VIEWER_USER_ID = 'user-me'

const wait = (delayMs: number) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, delayMs))

const minutesAgo = (minutes: number) =>
  new Date(Date.now() - minutes * 60_000).toISOString()

const MOCK_PEERS: Record<string, ChatPeer> = {
  'user-marina': { userId: 'user-marina', displayName: 'Марина', age: 27, isVerified: true },
  'user-anya': { userId: 'user-anya', displayName: 'Аня', age: 24, isVerified: true },
  'user-nika': { userId: 'user-nika', displayName: 'Ника', age: 28, isVerified: false },
  'user-ilya': { userId: 'user-ilya', displayName: 'Илья', age: 30, isVerified: true },
  'user-kirill': { userId: 'user-kirill', displayName: 'Кирилл', age: 26, isVerified: false },
  'user-dasha': { userId: 'user-dasha', displayName: 'Даша', age: 23, isVerified: true },
}

const MOCK_CONVERSATIONS: ConversationSummary[] = [
  {
    conversation: {
      id: 'conv-marina',
      connectionId: 'conn-marina',
      status: 'active',
      peerUserId: 'user-marina',
      createdAt: minutesAgo(70),
      lastMessageBody: 'Подходите',
      lastMessageAt: minutesAgo(2),
      unreadCount: 2,
    },
    peer: MOCK_PEERS['user-marina'],
    venueName: 'Гранёный',
  },
  {
    conversation: {
      id: 'conv-anya',
      connectionId: 'conn-anya',
      status: 'active',
      peerUserId: 'user-anya',
      createdAt: minutesAgo(60 * 30),
      lastMessageBody: 'Тогда до завтра — здесь же',
      lastMessageAt: minutesAgo(60 * 26),
      unreadCount: 0,
    },
    peer: MOCK_PEERS['user-anya'],
  },
  {
    conversation: {
      id: 'conv-nika',
      connectionId: 'conn-nika',
      status: 'active',
      peerUserId: 'user-nika',
      createdAt: minutesAgo(60 * 24 * 6),
      lastMessageBody: 'Спасибо за вечер',
      lastMessageAt: minutesAgo(60 * 24 * 5),
      unreadCount: 0,
    },
    peer: MOCK_PEERS['user-nika'],
  },
]

const drinkOffer = (
  id: string,
  senderUserId: string,
  recipientUserId: string,
  createdMinutesAgo: number,
): DrinkOfferDto => ({
  id,
  senderUserId,
  recipientUserId,
  senderPresenceId: `presence-${senderUserId}`,
  recipientPresenceId: `presence-${recipientUserId}`,
  venueId: 'venue-granyony',
  menuItemId: 'menu-negroni',
  status: 'pending',
  itemNameSnapshot: 'Негрони',
  priceSnapshot: { amountMinor: 90000, currency: 'RUB' },
  createdAt: minutesAgo(createdMinutesAgo),
  expiresAt: minutesAgo(createdMinutesAgo - 60),
})

const MOCK_DRINK_OFFERS: DrinkOfferSummary[] = [
  {
    offer: drinkOffer('offer-ilya', 'user-ilya', MOCK_VIEWER_USER_ID, 5),
    peer: MOCK_PEERS['user-ilya'],
  },
  {
    offer: drinkOffer('offer-kirill', 'user-kirill', MOCK_VIEWER_USER_ID, 18),
    peer: MOCK_PEERS['user-kirill'],
  },
  {
    offer: drinkOffer('offer-dasha', MOCK_VIEWER_USER_ID, 'user-dasha', 32),
    peer: MOCK_PEERS['user-dasha'],
  },
]

const MOCK_MESSAGES: Record<string, MessageDto[]> = {
  'conv-marina': [
    {
      id: 'msg-1',
      conversationId: 'conv-marina',
      senderUserId: 'user-marina',
      type: 'system',
      body: 'Марина приняла ваш напиток',
      createdAt: minutesAgo(64),
    },
    {
      id: 'msg-2',
      conversationId: 'conv-marina',
      senderUserId: MOCK_VIEWER_USER_ID,
      type: 'text',
      body: 'Надеюсь, игристое здесь приличное. Я за столиком у окна',
      createdAt: minutesAgo(24),
    },
    {
      id: 'msg-3',
      conversationId: 'conv-marina',
      senderUserId: 'user-marina',
      type: 'text',
      body: 'Вполне! Спасибо — а вы тот, кто спорил с барменом о музыке?',
      createdAt: minutesAgo(18),
    },
    {
      id: 'msg-4',
      conversationId: 'conv-marina',
      senderUserId: MOCK_VIEWER_USER_ID,
      type: 'text',
      body: 'Он первый начал. Можно подойду?',
      createdAt: minutesAgo(9),
    },
    {
      id: 'msg-5',
      conversationId: 'conv-marina',
      senderUserId: 'user-marina',
      type: 'text',
      body: 'Подходите',
      createdAt: minutesAgo(2),
    },
  ],
}

type MockChatServiceOptions = {
  delayMs?: number
  listError?: string
  sendError?: string
  conversations?: ConversationSummary[]
  drinkOffers?: DrinkOfferSummary[]
}

export function createMockChatService({
  delayMs = 350,
  listError,
  sendError,
  conversations = MOCK_CONVERSATIONS,
  drinkOffers = MOCK_DRINK_OFFERS,
}: MockChatServiceOptions = {}): ChatService {
  const messages: Record<string, MessageDto[]> = structuredClone(MOCK_MESSAGES)
  let sentCount = 0

  return {
    async listConversations() {
      await wait(delayMs)
      if (listError) throw new ChatServiceError(listError)
      return conversations
    },
    async listDrinkOffers() {
      await wait(delayMs)
      if (listError) throw new ChatServiceError(listError)
      return drinkOffers
    },
    async listMessages(conversationId) {
      await wait(delayMs)
      if (listError) throw new ChatServiceError(listError)
      return { items: messages[conversationId] ?? [], nextCursor: null }
    },
    async sendMessage(conversationId, body) {
      await wait(delayMs)
      if (sendError) throw new ChatServiceError(sendError)
      sentCount += 1
      const message: MessageDto = {
        id: `msg-sent-${sentCount}`,
        conversationId,
        senderUserId: MOCK_VIEWER_USER_ID,
        type: 'text',
        body,
        createdAt: new Date().toISOString(),
      }
      messages[conversationId] = [...(messages[conversationId] ?? []), message]
      return message
    },
  }
}

export const mockChatService = createMockChatService()
