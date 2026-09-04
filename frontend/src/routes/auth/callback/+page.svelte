<script lang="ts">
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<h1>Login failed</h1>
<p>{data.error.detail}</p>
