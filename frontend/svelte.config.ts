import type { Config } from '@sveltejs/kit';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import adapter from '@sveltejs/adapter-node';

const CONFIG: Config = {
    preprocess: vitePreprocess(),

    compilerOptions: {
        runes: ({ filename }) =>
            filename.split(/[/\\]/).includes('node_modules') ? undefined : true
    },

    kit: {
        adapter: adapter(),
        alias: {
            $gen: 'src/generated',
            $bff: 'src/bff',
            $lib: 'src/lib',
            $logging: 'src/logging',
            $src: 'src'
        }
    }
};

export default CONFIG;
