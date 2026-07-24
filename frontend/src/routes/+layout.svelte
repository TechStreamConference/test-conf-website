<script lang="ts">
	import { onMount } from 'svelte';
	import { init_theme } from '$lib/helper/light-dark';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	onMount(() => {
		init_theme();
	});
</script>

{@render children()}
