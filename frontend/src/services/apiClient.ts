/**
 * HTTP client for the backend.
 *
 * Every successful response is `{"data": <DTO>}` and every error is
 * `{"error": {code, message, traceId}}` (docs/CONTRACTS_DATA.md, sections 2 and 7).
 *
 * Authentication is not implemented on the backend yet: `get_current_user_id`
 * reads the dev-only `X-Dev-User-Id` header and accepts it exclusively when
 * `BACKEND_ENVIRONMENT=development`. Until real auth lands, the viewer id comes
 * from `VITE_DEV_USER_ID` rather than from the sign-in form.
 */

/**
 * Defaults to the `/api` prefix proxied by the dev server (see vite.config.ts),
 * which keeps requests same-origin. Set VITE_API_BASE_URL to an absolute origin
 * only when the backend is reachable directly and sends CORS headers.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api'
export const DEV_USER_ID: string = import.meta.env.VITE_DEV_USER_ID ?? ''

type ErrorEnvelope = {
  error?: {
    code?: string
    message?: string
    traceId?: string
  }
}

export class ApiError extends Error {
  readonly code: string
  readonly status: number
  readonly traceId?: string

  constructor(code: string, message: string, status: number, traceId?: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.traceId = traceId
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  // FormData sets its own multipart boundary — overriding it breaks the upload.
  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (DEV_USER_ID) headers.set('X-Dev-User-Id', DEV_USER_ID)

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError('NETWORK_ERROR', 'Сервер недоступен', 0)
  }

  const payload = (await response.json().catch(() => undefined)) as
    | ({ data?: T } & ErrorEnvelope)
    | undefined

  if (!response.ok) {
    throw new ApiError(
      payload?.error?.code ?? 'INTERNAL_ERROR',
      payload?.error?.message ?? 'Запрос не выполнен',
      response.status,
      payload?.error?.traceId,
    )
  }

  return payload?.data as T
}
