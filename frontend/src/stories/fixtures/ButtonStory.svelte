<script lang="ts">
    import Button from '$lib/elements/input/Button.svelte';

    interface Props {
        label: string;
        'aria-label': string;
        type: 'button' | 'submit' | 'reset';
        disabled: boolean;
    }
    const { label, 'aria-label': ariaLabel, type, disabled }: Props = $props();

    let clickCount: number = $state(0);
    let submitCount: number = $state(0);
    let resetCount: number = $state(0);

    function handleClick(): void {
        clickCount++;
    }

    function handleSubmit(event: SubmitEvent): void {
        event.preventDefault();
        submitCount++;
    }

    function handleReset(): void {
        resetCount++;
    }
</script>

<form onsubmit={handleSubmit} onreset={handleReset}>
    <Button {type} {disabled} aria-label={ariaLabel} onclick={handleClick}>{label}</Button>
    <p>Clicks: {clickCount}</p>
    <p>Form submits: {submitCount}</p>
    <p>Form resets: {resetCount}</p>
</form>
