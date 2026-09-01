import js from '@eslint/js';
import path from 'node:path';
import prettier from 'eslint-config-prettier';
import globals from 'globals';
import ts from 'typescript-eslint';
import { defineConfig, includeIgnoreFile } from 'eslint/config';
import svelte from 'eslint-plugin-svelte';

const gitignorePath = path.resolve(import.meta.dirname, '.gitignore');

export default defineConfig(
	includeIgnoreFile(gitignorePath),

	{
		ignores: ['src/generated/**']
	},

	js.configs.recommended,
	ts.configs.recommended,

	// Register the Svelte parser and recommended rules.
	...svelte.configs.recommended,

	prettier,

	// ---------------------------------------------------------------------
	// TypeScript
	// ---------------------------------------------------------------------
	{
		files: ['{src,scripts}/**/*.ts'],

		extends: [ts.configs.strictTypeChecked],

		languageOptions: {
			parser: ts.parser,
			parserOptions: {
				projectService: {
					allowDefaultProject: ['scripts/*.ts']
				}
			},
			globals: {
				...globals.browser,
				...globals.node
			}
		},

		rules: {
			'@typescript-eslint/no-explicit-any': 'error',
			'@typescript-eslint/no-unsafe-assignment': 'error',
			'@typescript-eslint/no-unsafe-call': 'error',
			'@typescript-eslint/no-unsafe-member-access': 'error',
			'@typescript-eslint/no-unsafe-return': 'error',
			'@typescript-eslint/no-unsafe-argument': 'error'
		}
	},

	// ---------------------------------------------------------------------
	// JavaScript (Node scripts)
	// ---------------------------------------------------------------------
	{
		files: ['scripts/**/*.js'],

		extends: [ts.configs.recommendedTypeChecked],

		languageOptions: {
			parser: ts.parser,
			parserOptions: {
				project: './tsconfig.scripts.json'
			},
			globals: {
				...globals.node
			}
		},

		rules: {
			'@typescript-eslint/no-explicit-any': 'error',

			'@typescript-eslint/no-unsafe-assignment': 'off',
			'@typescript-eslint/no-unsafe-call': 'off',
			'@typescript-eslint/no-unsafe-member-access': 'off',
			'@typescript-eslint/no-unsafe-return': 'off',
			'@typescript-eslint/no-unsafe-argument': 'off'
		}
	},

	// ---------------------------------------------------------------------
	// Svelte
	// ---------------------------------------------------------------------
	{
		files: ['src/**/*.svelte'],

		languageOptions: {
			parserOptions: {
				parser: ts.parser,
				projectService: true,
				extraFileExtensions: ['.svelte']
			},
			globals: {
				...globals.browser,
				...globals.node
			}
		},

		rules: {
			// Disallow `class="..."` on native HTML elements (components are fine).
			'no-restricted-syntax': [
				'error',
				{
					selector:
						'SvelteElement[kind="html"] > SvelteStartTag > SvelteAttribute[key.name="class"]',
					message:
						'Do not use `class="..."` on native HTML elements. Use it only on components. Use `class:...={true}` instead'
				},
				// Spread attributes (e.g. `{...rest}`) must always be the first attribute,
				// both on native HTML tags and on components.
				{
					selector: 'SvelteStartTag > SvelteSpreadAttribute:not(:first-child)',
					message: 'Spread attributes (e.g. `{...rest}`) must be the first attribute.'
				}
			],
			'@typescript-eslint/no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_',
					varsIgnorePattern: '^_',
					caughtErrorsIgnorePattern: '^_'
				}
			],
			'@typescript-eslint/no-explicit-any': 'error',
			'@typescript-eslint/no-unsafe-assignment': 'error',
			'@typescript-eslint/no-unsafe-call': 'error',
			'@typescript-eslint/no-unsafe-member-access': 'error',
			'@typescript-eslint/no-unsafe-return': 'error',
			'@typescript-eslint/no-unsafe-argument': 'error'
		}
	}
);
