import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { TagColor } from '$lib/helper/tag';

import TextStory from './fixtures/TextStory.svelte';

const META = {
    title: 'Components/Text',
    component: TextStory,
    args: {
        variant: 'headline',
        text: 'Tech Stream Conference',
        renderLine: false,
        preserveNewlines: false,
        tagColor: TagColor.Blue
    },
    argTypes: {
        variant: {
            control: 'select',
            options: ['headline', 'subheadline', 'paragraph', 'tag']
        },
        tagColor: {
            control: 'select',
            options: [TagColor.Blue, TagColor.BlueLight],
            mapping: {
                Blue: TagColor.Blue,
                BlueLight: TagColor.BlueLight
            }
        }
    }
} satisfies Meta<ComponentProps<typeof TextStory>>;

export default META;

type Story = StoryObj<typeof META>;

export const Headline: Story = {
    args: {
        renderLine: true
    }
};
export const SubHeadline: Story = {
    args: {
        variant: 'subheadline',
        text: 'Building reliable software together'
    }
};
export const Paragraph: Story = {
    args: {
        variant: 'paragraph',
        text: 'A conference for people who care about testing, quality, and sustainable engineering.'
    }
};
export const PreservedNewlines: Story = {
    args: {
        variant: 'paragraph',
        text: 'First line\nSecond line',
        preserveNewlines: true
    }
};
export const Tag: Story = {
    args: {
        variant: 'tag',
        text: 'Testing'
    }
};
