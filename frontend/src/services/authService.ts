export type Credentials = {
  email: string
  password: string
}

export type RegistrationDraft = Credentials & {
  passwordConfirmation: string
}

export type ProfileDraft = {
  displayName: string
  birthDate: string
  gender: string
  bio?: string
  photo?: File
}

export interface AuthService {
  signIn(credentials: Credentials): Promise<void>
  register(credentials: Credentials): Promise<void>
}

export class AuthServiceError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'AuthServiceError'
  }
}

type MockAuthServiceOptions = {
  delayMs?: number
  signInError?: string
  registerError?: string
}

const wait = (delayMs: number) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, delayMs))

export function createMockAuthService({
  delayMs = 450,
  registerError,
  signInError,
}: MockAuthServiceOptions = {}): AuthService {
  return {
    async signIn() {
      await wait(delayMs)
      if (signInError) throw new AuthServiceError(signInError)
    },
    async register() {
      await wait(delayMs)
      if (registerError) throw new AuthServiceError(registerError)
    },
  }
}

export const mockAuthService = createMockAuthService()
