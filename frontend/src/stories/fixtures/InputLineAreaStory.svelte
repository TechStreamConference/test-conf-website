<script lang="ts">
	import InputLine from '$lib/elements/input/input_line.svelte';
	import InputArea from '$lib/elements/input/input_area.svelte';
	import { InputType } from '$lib/helper/input';

	interface Props {
		count: number;
		variant: 'line' | 'area' | 'mixed';
		layout: 'horizontal' | 'vertical' | 'grid';
		label: string;
		type: InputType;
		maxlength?: number | undefined;
	}

	let { count, variant, layout, maxlength, label, type }: Props = $props();
	// use `any` here so that I can write every value here to just display it.
	// the actual type is displayed within the UI.
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let value: any = $state('');

	function getTypeName(value: unknown): string {
		if (value === null) return 'null';
		if (value === undefined) return 'undefined';

		return value.constructor.name;
	}
</script>

<p>{getTypeName(value)}</p>
<p>{value}</p>
{#if value instanceof Date && !Number.isNaN(value.getTime())}
	<p>UTC: {value.toISOString()}</p>
{/if}
<div
	class:horizontal={layout === 'horizontal'}
	class:vertical={layout === 'vertical'}
	class:grid={layout === 'grid'}
>
	{#each Array(count) as _, i (i)}
		{#if variant === 'line'}
			<InputLine id={`input-line-${i}`} {label} {type} bind:value {maxlength} />
		{:else if variant === 'area'}
			<InputArea id={`input-area-${i}`} {label} bind:value {maxlength} />
		{:else}
			<InputLine id={`input-line-${i}`} {label} {type} bind:value {maxlength} />
			<InputArea id={`input-area-${i}`} {label} bind:value {maxlength} />
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
