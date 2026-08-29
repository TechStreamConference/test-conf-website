<script lang="ts">
	import { onMount } from 'svelte';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';
	import SunMoon from '@lucide/svelte/icons/sun-moon';
	import Hourglass from '@lucide/svelte/icons/hourglass';

	import { Theme } from '$lib/helper/light-dark';
	import { setTheme } from '$lib/helper/light-dark';
	import { getTheme } from '$lib/helper/light-dark';

	onMount(() => {
		currentTheme = getTheme();
	});

	let currentTheme: Theme | undefined = $state(undefined);
	let isOpen: boolean = $state(false);

	function select(theme: Theme): void {
		setTheme(theme);
		isOpen = false;
		currentTheme = theme;
	}
</script>

<details bind:open={isOpen}>
	<summary aria-label="Theme selector">
		{#if currentTheme === Theme.Dark}
			<Moon aria-hidden="true" />
		{:else if currentTheme === Theme.Light}
			<Sun aria-hidden="true" />
		{:else if currentTheme === Theme.System}
			<SunMoon aria-hidden="true" />
		{:else}
			<Hourglass aria-hidden="true" />
		{/if}
	</summary>

	<div>
		<button
			class:selected={currentTheme === Theme.System}
			type="button"
			aria-pressed={currentTheme === Theme.System}
			onclick={() => select(Theme.System)}><SunMoon aria-hidden="true" /> System</button
		>
		<button
			class:selected={currentTheme === Theme.Light}
			type="button"
			aria-pressed={currentTheme === Theme.Light}
			onclick={() => select(Theme.Light)}><Sun aria-hidden="true" /> Light</button
		>
		<button
			class:selected={currentTheme === Theme.Dark}
			type="button"
			aria-pressed={currentTheme === Theme.Dark}
			onclick={() => select(Theme.Dark)}><Moon aria-hidden="true" /> Dark</button
		>
	</div>
</details>

<style>
	details {
		display: inline-block;
		position: relative;
	}

	summary {
		display: flex;
		align-items: center;
		justify-content: center;

		width: 4.4rem;
		height: 4.4rem;

		margin: 0.5rem;
		border-radius: var(--border-radius);
		border: none;

		user-select: none;
		cursor: pointer;
		list-style: none;
		background-color: transparent;
		color: var(--text-color);

		font-size: 2rem;

		transition: background-color var(--transition-duration);
	}
	summary:hover,
	summary:focus-visible {
		background-color: var(--primary-color-400);
		color: var(--white-color);
	}

	div {
		display: flex;
		flex-direction: column;
		position: absolute;
		gap: 0.4rem;

		top: calc(100% + 0.8rem);
		inset-inline-end: 0;
		min-width: 15rem;
		padding: 0.6rem;
		border-radius: var(--border-radius);

		background-color: var(--background-color-500);
		pointer-events: none;

		box-shadow: 0 0.6rem 2rem rgba(0, 0, 0, 0.25);
		opacity: 0;
		transform: translateY(-0.5rem);

		transition:
			opacity var(--transition-duration),
			transform var(--transition-duration);
	}
	details[open] div {
		pointer-events: auto;

		opacity: 1;
		transform: translateY(0);
	}

	button {
		display: flex;
		gap: 0.8rem;
		align-items: center;

		width: 100%;
		padding: 0.8rem 1rem;
		border-radius: var(--border-radius);
		text-align: start;

		border: none;
		background: transparent;
		color: var(--text-color);
		cursor: pointer;
	}
	button.selected {
		font-weight: 700;
	}
	button.selected::after {
		margin-inline-start: auto;

		content: '●';
		color: var(--gray-color-500);
	}
	button:hover,
	button:focus-visible {
		background-color: var(--primary-color-400);
		color: var(--white-color);

		outline: none;
	}
	button:active {
		font-weight: 600;
	}
</style>
