/**
 * Identity context client types (docs/CONTRACTS_DATA.md, sections 3, 5 and 6).
 *
 * `MyProfileDto` mirrors the backend response one-to-one. `MyProfileView` adds
 * the fields the profile screen needs that no current DTO returns — see the
 * comments below; they are deliberately kept outside `MyProfileDto`.
 */

import { apiRequest } from './apiClient'

export type CommunicationGoal =
  | 'dating'
  | 'friends'
  | 'company_tonight'
  | 'networking'
  | 'casual_chat'

export type ApproachMode = 'chat_only' | 'ask_before_approach' | 'may_approach'
export type MediaModerationStatus = 'pending' | 'approved' | 'rejected'

export type MyProfilePhotoDto = {
  id: string
  url: string
  position: number
  moderationStatus: MediaModerationStatus
}

export type MyProfileDto = {
  id: string
  displayName: string
  age: number | null
  gender?: string
  bio?: string
  communicationGoals: CommunicationGoal[]
  defaultApproachMode: ApproachMode
  photos: MyProfilePhotoDto[]
  verification: { isVerified: boolean }
}

export type MyProfileView = {
  profile: MyProfileDto
  /**
   * `UpdateMyProfileCommand` accepts `visibilityEnabled`, but `MyProfileDto`
   * does not return it, so the current value cannot be read back from the API.
   */
  visibilityEnabled: boolean
  /**
   * True when the value above is a client-side stand-in rather than server
   * state, so the screen can label the control as a stub.
   */
  isVisibilityStub?: boolean
  /**
   * Rendered under the «Верифицировано» row. `verification` exposes only
   * `isVerified`, so the date is not available from the profile DTO either.
   */
  verifiedAt?: string
}

/** Command UpdateMyProfileCommand (docs/CONTRACTS_DATA.md section 6). */
export type UpdateMyProfileCommand = {
  displayName: string
  gender?: string
  bio?: string
  birthDate?: string
  communicationGoals: CommunicationGoal[]
  defaultApproachMode: ApproachMode
  visibilityEnabled: boolean
}

export interface ProfileService {
  getMyProfile(): Promise<MyProfileView>
  setVisibilityEnabled(enabled: boolean): Promise<MyProfileView>
  updateMyProfile(command: UpdateMyProfileCommand): Promise<MyProfileView>
  uploadPhoto(file: File): Promise<MyProfileView>
  deletePhoto(photoId: string): Promise<MyProfileView>
}

export class ProfileServiceError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ProfileServiceError'
  }
}

/**
 * Talks to the real backend.
 *
 * `GET /me/profile` is used as-is. `setVisibilityEnabled` deliberately does NOT
 * call `PUT /me/profile`: that command is a full replacement and requires
 * `birthDate`, which `MyProfileDto` never returns — sending it would reset the
 * stored birth date to null and wipe `age`. The toggle therefore stays local
 * until the contract exposes `visibilityEnabled` (and either returns
 * `birthDate` or makes the update partial).
 */
export function createHttpProfileService(): ProfileService {
  // Mirrors what we last sent. Starts as a guess because GET cannot report it,
  // and becomes real state once the edit form submits a value we chose.
  let visibilityEnabled = true
  let isVisibilityStub = true

  const view = (profile: MyProfileDto): MyProfileView => ({
    profile,
    visibilityEnabled,
    isVisibilityStub,
  })

  return {
    async getMyProfile() {
      return view(await apiRequest<MyProfileDto>('/me/profile'))
    },
    async setVisibilityEnabled(enabled) {
      // Not persisted: PUT is a full replacement and needs `birthDate`, which
      // MyProfileDto never returns — sending it here would wipe the stored date.
      // The edit form collects `birthDate`, so it can persist this for real.
      visibilityEnabled = enabled
      return view(await apiRequest<MyProfileDto>('/me/profile'))
    },
    async updateMyProfile(command) {
      const profile = await apiRequest<MyProfileDto>('/me/profile', {
        method: 'PUT',
        body: JSON.stringify(command),
      })
      visibilityEnabled = command.visibilityEnabled
      isVisibilityStub = false
      return view(profile)
    },
    async uploadPhoto(file) {
      const form = new FormData()
      form.append('file', file)
      return view(
        await apiRequest<MyProfileDto>('/me/profile/photos', { method: 'POST', body: form }),
      )
    },
    async deletePhoto(photoId) {
      return view(
        await apiRequest<MyProfileDto>(`/me/profile/photos/${encodeURIComponent(photoId)}`, {
          method: 'DELETE',
        }),
      )
    },
  }
}

export const httpProfileService = createHttpProfileService()

const wait = (delayMs: number) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, delayMs))

const MOCK_PROFILE: MyProfileDto = {
  id: 'user-me',
  displayName: 'Марина',
  age: 27,
  gender: 'female',
  bio: 'Здесь с подругой, у бара справа. Люблю громкую музыку и тихие разговоры — можно и то, и другое.',
  communicationGoals: ['dating', 'company_tonight'],
  defaultApproachMode: 'ask_before_approach',
  photos: [],
  verification: { isVerified: true },
}

type MockProfileServiceOptions = {
  delayMs?: number
  loadError?: string
  updateError?: string
  profile?: MyProfileDto
  visibilityEnabled?: boolean
  verifiedAt?: string
}

export function createMockProfileService({
  delayMs = 350,
  loadError,
  updateError,
  profile = MOCK_PROFILE,
  visibilityEnabled = true,
  verifiedAt = '2026-03-12',
}: MockProfileServiceOptions = {}): ProfileService {
  let visibility = visibilityEnabled
  let current = profile

  const view = (): MyProfileView => ({
    profile: current,
    visibilityEnabled: visibility,
    verifiedAt,
  })

  return {
    async getMyProfile() {
      await wait(delayMs)
      if (loadError) throw new ProfileServiceError(loadError)
      return view()
    },
    async setVisibilityEnabled(enabled) {
      await wait(delayMs)
      if (updateError) throw new ProfileServiceError(updateError)
      visibility = enabled
      return view()
    },
    async updateMyProfile(command) {
      await wait(delayMs)
      if (updateError) throw new ProfileServiceError(updateError)
      current = {
        ...current,
        displayName: command.displayName,
        gender: command.gender,
        bio: command.bio,
        communicationGoals: command.communicationGoals,
        defaultApproachMode: command.defaultApproachMode,
      }
      visibility = command.visibilityEnabled
      return view()
    },
    async uploadPhoto(file) {
      await wait(delayMs)
      if (updateError) throw new ProfileServiceError(updateError)
      current = {
        ...current,
        photos: [
          ...current.photos,
          {
            id: `photo-${current.photos.length + 1}`,
            url: URL.createObjectURL(file),
            position: current.photos.length + 1,
            moderationStatus: 'approved',
          },
        ],
      }
      return view()
    },
    async deletePhoto(photoId) {
      await wait(delayMs)
      if (updateError) throw new ProfileServiceError(updateError)
      current = {
        ...current,
        photos: current.photos.filter((photo) => photo.id !== photoId),
      }
      return view()
    },
  }
}

export const mockProfileService = createMockProfileService()
