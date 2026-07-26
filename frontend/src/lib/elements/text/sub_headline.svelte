<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLParagraphElement> {
		children: Snippet;
	}

	const { children, ...rest }: Props = $props();
</script>

<h4 class="sub-headline-font" {...rest}>
	{@render children()}
</h4>

<style>
	h4 {
		font-size: var(--subheadline-font-size);
		align-self: center;
	}
</style>
