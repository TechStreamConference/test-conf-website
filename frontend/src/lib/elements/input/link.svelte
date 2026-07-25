<script lang="ts">
	import { get_rel } from '$lib/helper/link-options';
	import { LinkTarget } from '$lib/helper/link-options';
	import type { Snippet } from 'svelte';
	import type { HTMLAnchorAttributes } from 'svelte/elements';

	interface Props extends HTMLAnchorAttributes {
		children: Snippet;
		href: string;
		aria_label: string;
		target?: LinkTarget;
		external?: boolean;
	}

	const {
		children,
		href,
		aria_label,
		target = LinkTarget.Self,
		external = true,
		...rest
	}: Props = $props();
</script>

<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
<a {href} {target} aria-label={aria_label} rel={external ? get_rel(target) : undefined} {...rest}>
	{@render children()}
</a>

<style>
	a {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--half-gap);

		min-height: 4.4rem;
		padding: var(--full-padding) var(--2x-padding);

		border: none;
		border-radius: var(--border-radius);

		background-color: var(--primary-color-light);
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
		transform: translateY(-0.2rem);
		box-shadow: 0 0.8rem 1.8rem rgba(0, 0, 0, 0.28);

		background-color: var(--primary-color-dark);
		outline: none;
	}

	a:active {
		transform: translateY(0);
		box-shadow: 0 0.2rem 0.6rem rgba(0, 0, 0, 0.18);
	}
</style>
