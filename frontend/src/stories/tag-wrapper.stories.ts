import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import TagWrapperComponent from '$lib/elements/text/TagWrapper.svelte';

const META = {
    title: 'Components/Text',
    component: TagWrapperComponent,
    args: {
        tags: [
            { id: 1, color_id: 1, text: 'Testing' },
            { id: 2, color_id: 2, text: 'Frontend' },
            { id: 3, color_id: 1, text: 'Svelte' }
        ]
    }
} satisfies Meta<ComponentProps<typeof TagWrapperComponent>>;

export default META;
type Story = StoryObj<typeof META>;
export const TagWrapper: Story = {};
