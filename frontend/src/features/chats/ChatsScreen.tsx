import { useEffect, useState } from 'react'
import { Avatar } from '../../components/Avatar'
import { FormMessage } from '../../components/FormMessage'
import { PresenceBar } from '../../components/PresenceBar'
import { TabBar } from '../../components/TabBar'
import type { TabKey } from '../../components/TabBar'
import { CheersIcon } from '../../components/icons'
import type {
  ChatService,
  ConversationSummary,
  DrinkOfferSummary,
} from '../../services/chatService'
import { formatChatTime } from './formatTime'
import './chats.css'

type ChatsScreenProps = {
  chatService: ChatService
  viewerUserId: string
  venueLabel: string
  onOpenConversation: (conversation: ConversationSummary) => void
  onOpenDrinkOffer: (offerId: string) => void
  onNavigate: (tab: TabKey) => void
}

/**
 * `ConversationDto` and `DrinkOfferDto` carry no display name, so when the peer
 * could not be joined the row shows an explicit placeholder instead of a name.
 */
const peerName = (peer: { displayName: string } | null) => peer?.displayName ?? 'Имя (заглушка)'

export function ChatsScreen({
  chatService,
  viewerUserId,
  venueLabel,
  onOpenConversation,
  onOpenDrinkOffer,
  onNavigate,
}: ChatsScreenProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [drinkOffers, setDrinkOffers] = useState<DrinkOfferSummary[]>([])
  const [loadError, setLoadError] = useState<string>()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      setLoadError(undefined)
      try {
        const [nextConversations, nextOffers] = await Promise.all([
          chatService.listConversations(),
          chatService.listDrinkOffers(),
        ])
        if (cancelled) return
        setConversations(nextConversations)
        setDrinkOffers(nextOffers)
      } catch {
        if (!cancelled) setLoadError('Не удалось загрузить чаты')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [chatService])

  const pendingOffers = drinkOffers.filter(({ offer }) => offer.status === 'pending')
  const incomingOffers = pendingOffers.filter(
    ({ offer }) => offer.recipientUserId === viewerUserId,
  )
  const sentOffers = pendingOffers.filter(({ offer }) => offer.senderUserId === viewerUserId)
  const isEmpty =
    !isLoading &&
    !loadError &&
    incomingOffers.length === 0 &&
    sentOffers.length === 0 &&
    conversations.length === 0

  return (
    <div className="chats-screen accent-red">
      <PresenceBar venueLabel={venueLabel} isStub />

      <header className="chats-screen__heading">
        <h1>Чаты</h1>
      </header>

      <div className="chats-screen__list">
        {loadError && <FormMessage>{loadError}</FormMessage>}
        {isLoading && (
          <p className="chats-screen__status" role="status">
            Загружаем чаты…
          </p>
        )}
        {isEmpty && (
          <p className="chats-screen__status" role="status">
            Пока ничего нет. Напишите тому, кто рядом — и разговор появится здесь.
          </p>
        )}

        {incomingOffers.length > 0 && (
          <>
            <span className="section-label">Ждут ответа</span>
            {incomingOffers.map(({ offer, peer }) => (
              <button
                key={offer.id}
                type="button"
                className="chat-row chat-row--waiting"
                onClick={() => onOpenDrinkOffer(offer.id)}
              >
                <Avatar name={peerName(peer)} />
                <span className="chat-row__body">
                  <span className="chat-row__name">{peerName(peer)}</span>
                  <span className="chat-row__gift">
                    <CheersIcon size={15} strokeWidth={1.8} />
                    подарил напиток
                  </span>
                </span>
                <span className="chat-row__time">{formatChatTime(offer.createdAt)}</span>
              </button>
            ))}
          </>
        )}

        {sentOffers.length > 0 && (
          <>
            <span className="section-label">Отправлено</span>
            {sentOffers.map(({ offer, peer }) => (
              <div key={offer.id} className="chat-row chat-row--sent">
                <Avatar name={peerName(peer)} muted />
                <span className="chat-row__body">
                  <span className="chat-row__name">{peerName(peer)}</span>
                  <span className="chat-row__preview">Напиток отправлен · ждёт ответа</span>
                </span>
                <span className="chat-row__time">{formatChatTime(offer.createdAt)}</span>
              </div>
            ))}
          </>
        )}

        {conversations.length > 0 && (
          <>
            <span className="section-label">Диалоги</span>
            {conversations.map((summary) => {
              const { conversation, peer } = summary
              return (
              <button
                key={conversation.id}
                type="button"
                className="chat-row"
                onClick={() => onOpenConversation(summary)}
              >
                <Avatar name={peerName(peer)} />
                <span className="chat-row__body">
                  <span className="chat-row__name">{peerName(peer)}</span>
                  <span className="chat-row__preview">{conversation.lastMessageBody}</span>
                </span>
                <span className="chat-row__meta">
                  <span className="chat-row__time">
                    {conversation.lastMessageAt ? formatChatTime(conversation.lastMessageAt) : ''}
                  </span>
                  {conversation.unreadCount > 0 && (
                    <span className="chat-row__unread">
                      {conversation.unreadCount}
                      <span className="sr-only">непрочитанных</span>
                    </span>
                  )}
                </span>
              </button>
              )
            })}
          </>
        )}
      </div>

      <TabBar active="chats" onNavigate={onNavigate} />
    </div>
  )
}
