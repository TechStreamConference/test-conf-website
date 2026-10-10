<script lang="ts">
    import CloseIcon from '@lucide/svelte/icons/x';
    import MenuIcon from '@lucide/svelte/icons/menu';

    import type { Menu } from '$lib/helper/menus';
    import type { UserState } from '$lib/helper/menus';

    import { getEntries } from '$lib/helper/menus';
    import { i18n } from '$lib/helper/translate';
    import Link from '$lib/elements/link/Link.svelte';
    import { LinkTarget } from '$lib/helper/link-options';
    import { LinkVariant } from '$lib/helper/link-options';
    import LogoSmall from '$lib/elements/img/LogoSmall.svelte';
    import ThemeSelect from '$lib/elements/theme/ThemeSelect.svelte';

    import { m } from '$paraglide/messages';

    interface Props {
        languageTag: string;
        menu: Menu;
        userState: UserState;
    }
    const { languageTag, menu, userState }: Props = $props();

    const MENU_ID = 'header-menu';

    let isOpen: boolean = $state(false);
    let toggleButton: HTMLButtonElement | undefined = $state(undefined);

    function handleToggle(): void {
        isOpen = !isOpen;
    }

    function handleKeydown(event: KeyboardEvent): void {
        if (event.key === 'Escape' && isOpen) {
            isOpen = false;
            toggleButton?.focus();
        }
    }

    function closeMenu(): void {
        isOpen = false;
    }
</script>

<svelte:window onkeydown={handleKeydown} />

<header>
    <Link
        href="/"
        aria-label={i18n(m.menu_homepage_aria, languageTag)}
        target={LinkTarget.SameTab}
        variant={LinkVariant.Plain}
    >
        <LogoSmall {languageTag} height="3.2rem" />
    </Link>

    <button
        bind:this={toggleButton}
        type="button"
        aria-controls={MENU_ID}
        aria-expanded={isOpen}
        aria-label={i18n(m.header_menu_aria, languageTag)}
        onclick={handleToggle}
    >
        {#if isOpen}
            <CloseIcon aria-hidden="true" />
        {:else}
            <MenuIcon aria-hidden="true" />
        {/if}
    </button>

    <div id={MENU_ID} class:menu={true} class:open={isOpen}>
        <nav aria-label={i18n(m.header_menu_aria, languageTag)}>
            <ul>
                {#each getEntries(menu, userState) as entry (entry.url)}
                    <li>
                        <Link
                            href={entry.url}
                            aria-label={i18n(entry.ariaLabel, languageTag)}
                            target={LinkTarget.SameTab}
                            variant={LinkVariant.Menu}
                            onclick={closeMenu}
                        >
                            {i18n(entry.label, languageTag)}
                        </Link>
                    </li>
                {/each}
            </ul>
        </nav>

        <div class:controls={true}>
            <ThemeSelect {languageTag} />
        </div>
    </div>
</header>

<style>
    header {
        /* layout */
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 10;

        /* box */
        gap: 1rem;
        padding: 0.5rem 1rem;

        /* appearance */
        background-color: var(--primary-color-600);
        color: var(--white-color);

        /* effects */
        box-shadow: 0 0.2rem 0.6rem rgba(0, 0, 0, 0.25);
    }

    button {
        display: flex;
        align-items: center;
        justify-content: center;

        width: 3rem;
        height: 3rem;
        border: none;
        border-radius: var(--border-radius);

        background-color: transparent;
        color: var(--white-color);
        cursor: pointer;

        font-size: 2rem;

        transition: background-color var(--transition-duration);
    }
    button:hover,
    button:focus-visible {
        background-color: var(--primary-color-400);
    }
    button:focus-visible {
        outline: 0.2rem solid var(--white-color);
        outline-offset: -0.2rem;
    }

    .menu {
        /* layout */
        display: none;
        flex-direction: column;
        position: absolute;
        top: 100%;
        inset-inline: 0;
        overflow-y: auto;

        /* box */
        gap: 0.5rem;
        max-height: calc(100dvh - 100%);
        padding: 0.5rem 0 1rem;

        /* appearance */
        background-color: var(--primary-color-600);

        /* effects: the inset shadow is the one the header casts onto the panel, the outer one is the shadow below the panel. */
        box-shadow:
            inset 0 0.5rem 0.5rem -0.4rem rgba(0, 0, 0, 0.25),
            0 0.4rem 0.6rem rgba(0, 0, 0, 0.25);
    }
    .menu.open {
        display: flex;
    }

    ul {
        display: flex;
        flex-direction: column;

        margin: 0;
        padding: 0;

        list-style: none;
    }

    .controls {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }

    @media (min-width: 48rem) {
        header {
            padding-inline: 1.5rem;
        }

        button {
            display: none;
        }

        .menu {
            display: flex;
            flex-direction: row;
            align-items: center;
            position: static;
            overflow-y: visible;

            gap: 1rem;
            max-height: none;
            padding: 0;

            background-color: transparent;
            box-shadow: none;
        }

        ul {
            flex-direction: row;
        }
    }
</style>
