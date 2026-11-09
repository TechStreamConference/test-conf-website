<script lang="ts" generics="T">
    import type { Snippet } from 'svelte';

    import type { SwitchItem } from '$lib/elements/switch/switch-item';

    interface Props {
        items: SwitchItem<T>[];
        selected: T | undefined;
        onSelect: (value: T) => void;
        triggerIcon: Snippet;
        'aria-label': string;
    }
    const { items, selected, onSelect, triggerIcon, 'aria-label': ariaLabel }: Props = $props();

    let isOpen: boolean = $state(false);
    let options: HTMLDivElement | undefined = $state(undefined);

    /**
     * @brief Scrolls the open options into view. On small screens they open below the trigger and push the
     * content down, so a scrollable parent does not clip them.
     * @param event the toggle event of the `<details>` element.
     */
    function handleToggle(event: Event): void {
        const details = event.currentTarget;
        if (details instanceof HTMLDetailsElement && details.open) {
            options?.scrollIntoView({ block: 'nearest' });
        }
    }

    /**
     * @brief Selects an item and closes the options.
     * @param value the value of the selected item.
     */
    function select(value: T): void {
        onSelect(value);
        isOpen = false;
    }
</script>

<details bind:open={isOpen} ontoggle={handleToggle}>
    <summary aria-label={ariaLabel}>
        {@render triggerIcon()}
    </summary>

    <div bind:this={options}>
        {#each items as item (item.value)}
            <button
                class:selected={item.value === selected}
                type="button"
                aria-pressed={item.value === selected}
                onclick={() => select(item.value)}>{@render item.icon()} {item.label}</button
            >
        {/each}
    </div>
</details>

<style>
    details {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    summary {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 3rem;
        height: 3rem;

        margin: 0.5rem;
        border-radius: var(--border-radius);
        border: none;

        user-select: none;
        cursor: pointer;
        list-style: none;
        background-color: transparent;
        color: var(--white-color);

        font-size: 2rem;

        transition: background-color var(--transition-duration);
    }
    summary:hover,
    summary:focus-visible {
        background-color: var(--primary-color-400);
        color: var(--white-color);
    }

    /* On small screens the options open below the button and push the content down, so a scrollable parent does not clip them. */
    div {
        display: none;
        flex-direction: column;
        gap: 0.4rem;

        margin-top: 0.4rem;
        padding: 0.6rem;
        border-radius: var(--border-radius);

        background-color: var(--primary-color-400);
    }
    details[open] div {
        display: flex;
    }

    @media (min-width: 48rem) {
        details {
            display: inline-block;
            position: relative;
        }

        div {
            display: flex;
            position: absolute;

            top: calc(100% + 0.8rem);
            inset-inline-end: 0;
            min-width: 15rem;
            margin-top: 0;

            background-color: var(--background-color-500);
            pointer-events: none;

            box-shadow: 0 0.6rem 2rem rgba(0, 0, 0, 0.25);
            opacity: 0;
            transform: translateY(-0.5rem);

            transition:
                opacity var(--transition-duration),
                transform var(--transition-duration);
        }
        details[open] div {
            pointer-events: auto;

            opacity: 1;
            transform: translateY(0);
        }

        /* The popup is a light or dark card, so the options use the normal text color. `details` raises the specificity above the base `button` rules. */
        details button {
            color: var(--text-color);
        }
        details button:hover,
        details button:focus-visible {
            background-color: var(--primary-color-400);
            color: var(--white-color);
        }
    }

    button {
        display: flex;
        gap: 0.8rem;
        align-items: center;

        width: 100%;
        padding: 0.8rem 1rem;
        border-radius: var(--border-radius);
        text-align: start;

        border: none;
        background: transparent;
        color: var(--white-color);
        cursor: pointer;
    }
    button.selected {
        font-weight: 700;
    }
    button.selected::after {
        margin-inline-start: auto;

        content: '●';
        color: var(--gray-color-500);
    }
    button:hover,
    button:focus-visible {
        background-color: var(--primary-color-600);
        color: var(--white-color);

        outline: none;
    }
    button:active {
        font-weight: 600;
    }
</style>
