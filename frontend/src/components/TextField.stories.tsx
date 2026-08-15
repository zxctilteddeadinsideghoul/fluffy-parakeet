import type { Meta, StoryObj } from '@storybook/react-vite'
import { TextField } from './TextField'

const meta = {
  title: 'Components/TextField',
  component: TextField,
  args: { label: 'Email', placeholder: 'you@example.com' },
  decorators: [
    (Story) => (
      <div style={{ width: 334 }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof TextField>

export default meta
type Story = StoryObj<typeof meta>

export const Empty: Story = {}
export const Filled: Story = { args: { value: 'marina@example.com', readOnly: true } }
export const Password: Story = { args: { label: 'Пароль', type: 'password', value: 'password123', readOnly: true } }
export const Error: Story = { args: { error: 'Проверьте формат email', value: 'marina@' } }
