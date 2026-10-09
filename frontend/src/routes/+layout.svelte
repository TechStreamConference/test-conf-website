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

    onMount(() => {
        initTheme();
    });
</script>

<BasePage
    languageTag={data.languageTag}
    userState={data.userState}
    headerMenu={page.data.headerMenu ?? MAIN_PAGE_HEADER_MENU}
    footerMenu={page.data.footerMenu ?? MAIN_PAGE_FOOTER_MENU}
    events={[]}
    footerText={data.footerText}
>
    {@render children()}
</BasePage>
<RegionalSettingsPrompt />
