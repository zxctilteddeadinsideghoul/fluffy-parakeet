import type { ReactNode } from 'react'

type IconProps = {
  size?: number
  strokeWidth?: number
}

export function CheersIcon({ size = 24, strokeWidth = 1.9 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <g transform="rotate(-16 10 12)">
        <path d="M6 7h8l-1 5.6a3 3 0 0 1-6 0z" />
        <path d="M10 13v5M7.6 18.4h4.8" />
      </g>
      <g transform="rotate(16 19 12)">
        <path d="M15 7h8l-1 5.6a3 3 0 0 1-6 0z" />
        <path d="M19 13v5M16.6 18.4h4.8" />
      </g>
    </svg>
  )
}

export function VerifiedIcon({ size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 .8l1.7 1.35 2.16-.15.62 2.08 1.87 1.1-.75 2.04.75 2.04-1.87 1.1-.62 2.08-2.16-.15L8 15.2l-1.7-1.35-2.16.15-.62-2.08-1.87-1.1.75-2.04-.75-2.04 1.87-1.1.62-2.08 2.16.15z" />
      <path d="M6.9 10.6L4.6 8.3l.95-.95 1.35 1.35 3-3 .95.95z" fill="var(--color-surface)" />
    </svg>
  )
}

function StrokeIcon({
  children,
  size = 24,
  strokeWidth = 1.8,
}: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

export function ChevronRightIcon({ size = 18, strokeWidth = 2.2 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <path d="M9 5.5L15.5 12 9 18.5" />
    </StrokeIcon>
  )
}

export function ChevronLeftIcon({ size = 19, strokeWidth = 2.2 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <path d="M14.5 5.5L8 12l6.5 6.5" />
    </StrokeIcon>
  )
}

export function SendIcon({ size = 22, strokeWidth = 2 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <path d="M4 12h15M13 6l6 6-6 6" />
    </StrokeIcon>
  )
}

export function PencilIcon({ size = 15, strokeWidth = 1.9 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <path d="M16.5 4.5l3 3L9 18l-4 1 1-4z" />
    </StrokeIcon>
  )
}

export function VenueIcon({ size = 23, strokeWidth = 1.8 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <path d="M4 20V9.5L12 4l8 5.5V20" />
      <path d="M9.5 20v-6h5v6" />
    </StrokeIcon>
  )
}

export function PeopleIcon({ size = 23, strokeWidth = 1.8 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3.4 19c.5-3.1 2.8-4.8 5.6-4.8s5.1 1.7 5.6 4.8" />
      <path d="M16.4 5.4a3 3 0 0 1 0 5.4" />
      <path d="M18 18.8c-.2-1.9-.9-3.3-2-4.2 2.5.2 4.2 1.8 4.6 4.2z" />
    </StrokeIcon>
  )
}

export function ChatsIcon({ size = 23, strokeWidth = 1.8 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <path d="M20 12.5c0 3.9-3.6 7-8 7-1 0-2-.2-2.9-.5L4.5 20.5l1.1-3.3A6.7 6.7 0 0 1 4 12.5c0-3.9 3.6-7 8-7s8 3.1 8 7z" />
    </StrokeIcon>
  )
}

export function ProfileIcon({ size = 23, strokeWidth = 1.8 }: IconProps) {
  return (
    <StrokeIcon size={size} strokeWidth={strokeWidth}>
      <circle cx="12" cy="8.2" r="3.6" />
      <path d="M5 20c.6-3.6 3.4-5.6 7-5.6s6.4 2 7 5.6" />
    </StrokeIcon>
  )
}
