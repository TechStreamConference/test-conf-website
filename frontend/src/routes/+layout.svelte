<script lang="ts">
    import { onMount } from 'svelte';

    import { page } from '$app/state';

    import { MAIN_PAGE_FOOTER_MENU } from '$lib/helper/menus';
    import { MAIN_PAGE_HEADER_MENU } from '$lib/helper/menus';
    import { initTheme } from '$lib/helper/light-dark';
    import BasePage from '$lib/elements/layout/BasePage.svelte';
    import RegionalSettingsPrompt from '$lib/elements/regional_settings/regional_settings_prompt.svelte';

    import type { LayoutProps } from './$types';

    let { children, data }: LayoutProps = $props();

    const languageTag = $derived(page.data.languageTag ?? data.languageTag);

    onMount(() => {
        initTheme();
    });

    // The server renders the right `lang`; this keeps it up to date when the client navigates to a page in another language.
    $effect(() => {
        document.documentElement.lang = languageTag;
    });
</script>

<BasePage
    {languageTag}
    userState={data.userState}
    headerMenu={page.data.headerMenu ?? MAIN_PAGE_HEADER_MENU}
    footerMenu={page.data.footerMenu ?? MAIN_PAGE_FOOTER_MENU}
    events={[]}
    footerText={data.footerText}
>
    {@render children()}
</BasePage>
<RegionalSettingsPrompt />
