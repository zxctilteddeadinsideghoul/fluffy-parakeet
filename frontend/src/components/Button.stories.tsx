import type { Meta, StoryObj } from '@storybook/react-vite'
import { Button } from './Button'

const meta = {
  title: 'Components/Button',
  component: Button,
  args: { children: 'Продолжить' },
  decorators: [
    (Story) => (
      <div style={{ width: 334 }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

export const Primary: Story = {}
export const Secondary: Story = { args: { variant: 'secondary', children: 'Выйти' } }
export const Loading: Story = { args: { isLoading: true } }
export const Disabled: Story = { args: { disabled: true } }
