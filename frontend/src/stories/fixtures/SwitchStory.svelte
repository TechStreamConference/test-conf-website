<script lang="ts">
    import Flag from '@lucide/svelte/icons/flag';
    import Heart from '@lucide/svelte/icons/heart';
    import Star from '@lucide/svelte/icons/star';

    import type { SwitchItem } from '$lib/elements/switch/switch-item';
    import Switch from '$lib/elements/switch/Switch.svelte';

    type Choice = 'flag' | 'heart' | 'star';

    interface Props {
        selected: Choice;
    }
    const { selected: initialSelected }: Props = $props();

    let selected: Choice = $derived(initialSelected);

    const items: SwitchItem<Choice>[] = [
        { value: 'star', label: 'Star', icon: itemIcon },
        { value: 'heart', label: 'Heart', icon: itemIcon },
        { value: 'flag', label: 'Flag', icon: itemIcon }
    ];

    const TRIGGER_ICON_SIZE = 35;
</script>

{#snippet itemIcon(choice: Choice)}
    {#if choice === 'heart'}
        <Heart aria-hidden="true" />
    {:else if choice === 'flag'}
        <Flag aria-hidden="true" />
    {:else}
        <Star aria-hidden="true" />
    {/if}
{/snippet}
{#snippet triggerIcon()}
    {#if selected === 'heart'}
        <Heart size={TRIGGER_ICON_SIZE} aria-hidden="true" />
    {:else if selected === 'flag'}
        <Flag size={TRIGGER_ICON_SIZE} aria-hidden="true" />
    {:else}
        <Star size={TRIGGER_ICON_SIZE} aria-hidden="true" />
    {/if}
{/snippet}

<div>
    <Switch
        {items}
        {selected}
        onSelect={(value: Choice) => (selected = value)}
        {triggerIcon}
        aria-label="Choice selector"
    />
</div>

<style>
    div {
        display: flex;
        align-items: center;
        justify-content: center;

        min-height: 100vh;

        background-color: var(--primary-color-600);
    }
</style>
