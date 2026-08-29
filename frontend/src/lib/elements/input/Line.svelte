<script lang="ts" generics="T extends InputType">
	import type { AriaAttributes } from 'svelte/elements';
	import type { HTMLInputAttributes } from 'svelte/elements';
	import type { InputContextProp } from '$lib/helper/input';
	import type { InputValue } from '$lib/helper/input';
	import type { InputType } from '$lib/helper/input';
	import type { DateTimeContext } from '$lib/helper/zoned_date_time';
	import { isDateInputType } from '$lib/helper/input';
	import { isMaxLengthOrange } from '$lib/helper/input';
	import { isMaxLengthRed } from '$lib/helper/input';
	import { MAX_LENGTH_INPUT_TYPE } from '$lib/helper/input';
	import { parseDateInputValue } from '$lib/helper/input';
	import { parseInputValue } from '$lib/helper/input';
	import { formatInputValue } from '$lib/helper/input';
	import { unsignedIntOr } from '$lib/helper/numbers';
	import { isMaxLengthVisible } from '$lib/helper/input';

	type Props = Pick<
		HTMLInputAttributes,
		| 'autocomplete'
		| 'class'
		| 'disabled'
		| 'max'
		| 'min'
		| 'name'
		| 'placeholder'
		| 'readonly'
		| 'required'
		| 'step'
	> &
		AriaAttributes &
		InputContextProp<T> & {
			id: string;
			label: string;
			type: T;
			maxlength?: number | undefined;
			value: InputValue<T>;
		};
	let { id, label, type, maxlength, value = $bindable(), context, ...rest }: Props = $props();

	const validMaxLength: number | undefined = $derived(unsignedIntOr(maxlength, undefined));

	function oninput(event: Event & { currentTarget: HTMLInputElement }) {
		const element = event.currentTarget;
		value = (
			isDateInputType(type)
				? parseDateInputValue(type, element, context as DateTimeContext)
				: parseInputValue(type, element)
		) as InputValue<T>;
	}
</script>

<div>
	<label for={id}>{label}</label>
	<input
		{...rest}
		class:normal-font={true}
		{id}
		{type}
		value={formatInputValue(type, value)}
		oninput={onInput}
		maxlength={validMaxLength}
	/>
	{#if validMaxLength !== undefined && MAX_LENGTH_INPUT_TYPE.has(type) && typeof value === 'string'}
		<p
			class:visible={isMaxLengthVisible(validMaxLength, value)}
			class:normal-font={true}
			class:orange={isMaxLengthOrange(validMaxLength, value)}
			class:red={isMaxLengthRed(validMaxLength, value)}
		>
			{value.length.toString()} / {validMaxLength.toString()}
		</p>
	{/if}
</div>

<!-- eslint-disable svelte/no-unused-svelte-ignore -->
<!-- svelte-ignore css_unused_selector -->
<style>
	/*
	 * Unused textarea selector because it is the same selector as input.
	 * Also ESLint does not get, that the svelte-ignore is actually doing stuff.
	 */
	@import 'static/css/input.css';
</style>
