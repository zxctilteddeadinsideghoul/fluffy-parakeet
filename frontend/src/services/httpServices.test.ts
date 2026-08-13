import { afterEach, expect, vi } from 'vitest'
import { ApiError } from './apiClient'
import { createHttpChatService } from './chatService'
import { createHttpProfileService } from './profileService'

function mockFetch(payload: unknown, init: { ok?: boolean; status?: number } = {}) {
  const fetchMock = vi.fn(async (_url: string, _init?: RequestInit) => ({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => payload,
  }))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const profilePayload = {
  data: {
    id: 'user-1',
    displayName: 'Марина',
    age: 27,
    communicationGoals: [],
    defaultApproachMode: 'ask_before_approach',
    photos: [],
    verification: { isVerified: true },
  },
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('apiRequest', () => {
  it('unwraps the success envelope', async () => {
    mockFetch({ data: [] })
    await expect(createHttpChatService().listConversations()).resolves.toEqual([])
  })

  it('turns the error envelope into an ApiError with its code', async () => {
    mockFetch(
      { error: { code: 'AUTH_REQUIRED', message: 'Требуется вход', traceId: 'req-1' } },
      { ok: false, status: 401 },
    )

    await expect(createHttpProfileService().getMyProfile()).rejects.toMatchObject({
      name: 'ApiError',
      code: 'AUTH_REQUIRED',
      status: 401,
      traceId: 'req-1',
    })
  })

  it('reports an unreachable server instead of throwing a raw fetch error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )

    await expect(createHttpProfileService().getMyProfile()).rejects.toBeInstanceOf(ApiError)
  })
})

describe('createHttpChatService', () => {
  it('leaves the peer unresolved because the DTO carries no display name', async () => {
    mockFetch({ data: [{ id: 'conv-1', peerUserId: 'user-2', unreadCount: 0 }] })

    const [summary] = await createHttpChatService().listConversations()
    expect(summary.peer).toBeNull()
    expect(summary.conversation.id).toBe('conv-1')
  })

  it('posts the message body to the conversation endpoint', async () => {
    const fetchMock = mockFetch({ data: { id: 'msg-1', body: 'Уже иду' } })

    await createHttpChatService().sendMessage('conv 1', 'Уже иду')

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toContain('/me/conversations/conv%201/messages')
    expect(init?.method).toBe('POST')
    expect(init?.body).toBe(JSON.stringify({ body: 'Уже иду' }))
  })
})

describe('createHttpProfileService', () => {
  it('flags the visibility value as a stub', async () => {
    mockFetch(profilePayload)

    const view = await createHttpProfileService().getMyProfile()
    expect(view.isVisibilityStub).toBe(true)
    expect(view.profile.displayName).toBe('Марина')
  })

  it('never PUTs the profile, so the stored birthDate cannot be wiped', async () => {
    const fetchMock = mockFetch(profilePayload)

    await createHttpProfileService().setVisibilityEnabled(false)

    const methods = fetchMock.mock.calls.map(([, init]) => init?.method ?? 'GET')
    expect(methods).not.toContain('PUT')
  })
})
