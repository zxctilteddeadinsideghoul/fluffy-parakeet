import { useState } from 'react'
import type { Meta, StoryObj } from '@storybook/react-vite'
import type { GenderOption } from './GenderSelect'
import { GenderSelect } from './GenderSelect'

function InteractiveGenderSelect() {
  const [value, setValue] = useState<GenderOption>('female')
  return <GenderSelect value={value} onChange={setValue} />
}

const meta = {
  title: 'Components/GenderSelect',
  component: GenderSelect,
  decorators: [
    (Story) => (
      <div style={{ width: 334 }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof GenderSelect>

export default meta
type Story = StoryObj<typeof meta>

export const Interactive: Story = {
  args: { value: 'female', onChange: () => undefined },
  render: () => <InteractiveGenderSelect />,
}
