import { useState } from 'react'
import type { Meta, StoryObj } from '@storybook/react-vite'
import { PhotoPicker } from './PhotoPicker'

function InteractivePhotoPicker() {
  const [file, setFile] = useState<File>()
  return <PhotoPicker value={file} onChange={setFile} />
}

const meta = {
  title: 'Components/PhotoPicker',
  component: PhotoPicker,
} satisfies Meta<typeof PhotoPicker>

export default meta
type Story = StoryObj<typeof meta>

export const Empty: Story = {
  args: { onChange: () => undefined },
  render: () => <InteractivePhotoPicker />,
}
