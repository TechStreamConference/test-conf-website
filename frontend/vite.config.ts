import { defineConfig } from 'vitest/config';
import { loadEnv } from 'vite';
import { paraglideVitePlugin } from '@inlang/paraglide-js';
import { playwright } from '@vitest/browser-playwright';
import { sveltekit } from '@sveltejs/kit/vite';
import path from 'node:path';

export default defineConfig(({ mode }) => {
    // Load ../.env into process.env
    Object.assign(process.env, loadEnv(mode, path.resolve(import.meta.dirname, '..'), ''));

    return {
        plugins: [
            sveltekit(),
            // The output is checked in, so it has to be identical in dev and in build (CI validates it).
            // Without `outputStructure` the dev server uses another layout than the build.
            paraglideVitePlugin({
                project: './project.inlang',
                outdir: './src/paraglide',
                outputStructure: 'message-modules',
                emitReadme: false, // Contains an absolute path of the machine it was generated on.
                emitGitIgnore: false, // Would ignore the whole folder.
                emitPrettierIgnore: false // Prettier only reads the .prettierignore of the project root.
            })
        ],

        ssr: { noExternal: ['zod'] },

        test: {
            expect: { requireAssertions: true },

            projects: [
                {
                    extends: './vite.config.ts',

                    test: {
                        name: 'client',

                        browser: {
                            enabled: true,
                            provider: playwright(),
                            instances: [{ browser: 'chromium', headless: true }]
                        },

                        include: ['src/**/*.svelte.{test,spec}.{js,ts}'],
                        exclude: ['src/lib/server/**']
                    }
                },

                {
                    extends: './vite.config.ts',

                    test: {
                        name: 'server',
                        environment: 'node',

                        include: ['src/**/*.{test,spec}.{js,ts}'],
                        exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
                    }
                }
            ]
        }
    };
});
