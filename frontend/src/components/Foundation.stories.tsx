import type { Meta, StoryObj } from '@storybook/react-vite'
import { Brand, SuccessMark } from './Brand'
import { FormMessage } from './FormMessage'
import { MobileScreen } from './MobileScreen'

function FoundationPreview() {
  return (
    <div style={{ display: 'grid', gap: 28, padding: 28 }}>
      <Brand />
      <SuccessMark />
      <FormMessage>Не удалось выполнить запрос</FormMessage>
      <div className="palette-preview">
        {['brand', 'brand-soft', 'text-primary', 'text-secondary', 'border', 'surface'].map((token) => (
          <div key={token}>
            <i style={{ background: `var(--color-${token})` }} />
            <span>{token}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const meta = {
  title: 'Components/Foundation',
  component: FoundationPreview,
} satisfies Meta<typeof FoundationPreview>

export default meta
type Story = StoryObj<typeof meta>

export const TokensAndBrand: Story = {}
export const ScreenShell: Story = {
  parameters: { layout: 'fullscreen' },
  render: () => (
    <MobileScreen>
      <FoundationPreview />
    </MobileScreen>
  ),
}
