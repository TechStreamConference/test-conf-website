<script lang="ts">
    import { onMount } from 'svelte';
    import Hourglass from '@lucide/svelte/icons/hourglass';
    import Moon from '@lucide/svelte/icons/moon';
    import Sun from '@lucide/svelte/icons/sun';
    import SunMoon from '@lucide/svelte/icons/sun-moon';

    import { getTheme } from '$lib/helper/light-dark';
    import { i18n } from '$lib/helper/translate';
    import { setTheme } from '$lib/helper/light-dark';
    import { Theme } from '$lib/helper/light-dark';

    import { m } from '$paraglide/messages';

    interface Props {
        languageTag: string;
    }
    const { languageTag }: Props = $props();

    onMount(() => {
        currentTheme = getTheme();
    });

    let currentTheme: Theme | undefined = $state(undefined);
    let isOpen: boolean = $state(false);
    let options: HTMLDivElement | undefined = $state(undefined);

    function handleToggle(event: Event): void {
        const details = event.currentTarget;
        if (details instanceof HTMLDetailsElement && details.open) {
            options?.scrollIntoView({ block: 'nearest' });
        }
    }

    function selectTheme(theme: Theme): void {
        setTheme(theme);
        isOpen = false;
        currentTheme = theme;
    }
</script>

<details bind:open={isOpen} ontoggle={handleToggle}>
    <summary aria-label={i18n(m.global_themeSelect_aria, languageTag)}>
        {#if currentTheme === Theme.Dark}
            <Moon aria-hidden="true" />
        {:else if currentTheme === Theme.Light}
            <Sun aria-hidden="true" />
        {:else if currentTheme === Theme.System}
            <SunMoon aria-hidden="true" />
        {:else}
            <Hourglass aria-hidden="true" />
        {/if}
    </summary>

    <div bind:this={options}>
        <button
            class:selected={currentTheme === Theme.System}
            type="button"
            aria-pressed={currentTheme === Theme.System}
            onclick={() => selectTheme(Theme.System)}
            ><SunMoon aria-hidden="true" /> {i18n(m.global_themeSelectSystem, languageTag)}</button
        >
        <button
            class:selected={currentTheme === Theme.Light}
            type="button"
            aria-pressed={currentTheme === Theme.Light}
            onclick={() => selectTheme(Theme.Light)}
            ><Sun aria-hidden="true" /> {i18n(m.global_themeSelectLight, languageTag)}</button
        >
        <button
            class:selected={currentTheme === Theme.Dark}
            type="button"
            aria-pressed={currentTheme === Theme.Dark}
            onclick={() => selectTheme(Theme.Dark)}
            ><Moon aria-hidden="true" /> {i18n(m.global_themeSelectDark, languageTag)}</button
        >
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
