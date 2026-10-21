<script lang="ts">
    import type { Menu } from '$lib/helper/menus';
    import type { UserState } from '$lib/helper/menus';

    import { getEntries } from '$lib/helper/menus';
    import { i18n } from '$lib/helper/translate';
    import Link from '$lib/elements/link/Link.svelte';
    import { LinkTarget } from '$lib/helper/link-options';
    import { LinkVariant } from '$lib/helper/link-options';
    import LogoBig from '$lib/elements/img/LogoBig.svelte';

    import { m } from '$paraglide/messages';

    interface Props {
        languageTag: string;
        menu: Menu;
        userState: UserState;
        events: { label: string; url: string }[];
        footerText: string;
    }
    const { languageTag, menu, userState, events, footerText }: Props = $props();

    const MENU_HEADLINE_ID = 'footer-menu-headline';
    const EVENTS_HEADLINE_ID = 'footer-events-headline';

    const currentYear = new Date().getFullYear();
</script>

<footer>
    <div class:columns={true}>
        <nav aria-labelledby={MENU_HEADLINE_ID}>
            <h2 id={MENU_HEADLINE_ID}>{i18n(m.footer_menuHeadline, languageTag)}</h2>
            <ul>
                {#each getEntries(menu, userState) as entry (entry.url)}
                    <li>
                        <Link
                            href={entry.url}
                            aria-label={i18n(entry.ariaLabel, languageTag)}
                            target={LinkTarget.SameTab}
                            variant={LinkVariant.Footer}
                        >
                            {i18n(entry.label, languageTag)}
                        </Link>
                    </li>
                {/each}
            </ul>
        </nav>

        <nav aria-labelledby={EVENTS_HEADLINE_ID}>
            <h2 id={EVENTS_HEADLINE_ID}>{i18n(m.footer_eventsHeadline, languageTag)}</h2>
            <ul class:events={true}>
                {#each events as event (event.url)}
                    <li>
                        <Link
                            href={event.url}
                            aria-label={event.label}
                            target={LinkTarget.SameTab}
                            variant={LinkVariant.Footer}
                        >
                            {event.label}
                        </Link>
                    </li>
                {/each}
            </ul>
        </nav>

        <p>{footerText}</p>

        <div class:logo={true}>
            <Link
                href="/"
                aria-label={i18n(m.menu_homepage_aria, languageTag)}
                target={LinkTarget.SameTab}
                variant={LinkVariant.Plain}
            >
                <LogoBig {languageTag} width="16rem" />
            </Link>
        </div>
    </div>

    <small>{i18n(m.footer_copyright, languageTag, { year: currentYear })}</small>
</footer>

<style>
    footer {
        /* layout */
        display: flex;
        flex-direction: column;
        align-items: center;

        /* box */
        gap: 2rem;
        padding: 2rem 1rem;

        /* appearance */
        background-color: var(--primary-color-600);
        color: var(--white-color);

        /* effects */
        box-shadow: 0 -0.2rem 0.6rem rgba(0, 0, 0, 0.25);
    }

    .columns {
        display: grid;
        grid-template-columns: 1fr;

        gap: 2rem;
        width: 100%;
    }

    h2 {
        margin-bottom: 0.5rem;

        font-size: 1.25rem;
        font-weight: 700;
        text-align: center;
    }

    ul {
        display: flex;
        flex-direction: column;

        margin: 0;
        padding: 0;

        list-style: none;
    }

    .events {
        flex-flow: row wrap;
        justify-content: center;
    }

    p {
        text-align: center;
    }

    .logo {
        display: flex;
        justify-content: center;
    }

    small {
        font-size: 0.875rem;
        text-align: center;
    }

    @media (min-width: 48rem) {
        footer {
            padding-inline: 1.5rem;
        }

        .columns {
            grid-template-columns: repeat(2, 1fr);
        }

        nav,
        p,
        .logo {
            padding: 1.5rem;
        }

        /* Links only need as much width as their text on larger screens, so the hover is small. */
        li {
            display: flex;
            justify-content: center;
        }

        p,
        .logo {
            align-items: center;
        }

        p {
            display: flex;
            justify-content: center;
        }
    }

    @media (min-width: 80rem) {
        footer {
            gap: 0;
        }

        .columns {
            grid-template-columns: repeat(4, 1fr);
        }

        p {
            align-items: flex-start;
        }

        .logo {
            justify-content: flex-end;
        }
    }
</style>
