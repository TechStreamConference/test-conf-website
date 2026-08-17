<script lang="ts">
	import type { HTMLAreaAttributes } from 'svelte/elements';

	// eslint-disable-next-line @typescript-eslint/no-empty-object-type
	interface Props extends HTMLAreaAttributes {}
	const { ...rest }: Props = $props();
</script>

<textarea {...rest}></textarea>

<style>
</style>
