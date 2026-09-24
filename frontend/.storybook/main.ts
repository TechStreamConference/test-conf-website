import type { StorybookConfig } from '@storybook/sveltekit';

const CONFIG: StorybookConfig = {
    stories: ['../src/**/*.stories.@(js|ts|svelte)'],
    addons: ['@storybook/addon-a11y'],
    framework: '@storybook/sveltekit',
    staticDirs: ['../static']
};

export default CONFIG;
