<script lang="ts">
    import type { HTMLButtonAttributes } from 'svelte/elements';
    import type { Snippet } from 'svelte';

    interface Props extends Omit<HTMLButtonAttributes, 'aria-label' | 'type'> {
        children: Snippet;
        'aria-label': string;
        type?: 'button' | 'submit' | 'reset';
    }
    const { children, 'aria-label': ariaLabel, type = 'button', ...rest }: Props = $props();
</script>

<button {...rest} {type} aria-label={ariaLabel}>
    {@render children()}
</button>

<style>
    button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;

        padding: var(--full-padding) var(--2x-padding);
        min-height: 4.4rem;
        border-radius: var(--border-radius);
        border: none;

        background-color: var(--primary-color-400);
        color: var(--white-color);
        font: inherit;
        text-decoration: none;
        cursor: pointer;

        box-shadow: 0 0.4rem 1rem rgba(0, 0, 0, 0.2);

        transition:
            transform var(--transition-duration),
            box-shadow var(--transition-duration),
            background-color var(--transition-duration);
    }
    button:hover,
    button:focus-visible {
        background-color: var(--primary-color-600);

        box-shadow: 0 0.8rem 1.8rem rgba(0, 0, 0, 0.28);
        outline: none;
        transform: translateY(-0.2rem);
    }
    button:active {
        transform: translateY(0);
        box-shadow: 0 0.2rem 0.6rem rgba(0, 0, 0, 0.18);
    }
    button:disabled {
        background-color: var(--primary-color-400);

        box-shadow: none;
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
    }
</style>
