<script lang="ts">
    import type { Snippet } from 'svelte';

    import type { Menu } from '$lib/helper/menus';
    import type { UserState } from '$lib/helper/menus';

    import Footer from '$lib/elements/layout/Footer.svelte';
    import Header from '$lib/elements/layout/Header.svelte';

    interface Props {
        children: Snippet;
        languageTag: string;
        userState: UserState;
        headerMenu: Menu;
        footerMenu: Menu;
        events: { label: string; url: string }[];
        footerText: string;
    }
    const { children, languageTag, userState, headerMenu, footerMenu, events, footerText }: Props =
        $props();
</script>

<div>
    <Header {languageTag} {userState} menu={headerMenu} />
    <main>
        {@render children()}
    </main>
    <Footer {languageTag} {userState} menu={footerMenu} {events} {footerText} />
</div>

<style>
    div {
        display: flex;
        flex-direction: column;

        min-height: 100vh;
        min-height: 100dvh;
    }

    main {
        flex: 1;
    }
</style>
