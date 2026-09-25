<script lang="ts">
	import { onMount } from 'svelte';

	import { decide_regional_settings_change } from '$lib/helper/regional_settings';
	import { init_regional_settings } from '$lib/helper/regional_settings';
	import type { PendingRegionalSettingsChange } from '$lib/helper/regional_settings';

	// Deliberately minimal/unstyled: a functional starting point, not a final design.

	let pending: PendingRegionalSettingsChange | undefined = $state(undefined);

	onMount(async () => {
		pending = await init_regional_settings();
	});

	async function decide(field: 'timezone' | 'locale', value: 'accept' | 'keep'): Promise<void> {
		if (!pending) {
			return;
		}

		await decide_regional_settings_change(pending.change.id, { [field]: value });

		const remaining = { ...pending.change, [field]: null };
		pending =
			remaining.timezone == null && remaining.locale == null
				? undefined
				: { ...pending, change: remaining };
	}
</script>

{#if pending}
	<div class="regional-settings-prompt">
		{#if pending.change.timezone}
			<p>
				This device is now using {pending.change.timezone}. Currently set to {pending.current
					.timezone} for displayed times.
				<button type="button" onclick={() => decide('timezone', 'accept')}
					>Use {pending.change.timezone}</button
				>
				<button type="button" onclick={() => decide('timezone', 'keep')}
					>Keep {pending.current.timezone}</button
				>
			</p>
		{/if}
		{#if pending.change.locale}
			<p>
				This device now formats dates and numbers using {pending.change.locale}. Currently set to {pending
					.current.locale}. (This does not change the website's language.)
				<button type="button" onclick={() => decide('locale', 'accept')}
					>Use {pending.change.locale}</button
				>
				<button type="button" onclick={() => decide('locale', 'keep')}
					>Keep {pending.current.locale}</button
				>
			</p>
		{/if}
	</div>
{/if}

<style>
	.regional-settings-prompt {
		position: fixed;
		inset-block-end: 1rem;
		inset-inline: 1rem;
		z-index: 1000;

		display: flex;
		flex-direction: column;
		gap: 0.5rem;

		padding: 1rem;
		border: 1px solid #888;
		background: #fffbe6;
		color: #111;
	}
</style>
