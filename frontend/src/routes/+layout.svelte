<script lang="ts">
    import { onMount } from 'svelte';

    import { initTheme } from '$lib/helper/light-dark';
    import RegionalSettingsPrompt from '$lib/elements/regional_settings/regional_settings_prompt.svelte';

    import type { LayoutProps } from './$types';

    let { children }: LayoutProps = $props();

    onMount(() => {
        initTheme();
    });
</script>

{@render children()}
<RegionalSettingsPrompt />
