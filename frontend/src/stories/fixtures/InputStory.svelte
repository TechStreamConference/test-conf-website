<script lang="ts">
	import InputLine from '$lib/elements/input/input_line.svelte';
	import InputArea from '$lib/elements/input/input_area.svelte';

	interface Props {
		count: number;
		variant: 'line' | 'area' | 'mixed';
		label: string;
	}

	let { count, variant, label }: Props = $props();
</script>

{#each Array(count) as i (i)}
	{#if variant === 'line'}
		<InputLine id="input-line-{i}" {label} />
	{:else if variant === 'area'}
		<InputArea id="input-area-{i}" {label} />
	{:else}
		<InputLine id="input-line-{i}" {label} />
		<InputArea id="input-area-{i}" {label} />
	{/if}
{/each}
