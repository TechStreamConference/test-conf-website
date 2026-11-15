import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import SwitchStory from './fixtures/SwitchStory.svelte';

const META = {
    title: 'Components/Select',
    component: SwitchStory,
    parameters: {
        layout: 'fullscreen'
    },
    args: {
        selected: 'star'
    },
    argTypes: {
        selected: {
            control: 'select',
            options: ['star', 'heart', 'flag']
        }
    }
} satisfies Meta<ComponentProps<typeof SwitchStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const Generic: Story = {};
