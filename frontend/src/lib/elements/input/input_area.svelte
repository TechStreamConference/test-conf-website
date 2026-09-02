<script lang="ts">
	import type { AriaAttributes } from 'svelte/elements';
	import type { HTMLTextareaAttributes } from 'svelte/elements';
	import { validate_unsigned_int } from '$lib/helper/numbers';
	import { calculateOrange } from '$lib/helper/input';
	import { calculateRed } from '$lib/helper/input';
	import { isMaxLengthVisible } from '$lib/helper/input';

	interface Props
		extends
			Pick<
				HTMLTextareaAttributes,
				'autocomplete' | 'class' | 'disabled' | 'name' | 'placeholder' | 'readonly' | 'required'
			>,
			AriaAttributes {
		id: string;
		label: string;
		maxlength?: number | undefined;
		value: string;
	}
	let { id, label, maxlength, value = $bindable(), ...rest }: Props = $props();

	const validMaxLength: number | undefined = $derived(validate_unsigned_int(maxlength));
</script>

<div>
	<label for={id}>{label}</label>
	<textarea {...rest} class:normal-font={true} {id} maxlength={validMaxLength} bind:value
	></textarea>
	{#if validMaxLength !== undefined}
		<p
			class:visible={isMaxLengthVisible(validMaxLength, value)}
			class:normal-font={true}
			class:orange={calculateOrange(validMaxLength, value)}
			class:red={calculateRed(validMaxLength, value)}
		>
			{value.length.toString()} / {validMaxLength.toString()}
		</p>
	{/if}
</div>

<!-- eslint-disable svelte/no-unused-svelte-ignore -->
<!-- svelte-ignore css_unused_selector -->
<style>
	/*
	 * unused input selector because it is the same selector as textarea.
	 * Also ESLint does not get, that the svelte-ignore is actually doing stuff.
	 */
	@import 'static/css/input.css';
</style>
