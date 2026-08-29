<script lang="ts">
	import Headline from '$lib/elements/text/Headline.svelte';
	import Paragraph from '$lib/elements/text/Paragraph.svelte';
	import SubHeadline from '$lib/elements/text/SubHeadline.svelte';
	import Tag from '$lib/elements/text/Tag.svelte';

	import { TagColor } from '$lib/helper/tag';

	interface Props {
		variant: 'headline' | 'subheadline' | 'paragraph' | 'tag';
		text: string;
		render_line: boolean;
		preserve_newlines: boolean;
		tag_color: TagColor;
	}
	let { variant, text, render_line, preserve_newlines, tag_color }: Props = $props();
</script>

{#if variant === 'headline'}
	<Headline {render_line}>{text}</Headline>
{:else if variant === 'subheadline'}
	<SubHeadline>{text}</SubHeadline>
{:else if variant === 'paragraph'}
	<Paragraph {preserve_newlines}>{text}</Paragraph>
{:else}
	<Tag {tag_color}>{text}</Tag>
{/if}
