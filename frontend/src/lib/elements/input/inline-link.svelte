<script lang="ts">
	import type { Snippet } from 'svelte';
	import { LinkTarget } from '$lib/helper/link-options';
	import { get_rel } from '$lib/helper/link-options';
	import type { HTMLAnchorAttributes } from 'svelte/elements';

	interface Props extends HTMLAnchorAttributes {
		children: Snippet;
		href: string;
		aria_label: string;
		target?: LinkTarget;
	}

	const { children, href, aria_label, target = LinkTarget.NewTab, ...rest }: Props = $props();
</script>

<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
<a {href} {target} aria-label={aria_label} rel={get_rel(target)} {...rest}>
	{@render children()}
</a>

<style>
	a {
		color: var(--text-color);
		text-decoration: underline;
		text-decoration-thickness: 0.2rem;
		text-underline-offset: 0.2rem;
		text-decoration-color: var(--text-color);

		transition:
			color var(--transition-duration),
			text-decoration-color var(--transition-duration);
	}

	a:hover,
	a:focus-visible {
		color: var(--primary-color-light);
		text-decoration-color: var(--primary-color-light);
	}
</style>
