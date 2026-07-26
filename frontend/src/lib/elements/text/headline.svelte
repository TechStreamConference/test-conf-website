<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLParagraphElement> {
		children: Snippet;
		render_line?: boolean;
	}

	const { children, render_line = false, ...rest }: Props = $props();
</script>

<h2 class="headline-font" class:render-line={render_line} {...rest}>
	{@render children()}
</h2>

<style>
	h2 {
		display: inline-block;
		align-self: center;
		font-size: var(--headline-font-size);
	}

	h2.render-line::after {
		content: '';
		display: block;
		height: var(--headline-after-height);
		width: var(--headline-after-width);
		margin-inline-start: var(--headline-after-margin-start);
		background: var(--secondary-color);
	}
</style>
