<script lang="ts">
	import InputLine from '$lib/elements/input/input_line.svelte';
	import InputArea from '$lib/elements/input/input_area.svelte';

	interface Props {
		count: number;
		variant: 'line' | 'area' | 'mixed';
		layout: 'horizontal' | 'vertical' | 'grid';
		label: string;
	}

	let { count, variant, layout, label }: Props = $props();
</script>

<div
	class:horizontal={layout === 'horizontal'}
	class:vertical={layout === 'vertical'}
	class:grid={layout === 'grid'}
>
	{#each Array(count) as _, i (i)}
		{#if variant === 'line'}
			<InputLine id={`input-line-${i}`} {label} />
		{:else if variant === 'area'}
			<InputArea id={`input-area-${i}`} {label} />
		{:else}
			<InputLine id={`input-line-${i}`} {label} />
			<InputArea id={`input-area-${i}`} {label} />
		{/if}
	{/each}
</div>

<style>
	.horizontal {
		display: flex;
		flex-direction: row;
		gap: 1rem;
	}

	.vertical {
		display: flex;
		flex-direction: column;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		column-gap: 1rem;
	}
</style>
