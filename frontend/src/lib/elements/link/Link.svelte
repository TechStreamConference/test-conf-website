<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAnchorAttributes } from 'svelte/elements';

	import { DEFAULT_LINK_TARGET } from '$lib/helper/link-options';
	import { LinkTarget } from '$lib/helper/link-options';
	import { getRel } from '$lib/helper/link-options';

	interface Props extends Omit<HTMLAnchorAttributes, 'href' | 'aria-label' | 'target'> {
		children: Snippet;
		href: string;
		aria_label: string;
		target?: LinkTarget;
	}
	const {
		children,
		href,
		aria_label,
		target = DEFAULT_LINK_TARGET,
		rel: rel_name,
		...rest
	}: Props = $props();
</script>

<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
<a {...rest} {href} {target} aria-label={aria_label} rel={getRel(target, rel_name)}>
	{@render children()}
</a>

<style>
	a {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;

		padding: var(--full-padding) var(--2x-padding);
		min-height: 4.4rem;
		border-radius: var(--border-radius);
		border: none;

		background-color: var(--primary-color-400);
		color: var(--white-color);
		text-decoration: none;
		cursor: pointer;

		box-shadow: 0 0.4rem 1rem rgba(0, 0, 0, 0.2);

		transition:
			transform var(--transition-duration),
			box-shadow var(--transition-duration),
			background-color var(--transition-duration);
	}
	a:hover,
	a:focus-visible {
		background-color: var(--primary-color-600);

		box-shadow: 0 0.8rem 1.8rem rgba(0, 0, 0, 0.28);
		outline: none;
		transform: translateY(-0.2rem);
	}
	a:active {
		transform: translateY(0);
		box-shadow: 0 0.2rem 0.6rem rgba(0, 0, 0, 0.18);
	}
</style>
