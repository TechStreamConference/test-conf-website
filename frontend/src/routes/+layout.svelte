<script lang="ts">
	import { onMount } from 'svelte';
	import { initTheme } from '$lib/helper/light-dark';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	onMount(() => {
		initTheme();
	});
</script>

{@render children()}
