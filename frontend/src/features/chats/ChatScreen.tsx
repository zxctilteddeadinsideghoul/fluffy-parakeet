import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Avatar } from '../../components/Avatar'
import { FormMessage } from '../../components/FormMessage'
import { CheersIcon, ChevronLeftIcon, SendIcon, VerifiedIcon } from '../../components/icons'
import type { ChatService, ConversationSummary, MessageDto } from '../../services/chatService'
import './chats.css'

type ChatScreenProps = {
  chatService: ChatService
  conversation: ConversationSummary
  viewerUserId: string
  onBack: () => void
}

function meetingNote(createdAt: string, venueName: string) {
  const created = new Date(createdAt)
  const isToday = created.toDateString() === new Date().toDateString()
  const when = isToday
    ? 'сегодня'
    : created.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
  return `Вы познакомились в баре «${venueName}» ${when}`
}

export function ChatScreen({
  chatService,
  conversation,
  viewerUserId,
  onBack,
}: ChatScreenProps) {
  const { conversation: dto, peer, venueName } = conversation
  const [messages, setMessages] = useState<MessageDto[]>([])
  const [draft, setDraft] = useState('')
  const [loadError, setLoadError] = useState<string>()
  const [sendError, setSendError] = useState<string>()
  const [isSending, setIsSending] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoadError(undefined)
      try {
        const page = await chatService.listMessages(dto.id)
        if (!cancelled) setMessages(page.items)
      } catch {
        if (!cancelled) setLoadError('Не удалось загрузить переписку')
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [chatService, dto.id])

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'end' })
  }, [messages])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const body = draft.trim()
    if (!body || isSending) return

    setIsSending(true)
    setSendError(undefined)
    try {
      const message = await chatService.sendMessage(dto.id, body)
      setMessages((current) => [...current, message])
      setDraft('')
    } catch {
      setSendError('Сообщение не отправлено')
    } finally {
      setIsSending(false)
    }
  }

  // See ChatsScreen: the conversation DTO has no display name for the peer.
  const peerLabel = peer?.displayName ?? 'Имя (заглушка)'

  return (
    <div className="chat-screen accent-red">
      <header className="chat-screen__header">
        <button
          type="button"
          className="chat-screen__back"
          onClick={onBack}
          aria-label="Назад к чатам"
        >
          <ChevronLeftIcon />
        </button>
        <Avatar name={peerLabel} size="sm" muted />
        <h1 className="chat-screen__title">
          {peerLabel}
          {peer?.age != null && <span className="chat-screen__age">{peer.age}</span>}
          {peer?.isVerified && (
            <span className="chat-screen__verified">
              <VerifiedIcon size={15} />
              <span className="sr-only">Профиль верифицирован</span>
            </span>
          )}
        </h1>
      </header>

      {venueName && (
        <p className="chat-screen__note">
          <CheersIcon size={18} strokeWidth={1.7} />
          {meetingNote(dto.createdAt, venueName)}
        </p>
      )}

      <div className="chat-screen__thread">
        {loadError && <FormMessage>{loadError}</FormMessage>}
        {messages.map((message) =>
          message.type === 'system' ? (
            <p key={message.id} className="chat-bubble chat-bubble--system">
              {message.body}
            </p>
          ) : (
            <p
              key={message.id}
              className={`chat-bubble ${
                message.senderUserId === viewerUserId ? 'chat-bubble--own' : 'chat-bubble--peer'
              }`}
            >
              {message.body}
            </p>
          ),
        )}
        <div ref={endRef} />
      </div>

      {sendError && (
        <div className="chat-screen__error">
          <FormMessage>{sendError}</FormMessage>
        </div>
      )}

      <form className="chat-screen__composer" onSubmit={handleSubmit}>
        <input
          className="chat-screen__input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Сообщение"
          aria-label="Сообщение"
          maxLength={2000}
        />
        <button
          type="submit"
          className="chat-screen__send"
          disabled={!draft.trim() || isSending}
          aria-label="Отправить"
        >
          <SendIcon />
        </button>
      </form>
    </div>
  )
}
