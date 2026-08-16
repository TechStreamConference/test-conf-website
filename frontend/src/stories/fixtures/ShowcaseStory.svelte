<script lang="ts">
	import Headline from '$lib/elements/text/headline.svelte';
	import SubHeadline from '$lib/elements/text/sub_headline.svelte';
	import Paragraph from '$lib/elements/text/paragraph.svelte';
	import TagWrapper from '$lib/elements/text/tag_wrapper.svelte';
	import InlineLink from '$lib/elements/link/inline_link.svelte';
	import LogoSmall from '$lib/elements/img/logo_small.svelte';
</script>

<article>
	<LogoSmall width="4rem" />
	<Headline render_line>Tech Stream Conference 2026</Headline>
	<SubHeadline>Building reliable software together</SubHeadline>
	<Paragraph>
		A two-day conference for engineers who care about testing, quality, and sustainable software
		development. Expect talks, workshops, and plenty of hallway conversations.
	</Paragraph>
	<TagWrapper
		tags={[
			{ id: 1, color_id: 1, text: 'Testing' },
			{ id: 2, color_id: 2, text: 'Frontend' },
			{ id: 3, color_id: 1, text: 'Svelte' },
			{ id: 4, color_id: 2, text: 'Quality' }
		]}
	/>
	<p>
		<InlineLink
			href="https://tech-stream.org"
			aria_label="Visit the Tech Stream Conference website"
		>
			Visit conference website
		</InlineLink>
	</p>
</article>

<style>
	article {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		max-width: 40rem;
	}
</style>
