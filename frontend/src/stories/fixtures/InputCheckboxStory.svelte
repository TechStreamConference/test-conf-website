<script lang="ts">
	import InputCheckbox from '$lib/elements/input/Checkbox.svelte';

	interface Props {
		count: number;
		layout: 'horizontal' | 'vertical' | 'grid';
		label: string;
	}
	const { count, layout, label }: Props = $props();

	let value: boolean = $state(false);
</script>

<p>{value}</p>
<div
	class:horizontal={layout === 'horizontal'}
	class:vertical={layout === 'vertical'}
	class:grid={layout === 'grid'}
>
	{#each Array(count) as _, i (i)}
		<InputCheckbox id={`checkbox-${i}`} {label} bind:checked={value} />
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
