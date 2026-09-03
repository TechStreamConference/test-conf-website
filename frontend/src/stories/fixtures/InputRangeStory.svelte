<script lang="ts">
	import InputRange from '$lib/elements/input/input_range.svelte';

	interface Props {
		count: number;
		layout: 'horizontal' | 'vertical' | 'grid';
		label: string;
		min: number;
		max: number;
		step: number;
	}
	const { count, layout, label, min, max, step }: Props = $props();
	let value: number = $state(0);
</script>

<p>{value}</p>
<div
	class:horizontal={layout === 'horizontal'}
	class:vertical={layout === 'vertical'}
	class:grid={layout === 'grid'}
>
	{#each Array(count) as _, i (i)}
		<InputRange id={`range-${i}`} {label} bind:value {min} {max} {step} />
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
