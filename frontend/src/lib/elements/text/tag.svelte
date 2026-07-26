<script lang="ts">
	import type { TagColor } from '$lib/helper/tag';
	import type { ThemeColor } from '$lib/helper/tag';
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';
	import { get_theme_color } from '$lib/helper/tag';

	interface Props extends HTMLAttributes<HTMLParagraphElement> {
		children: Snippet;
		tag_color: TagColor;
	}

	const { children, tag_color, ...rest }: Props = $props();
	// it is okay, that this is set only once since light dark switch is working via CSS
	// svelte-ignore state_referenced_locally
	const theme_color: ThemeColor = get_theme_color(tag_color);
</script>

<p style:background-color={theme_color.background} style:color={theme_color.text} {...rest}>
	{@render children()}
</p>

<style>
	p {
		font-size: var(--paragraph-font-size);
		display: block;
		padding: 0.25rem;
		border-radius: var(--border-radius);
	}

	@media (min-width: 120rem) {
		p {
			padding: 0.25rem 0.5rem;
		}
	}
</style>
