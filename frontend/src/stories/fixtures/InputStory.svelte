<script lang="ts">
	import InputLine from '$lib/elements/input/input_line.svelte';
	import InputArea from '$lib/elements/input/input_area.svelte';

	interface Props {
		variant: 'line' | 'area';
		label: string;
	}

	let { variant, label }: Props = $props();
</script>

{#if variant === 'line'}
	<InputLine id="input-line" {label} />
{:else}
	<InputArea id="input-area" />
{/if}
