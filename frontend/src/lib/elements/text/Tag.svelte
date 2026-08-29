<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';

	import type { TagColor } from '$lib/helper/tag';
	import type { ThemeColor } from '$lib/helper/tag';
	import { getThemeColor } from '$lib/helper/tag';

	interface Props extends HTMLAttributes<HTMLParagraphElement> {
		children: Snippet;
		tag_color: TagColor;
	}
	const { children, tag_color, ...rest }: Props = $props();

	const themeColor: ThemeColor = $derived(getThemeColor(tag_color));
</script>

<p
	{...rest}
	class:normal-font={true}
	style:background-color={themeColor.background}
	style:color={themeColor.text}
>
	{@render children()}
</p>

<style>
	p {
		display: block;

		padding: 0.25rem;
		border-radius: var(--border-radius);

		font-size: var(--paragraph-font-size);
	}

	@media (min-width: 120rem) {
		p {
			padding: 0.25rem 0.5rem;
		}
	}
</style>
