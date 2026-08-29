<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAnchorAttributes } from 'svelte/elements';

	import { LinkTarget } from '$lib/helper/link-options';
	import { DEFAULT_LINK_TARGET } from '$lib/helper/link-options';
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
		color: var(--line-color);

		text-decoration-color: var(--line-color);
	}
</style>
