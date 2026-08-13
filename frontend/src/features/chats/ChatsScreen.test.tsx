import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
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

function renderChats(overrides: Partial<Parameters<typeof ChatsScreen>[0]> = {}) {
  const onOpenConversation = vi.fn()
  render(
    <ChatsScreen
      chatService={createMockChatService({ delayMs: 0 })}
      viewerUserId={MOCK_VIEWER_USER_ID}
      venueLabel={VENUE_LABEL}
      onOpenConversation={onOpenConversation}
      onOpenDrinkOffer={() => undefined}
      onNavigate={() => undefined}
      {...overrides}
    />,
  )
  return { onOpenConversation }
}

describe('ChatsScreen', () => {
  it('splits incoming offers, sent offers and conversations', async () => {
    renderChats()

    expect(await screen.findByText('Ждут ответа')).toBeInTheDocument()
    expect(screen.getByText('Отправлено')).toBeInTheDocument()
    expect(screen.getByText('Диалоги')).toBeInTheDocument()

    // Илья sent a drink to the viewer, Даша received one from the viewer.
    expect(screen.getByRole('button', { name: /Илья/ })).toBeInTheDocument()
    expect(screen.getByText('Напиток отправлен · ждёт ответа')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Марина/ })).toBeInTheDocument()
  })

  it('opens a conversation with its joined peer', async () => {
    const user = userEvent.setup()
    const { onOpenConversation } = renderChats()

    await user.click(await screen.findByRole('button', { name: /Марина/ }))

    expect(onOpenConversation).toHaveBeenCalledWith(
      expect.objectContaining({
        conversation: expect.objectContaining({ id: 'conv-marina' }),
      }),
    )
  })

  it('labels an unresolved peer as a placeholder instead of guessing a name', async () => {
    renderChats({
      chatService: createMockChatService({
        delayMs: 0,
        drinkOffers: [],
        conversations: [
          {
            conversation: {
              ...marinaConversation.conversation,
              lastMessageBody: 'Подходите',
            },
            peer: null,
          },
        ],
      }),
    })

    expect(await screen.findByText('Имя (заглушка)')).toBeInTheDocument()
  })

  it('shows an empty state when there is nothing to read', async () => {
    renderChats({
      chatService: createMockChatService({ delayMs: 0, conversations: [], drinkOffers: [] }),
    })

    expect(await screen.findByText(/Пока ничего нет/)).toBeInTheDocument()
  })

  it('reports a load failure instead of rendering an empty list', async () => {
    renderChats({ chatService: createMockChatService({ delayMs: 0, listError: 'offline' }) })

    expect(await screen.findByRole('alert')).toHaveTextContent('Не удалось загрузить чаты')
    expect(screen.queryByText(/Пока ничего нет/)).not.toBeInTheDocument()
  })
})

describe('ChatScreen', () => {
  it('renders own and peer messages on opposite sides', async () => {
    render(
      <ChatScreen
        chatService={createMockChatService({ delayMs: 0 })}
        conversation={marinaConversation}
        viewerUserId={MOCK_VIEWER_USER_ID}
        onBack={() => undefined}
      />,
    )

    const own = await screen.findByText('Он первый начал. Можно подойду?')
    expect(own).toHaveClass('chat-bubble--own')
    expect(screen.getByText('Подходите')).toHaveClass('chat-bubble--peer')
    expect(screen.getByText('Марина приняла ваш напиток')).toHaveClass('chat-bubble--system')
  })

  it('sends a message and clears the draft', async () => {
    const user = userEvent.setup()
    render(
      <ChatScreen
        chatService={createMockChatService({ delayMs: 0 })}
        conversation={marinaConversation}
        viewerUserId={MOCK_VIEWER_USER_ID}
        onBack={() => undefined}
      />,
    )

    const input = await screen.findByLabelText('Сообщение')
    await user.type(input, 'Уже иду')
    await user.click(screen.getByRole('button', { name: 'Отправить' }))

    expect(await screen.findByText('Уже иду')).toHaveClass('chat-bubble--own')
    expect(input).toHaveValue('')
  })

  it('keeps the draft when sending fails', async () => {
    const user = userEvent.setup()
    render(
      <ChatScreen
        chatService={createMockChatService({ delayMs: 0, sendError: 'offline' })}
        conversation={marinaConversation}
        viewerUserId={MOCK_VIEWER_USER_ID}
        onBack={() => undefined}
      />,
    )

    const input = await screen.findByLabelText('Сообщение')
    await user.type(input, 'Уже иду')
    await user.click(screen.getByRole('button', { name: 'Отправить' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Сообщение не отправлено')
    expect(input).toHaveValue('Уже иду')
  })
})
