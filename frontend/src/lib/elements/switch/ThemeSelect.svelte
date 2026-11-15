<script lang="ts">
    import { onMount } from 'svelte';
    import Hourglass from '@lucide/svelte/icons/hourglass';
    import Moon from '@lucide/svelte/icons/moon';
    import Sun from '@lucide/svelte/icons/sun';
    import SunMoon from '@lucide/svelte/icons/sun-moon';

    import type { SwitchItem } from '$lib/elements/switch/switch-item';
    import { getTheme } from '$lib/helper/light-dark';
    import { i18n } from '$lib/helper/translate';
    import { setTheme } from '$lib/helper/light-dark';
    import Switch from '$lib/elements/switch/Switch.svelte';
    import { Theme } from '$lib/helper/light-dark';

    import { m } from '$paraglide/messages';

    interface Props {
        languageTag: string;
    }
    const { languageTag }: Props = $props();

    const SUMMARY_ICON_SIZE = 35;

    onMount(() => {
        currentTheme = getTheme();
    });

    let currentTheme: Theme | undefined = $state(undefined);

    const items: SwitchItem<Theme>[] = $derived([
        {
            value: Theme.System,
            label: i18n(m.global_themeSelectSystem, languageTag),
            icon: itemIcon
        },
        {
            value: Theme.Light,
            label: i18n(m.global_themeSelectLight, languageTag),
            icon: itemIcon
        },
        {
            value: Theme.Dark,
            label: i18n(m.global_themeSelectDark, languageTag),
            icon: itemIcon
        }
    ]);

    /**
     * @brief Sets the theme and keeps the local selection in sync with it.
     * @param theme the newly selected theme.
     */
    function selectTheme(theme: Theme): void {
        setTheme(theme);
        currentTheme = theme;
    }
</script>

{#snippet itemIcon(theme: Theme)}
    {#if theme === Theme.Light}
        <Sun aria-hidden="true" />
    {:else if theme === Theme.Dark}
        <Moon aria-hidden="true" />
    {:else}
        <SunMoon aria-hidden="true" />
    {/if}
{/snippet}
{#snippet triggerIcon()}
    {#if currentTheme === Theme.Dark}
        <Moon size={SUMMARY_ICON_SIZE} aria-hidden="true" />
    {:else if currentTheme === Theme.Light}
        <Sun size={SUMMARY_ICON_SIZE} aria-hidden="true" />
    {:else if currentTheme === Theme.System}
        <SunMoon size={SUMMARY_ICON_SIZE} aria-hidden="true" />
    {:else}
        <Hourglass size={SUMMARY_ICON_SIZE} aria-hidden="true" />
    {/if}
{/snippet}

<Switch
    {items}
    selected={currentTheme}
    onSelect={selectTheme}
    {triggerIcon}
    aria-label={i18n(m.global_themeSelect_aria, languageTag)}
/>
