<script lang="ts">
    import type { HTMLImgAttributes } from 'svelte/elements';

    import { i18n } from '$lib/helper/translate';
    import Image from '$lib/elements/img/Image.svelte';

    import { m } from '$paraglide/messages';

    interface Props extends Omit<HTMLImgAttributes, 'src' | 'alt'> {
        languageTag: string;
        height?: string | undefined;
        width?: string | undefined;
    }
    const { languageTag, height, width, ...rest }: Props = $props();
</script>

<Image
    {...rest}
    src="/img/logo_small.png"
    alt={i18n(m.global_logoSmall_alt, languageTag)}
    {height}
    {width}
/>
