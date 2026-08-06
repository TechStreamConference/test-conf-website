<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';
	import type { PlaceholderBackendTagClass } from '$src/placeholder/tag';
	import { get_tag_color } from '$lib/helper/tag';

	import Tag from '$lib/elements/text/tag.svelte';

	interface Props extends HTMLAttributes<HTMLParagraphElement> {
		tags: PlaceholderBackendTagClass[]; // replace that with the actural backend type later
	}

	const { tags, ...rest }: Props = $props();
</script>

<div>
	{#each tags as tag (tag.id)}
		<Tag tag_color={get_tag_color(tag.color_id)} {...rest}>{tag.text}</Tag>
	{/each}
</div>

<style>
	div {
		display: flex;
		flex-direction: row;
		gap: 0.2rem;
		align-items: flex-start;
		justify-content: flex-end;
		align-content: flex-start;
		flex-wrap: wrap;
	}
</style>
